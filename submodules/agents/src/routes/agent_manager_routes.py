import logging
import asyncio
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from stores.agent_manager import agent_manager_instance
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/available")
async def get_available_agents() -> JSONResponse:
    """Get the list of currently available agents"""
    return JSONResponse(
        content={
            "selected_agents": agent_manager_instance.get_selected_agents(),
            "available_agents": agent_manager_instance.get_available_agents(),
        }
    )


@router.post("/selected")
async def set_selected_agents(request: Request) -> JSONResponse:
    """Set which agents should be selected"""
    data = await request.json()
    agent_names = data.get("agents", [])

    agent_manager_instance.set_selected_agents(agent_names)
    logger.info(f"Newly selected agents: {agent_manager_instance.get_selected_agents()}")

    return JSONResponse(content={"status": "success", "agents": agent_names})


@router.get("/commands")
async def get_agent_commands() -> JSONResponse:
    """Get the list of available agent commands"""
    available_agents = agent_manager_instance.get_available_agents()
    commands = [
        {
            "command": agent["command"],
            "description": agent["description"],
            "name": agent["human_readable_name"],
        }
        for agent in available_agents
    ]
    return JSONResponse(content={"commands": commands})


class CreateAgentRequest(BaseModel):
    """Request model for creating a new agent"""

    human_readable_name: str
    description: str
    mcp_server_url: str
    command: Optional[str] = None
    delegator_description: Optional[str] = None
    upload_required: bool = False
    is_enabled: bool = True


@router.post("/create")
async def create_agent(agent_data: CreateAgentRequest) -> JSONResponse:
    """Create a new MCP agent"""
    try:
        # If command is provided, validate that it's unique
        if agent_data.command:
            commands = [agent["command"] for agent in agent_manager_instance.get_available_agents()]
            if agent_data.command in commands:
                raise HTTPException(status_code=400, detail=f"Command '{agent_data.command}' already exists")

        # Create the agent
        agent_config = await agent_manager_instance.create_mcp_agent(agent_data.model_dump())

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Agent '{agent_data.human_readable_name}' created successfully",
                "agent": {
                    "name": agent_config["name"],
                    "human_readable_name": agent_config["human_readable_name"],
                    "command": agent_config["command"],
                    "description": agent_config["description"],
                    "tools": [tool["name"] for tool in agent_config.get("tools", [])],
                },
            },
            status_code=201,
        )
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")


@router.get("/reset")
async def reset_agent_manager() -> JSONResponse:
    """Reset the agent manager to its initial state"""
    agent_manager_instance.reset()

    return JSONResponse(content={"status": "success", "message": "Agent manager reset to initial state"})


@router.post("/verify-url")
async def verify_mcp_url(request: Request) -> JSONResponse:
    """Verify an MCP Server URL by attempting to connect and retrieve tools"""
    try:
        data = await request.json()
        url = data.get("url")

        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        if not url.startswith("http"):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

        # Create a temporary name for the agent
        agent_name = "test_agent_" + str(hash(url))[:8]

        # Test connection and get tools from the MCP server
        test_client = MultiServerMCPClient(
            {
                agent_name: {
                    "url": url,
                    "transport": "sse",
                }
            }
        )

        try:
            # Set a timeout of 5 seconds for the connection attempt
            async with asyncio.timeout(5):
                async with test_client as client:
                    # Get the tools from the MCP server
                    tools = client.get_tools()

                    # Log the tools for debugging
                    logger.info(f"Retrieved {len(tools)} tools from MCP server")

                    # Extract tool schemas properly from StructuredTools
                    tool_schemas = []
                    for tool in tools:
                        try:
                            logger.info(f"Tool: {tool.name}, Description: {tool.description}")

                            # Extract schema based on tool type
                            schema_dict = None

                            # For StructuredTool with Pydantic schema
                            if hasattr(tool, "args_schema") and tool.args_schema is not None:
                                if hasattr(tool.args_schema, "model_json_schema"):
                                    schema_dict = tool.args_schema.model_json_schema()

                            # Add the tool schema with available information
                            if schema_dict:
                                tool_schemas.append(
                                    {
                                        "name": tool.name,
                                        "description": tool.description,
                                        "properties": schema_dict.get("properties", {}),
                                        "required": schema_dict.get("required", []),
                                    }
                                )
                            else:
                                # Fallback if we can't get schema directly
                                tool_schemas.append({"name": tool.name, "description": tool.description})

                        except Exception as e:
                            logger.warning(f"Error processing tool {getattr(tool, 'name', 'unknown')}: {str(e)}")
                            # Ensure we at least capture the name and description
                            tool_schemas.append(
                                {
                                    "name": getattr(tool, "name", "unknown"),
                                    "description": getattr(tool, "description", ""),
                                }
                            )

                    logger.info(f"Successfully verified MCP URL: {url}, found {len(tools)} tools")

                    return JSONResponse(
                        content={
                            "status": "success",
                            "message": f"Successfully connected to MCP server",
                            "tools": tool_schemas,
                        }
                    )

        except asyncio.TimeoutError:
            logger.warning(f"MCP URL verification timed out after 5 seconds: {url}")
            raise HTTPException(
                status_code=400,
                detail="Connection to MCP server timed out after 5 seconds. This likely indicates a misconfiguration. Please check your MCP server logs for errors.",
            )
        except Exception as e:
            error_message = str(e)
            suggestion = ""

            # Provide helpful suggestions based on common error patterns
            if "Connection refused" in error_message:
                suggestion = "Make sure the server is running and accessible."
            elif "404" in error_message:
                suggestion = "The endpoint was not found. Try adding '/sse' to the URL if it's missing."
            elif "502" in error_message or "Bad Gateway" in error_message:
                suggestion = (
                    "Received a Bad Gateway error. The server might be temporarily unavailable or misconfigured."
                )
            elif "Timeout" in error_message or "timed out" in error_message:
                suggestion = "Connection timed out. Check if the server is responding to tool requests."
            elif "SSE" in error_message or "EventSource" in error_message:
                suggestion = "This URL doesn't support Server-Sent Events (SSE). Ensure the endpoint supports SSE."
            elif "TaskGroup" in error_message and "sub-exception" in error_message:
                # Handle the specific error from the logs
                suggestion = (
                    "The server returned an error. This might be due to server unavailability or misconfiguration."
                )
                error_message = "Failed to establish connection with the MCP server"

            detailed_message = f"Failed to connect to MCP server: {error_message}"
            if suggestion:
                detailed_message += f" {suggestion}"

            logger.warning(f"MCP URL verification failed: {url}. Error: {error_message}")

            raise HTTPException(status_code=400, detail=detailed_message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying MCP URL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error verifying MCP URL: {str(e)}")

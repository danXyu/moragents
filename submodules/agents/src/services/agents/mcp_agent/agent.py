import logging
from typing import Any, Dict, Optional

from langchain.schema import SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from models.service.agent_core import AgentCore
from models.service.chat_models import AgentResponse, ChatRequest

logger = logging.getLogger(__name__)


class MCPAgent(AgentCore):
    """Agent for interacting with MCP-based tools."""

    def __init__(self, config: Dict[str, Any], llm: Any):
        super().__init__(config, llm)
        self.agent_name = config.get("name", "mcp_agent")
        self.mcp_url = config.get("mcp_server_url")
        self.tools_provided = config.get("tools", [])
        self.description = config.get("description", "You are a specialized agent that works with external tools.")
        self.system_message = SystemMessage(content=self.description)

        # Create MCP client config without initializing it yet
        self.mcp_config = {
            self.agent_name: {
                "url": self.mcp_url,
                "transport": "sse",
            }
        }

        self.mcp_client = None
        self.tool_bound_llm = None

        self.logger.info(f"Created MCPAgent for {self.agent_name} with URL {self.mcp_url}")

    async def chat(self, request: ChatRequest) -> AgentResponse:
        """Override the chat method to initialize the MCP client before processing."""
        try:
            # Always clean up previous client if it exists
            if self.mcp_client:
                try:
                    await self.mcp_client.__aexit__(None, None, None)
                except Exception as e:
                    self.logger.warning(f"Error cleaning up previous MCP client: {str(e)}")

            # Always create and initialize a new MCP client
            self.mcp_client = MultiServerMCPClient(self.mcp_config)
            await self.mcp_client.__aenter__()

            # Get tools from the MCP server
            tools = self.mcp_client.get_tools()
            self.tools_provided = tools

            # Bind tools to the LLM if available
            if self.llm:
                self.tool_bound_llm = self.llm.bind_tools(tools)
                self.logger.info(f"Bound {len(tools)} tools to LLM for {self.agent_name}")
            else:
                return AgentResponse.error(error_message="LLM is not available for tool binding")

            self.logger.info(f"Successfully initialized MCP agent {self.agent_name}")

            # Now proceed with the normal chat flow
            return await super().chat(request)

        except Exception as e:
            self.logger.error(f"Failed to initialize MCP agent: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=f"Failed to initialize MCP agent: {str(e)}")

    async def _validate_request(self, request: ChatRequest) -> Optional[AgentResponse]:
        """Validate the request before processing."""
        # First call parent validation
        parent_validation = await super()._validate_request(request)
        if parent_validation:
            return parent_validation

        # No need to check initialization since we always initialize in chat()
        return None

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request using MCP tools."""
        try:
            # Build messages for the LLM
            messages = [self.system_message, *request.messages_for_llm]

            # Invoke the LLM with bound tools
            result = self.tool_bound_llm.invoke(messages)

            # Handle the response
            return await self._handle_llm_response(result)

        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=f"An error occurred: {str(e)}")

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute the appropriate MCP tool based on function name."""
        try:
            # Find the matching tool
            tool = next((t for t in self.tools_provided if t.name == func_name), None)

            if not tool:
                self.logger.warning(f"Unknown tool requested: {func_name}")
                return AgentResponse.error(error_message=f"Unknown tool: {func_name}")

            # Execute the tool
            self.logger.info(f"Executing tool {func_name} with args {args}")
            tool_result = await tool.ainvoke(args)
            self.logger.info(f"Tool execution result: {tool_result}")

            # Clean non-serializable objects from args before adding to metadata
            clean_args = {}
            for key, value in args.items():
                # Skip the run_manager and any other non-serializable objects
                if key != "run_manager" and not isinstance(value, (type, object)):
                    try:
                        # Quick test if it's serializable
                        import json

                        json.dumps(value)
                        clean_args[key] = value
                    except (TypeError, OverflowError):
                        # If not serializable, convert to string
                        clean_args[key] = str(value)

            # Return the result with cleaned metadata
            return AgentResponse.success(
                content=str(tool_result),
                metadata={"tool": func_name, "args": clean_args},
                action_type=func_name,
            )
        except Exception as e:
            self.logger.error(f"Error executing tool {func_name}: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=f"Error executing tool {func_name}: {str(e)}")

    async def cleanup(self):
        """Clean up resources when the agent is no longer needed."""
        if self.mcp_client:
            try:
                await self.mcp_client.__aexit__(None, None, None)
                self.mcp_client = None
                self.logger.info(f"Successfully cleaned up MCP client for {self.agent_name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up MCP client: {str(e)}", exc_info=True)

import json
import logging
from typing import List, Optional, Tuple

from config import TOGETHER_CLIENT
from models.service.chat_models import AgentResponse, ChatRequest, ResponseType
from pydantic import BaseModel, Field
from stores.agent_manager import agent_manager_instance

from .system_prompt import get_system_prompt

logger = logging.getLogger(__name__)


class RankAgentsOutput(BaseModel):
    """JSON schema for agent ranking output"""

    agents: List[str] = Field(..., description="List of up to 3 agent names, ordered by relevance")


async def _try_agent(agent_name: str, chat_request: ChatRequest) -> Optional[AgentResponse]:
    """Attempt to use a single agent, with error handling"""
    try:
        logger.info(f"Attempting agent: {agent_name}")
        logger.info(f"Agent manager agents: {agent_manager_instance.agents}")
        logger.info(f"Agent manager config: {agent_manager_instance.config}")
        agent = agent_manager_instance.get_agent(agent_name)
        if not agent:
            logger.error(f"Agent {agent_name} not found")
            return None

        result: AgentResponse = await agent.chat(chat_request)

        if result.response_type == ResponseType.ERROR:
            logger.warning(f"Agent {agent_name} returned error response. You should probably look into this")
            logger.error(f"Error message: {result.error_message}")
            return None

        return result

    except Exception as e:
        logger.error(f"Error using agent {agent_name}: {str(e)}")
        return None


def _get_delegator_response(chat_request: ChatRequest, attempted_agents: set[str], max_retries: int = 3) -> List[str]:
    """Get ranked list of appropriate agents with retry logic"""
    # Get all available agents
    all_available_agents = agent_manager_instance.get_available_agents()
    logger.info(f"All available agents: {all_available_agents}")

    # Filter by selected agents if specified in the request
    available_agents = all_available_agents
    if chat_request.selected_agents:
        # Filter available agents to only include those that were selected
        available_agents = [
            agent for agent in all_available_agents if agent.get("name") in chat_request.selected_agents
        ]
        logger.info(f"Filtered to selected agents: {chat_request.selected_agents}")
        logger.info(f"Available selected agents: {available_agents}")

    if not available_agents:
        if "default" not in attempted_agents:
            return ["default"]
        raise ValueError("No remaining agents available")

    # Build a proper message list for Together API
    messages = [{"role": "system", "content": get_system_prompt(available_agents)}]

    # Add chat history
    for msg in chat_request.chat_history[-5:]:
        messages.append({"role": msg.role, "content": msg.content})

    # Add current prompt
    messages.append({"role": "user", "content": chat_request.prompt.content})

    # Define the tool that will return agent rankings
    tools = [
        {
            "type": "function",
            "function": {
                "name": "rank_agents",
                "description": "Rank the most appropriate agents for this request",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agents": {
                            "type": "array",
                            "description": "List of up to 3 agent names, ordered by relevance",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["agents"],
                },
            },
        }
    ]

    for attempt in range(max_retries):
        try:
            # Use Together's function calling without forcing tool choice
            response = TOGETHER_CLIENT.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                messages=messages,
                tools=tools,
                temperature=0.7,
            )

            # Extract tool calls
            tool_calls = response.choices[0].message.tool_calls

            if tool_calls and len(tool_calls) > 0:
                # Extract the arguments from the function call
                tool_call = tool_calls[0]
                function_args = json.loads(tool_call.function.arguments)

                if "agents" in function_args and isinstance(function_args["agents"], list):
                    agents = function_args["agents"]
                    if all(isinstance(a, str) for a in agents):
                        logger.info(f"Selected agents (attempt {attempt+1}): {agents}")
                        return agents

            logger.warning(f"Failed to parse agent selection from tool call on attempt {attempt+1}")

        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {str(e)}")

        if attempt == max_retries - 1:
            logger.error("All retries failed")
            return ["default"]

    return []


async def run_delegation(chat_request: ChatRequest) -> Tuple[Optional[str], AgentResponse]:
    """Run the delegation process to find and execute the best agent for the request"""
    attempted_agents: set[str] = set()

    try:
        # Get ranked agents based on LLM delegation
        ranked_agents = _get_delegator_response(chat_request, attempted_agents)

        for agent_name in ranked_agents:
            attempted_agents.add(agent_name)
            logger.info(f"Attempting agent: {agent_name}")

            result = await _try_agent(agent_name, chat_request)
            if result:
                logger.info(f"Successfully used agent: {agent_name}")
                return agent_name, result

        return None, AgentResponse.error(error_message="All agents have been attempted without success")

    except ValueError as ve:
        logger.error(f"No available agents: {str(ve)}")
        return None, AgentResponse.error(error_message="No suitable agents available for the request")

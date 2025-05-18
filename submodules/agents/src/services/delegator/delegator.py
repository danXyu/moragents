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
        agent = agent_manager_instance.get_agent(agent_name)
        if not agent:
            logger.error(f"Agent {agent_name} not found")
            return None

        result: AgentResponse = await agent.chat(chat_request)

        if result.response_type == ResponseType.ERROR:
            logger.warning(f"Agent {agent_name} returned error response")
            logger.error(f"Error message: {result.error_message}")
            return None

        return result

    except Exception as e:
        logger.error(f"Error using agent {agent_name}: {str(e)}")
        return None


def _get_delegator_response(chat_request: ChatRequest, attempted_agents: set[str], max_retries: int = 3) -> List[str]:
    """Get ranked list of appropriate agents"""
    # Get all available agents
    all_available_agents = agent_manager_instance.get_available_agents()
    logger.info(f"All available agents: {all_available_agents}")

    # Filter by selected agents if specified in the request
    available_agents = all_available_agents
    if chat_request.selected_agents:
        available_agents = [
            agent for agent in all_available_agents if agent.get("name") in chat_request.selected_agents
        ]
        logger.info(f"Filtered to selected agents: {available_agents}")

    if not available_agents:
        if "default" not in attempted_agents:
            return ["default"]
        raise ValueError("No remaining agents available")

    # Build message list for Together API
    messages = [{"role": "system", "content": get_system_prompt(available_agents)}]

    # Add chat history (last 5 messages)
    for msg in chat_request.chat_history[-5:]:
        messages.append({"role": msg.role, "content": msg.content})

    # Add current prompt
    messages.append({"role": "user", "content": chat_request.prompt.content})

    # Define the agent ranking tool
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
            response = TOGETHER_CLIENT.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                messages=messages,
                tools=tools,
                temperature=0.7,
                tool_choice="auto",  # Let model decide when to use tools
            )

            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                logger.error(f"No tool calls in response (attempt {attempt + 1})")
                continue

            tool_call = tool_calls[0]
            if tool_call.function.name != "rank_agents":
                logger.error(f"Unexpected function call {tool_call.function.name} (attempt {attempt + 1})")
                continue

            try:
                function_args = json.loads(tool_call.function.arguments)
                agents = function_args.get("agents", [])

                if not isinstance(agents, list) or not all(isinstance(a, str) for a in agents):
                    logger.error(f"Invalid agents format in response (attempt {attempt + 1})")
                    continue

                # Validate agent names against available agents
                valid_agents = [a for a in agents if any(av.get("name") == a for av in available_agents)]
                if valid_agents:
                    logger.info(f"Selected agents: {valid_agents}")
                    return valid_agents

                logger.error(f"No valid agents in response (attempt {attempt + 1})")

            except json.JSONDecodeError:
                logger.error(f"Failed to parse function arguments (attempt {attempt + 1})")
                continue

        except Exception as e:
            logger.error(f"Error in delegator response (attempt {attempt + 1}): {str(e)}")

    # If all retries fail, return default agent
    logger.error("All delegator attempts failed, falling back to default agent")
    return ["default"]


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

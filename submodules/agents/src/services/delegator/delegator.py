import importlib
import json
import logging
from typing import Any, List, Optional, Tuple

from config import LLM_AGENT, LLM_DELEGATOR, load_agent_config
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import BaseMessage, SystemMessage
from models.service.chat_models import AgentResponse, ChatRequest, ResponseType
from pydantic import BaseModel, Field
from stores import agent_manager_instance

from .system_prompt import get_system_prompt

logger = logging.getLogger(__name__)


class RankAgentsOutput(BaseModel):
    """JSON schema for agent ranking output"""

    agents: List[str] = Field(..., description="List of up to 3 agent names, ordered by relevance")


class Delegator:
    def __init__(self, llm: Any):
        self.llm = LLM_DELEGATOR
        self.attempted_agents: set[str] = set()
        self.selected_agents_for_request: list[str] = []
        self.parser = PydanticOutputParser(pydantic_object=RankAgentsOutput)

    async def _try_agent(self, agent_name: str, chat_request: ChatRequest) -> Optional[AgentResponse]:
        """Attempt to use a single agent, with error handling"""
        try:
            agent_config = load_agent_config(agent_name)
            if not agent_config:
                logger.error(f"Could not load config for agent {agent_name}")

                return None

            module = importlib.import_module(agent_config["path"])
            agent_class = getattr(module, agent_config["class_name"])
            agent = agent_class(agent_config, LLM_AGENT)

            result: AgentResponse = await agent.chat(chat_request)

            if result.response_type == ResponseType.ERROR:
                logger.warning(f"Agent {agent_name} returned error response. You should probably look into this")
                logger.error(f"Error message: {result.error_message}")
                return None

            return result

        except Exception as e:
            logger.error(f"Error using agent {agent_name}: {str(e)}")
            return None

    def get_delegator_response(self, prompt: ChatRequest, max_retries: int = 3) -> List[str]:
        """Get ranked list of appropriate agents with retry logic"""
        available_agents = agent_manager_instance.get_available_agents()
        logger.info(f"Available agents: {available_agents}")

        if not available_agents:
            if "default" not in self.attempted_agents:
                return ["default"]
            raise ValueError("No remaining agents available")

        system_prompt = get_system_prompt(available_agents)

        # Build message history from chat history
        messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
        messages.extend(prompt.messages_for_llm)

        for attempt in range(max_retries):
            try:
                response = self.llm(messages)
                try:
                    # First try parsing as JSON directly
                    json_response = json.loads(response.content)
                    if isinstance(json_response, dict) and "agents" in json_response:
                        agents = json_response["agents"]
                        if isinstance(agents, list) and all(isinstance(a, str) for a in agents):
                            self.selected_agents_for_request = agents
                            logger.info(f"Selected agents (attempt {attempt+1}): {agents}")
                            return agents
                except json.JSONDecodeError:
                    pass

                # Fallback to pydantic parser
                parsed = self.parser.parse(response.content)
                self.selected_agents_for_request = parsed.agents
                logger.info(f"Selected agents (attempt {attempt+1}): {parsed.agents}")
                return parsed.agents

            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("All retries failed")
                    return ["default"]
        return []

    async def delegate_chat(self, chat_request: ChatRequest) -> Tuple[Optional[str], AgentResponse]:
        """Delegate chat to ranked agents with fallback"""
        attempts = 0
        try:
            ranked_agents = self.get_delegator_response(chat_request)

            for agent_name in ranked_agents:
                attempts += 1
                self.attempted_agents.add(agent_name)
                logger.info(f"Attempting agent: {agent_name}")

                result = await self._try_agent(agent_name, chat_request)
                if result:
                    logger.info(f"Successfully used agent: {agent_name}")
                    return agent_name, result

            return None, AgentResponse.error(error_message="All agents have been attempted without success")

        except ValueError as ve:
            logger.error(f"No available agents: {str(ve)}")
            return None, AgentResponse.error(error_message="No suitable agents available for the request")

import logging
from typing import Any, Dict

from models.service.agent_core import AgentCore
from models.service.chat_models import AgentResponse, ChatRequest

from .config import Config
from .tools import generate_tweet

logger = logging.getLogger(__name__)


class TweetSizzlerAgent(AgentCore):
    """Agent for generating memorable tweets."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tools_provided = Config.tools

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for tweet generation."""
        try:
            messages = [Config.system_message, *request.messages_for_llm]
            response = await self._call_llm_with_tools(messages, self.tools_provided)
            return await self._handle_llm_response(response)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute the appropriate tool based on function name."""
        try:
            if func_name == "generate_tweet":
                content = args.get("content")
                if not content:
                    return AgentResponse.error(error_message="Please provide content for tweet generation")

                result = await generate_tweet(content)
                return AgentResponse.success(content=result)

            else:
                return AgentResponse.error(error_message=f"Unknown tool function: {func_name}")

        except Exception as e:
            logger.error(f"Error executing tool {func_name}: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

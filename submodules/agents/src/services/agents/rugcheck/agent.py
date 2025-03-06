import logging
from typing import Dict, Any
from models.service.agent_core import AgentCore
from models.service.chat_models import ChatRequest, AgentResponse
from .config import Config, TokenRegistry
from .tool_types import RugcheckToolType
from .tools import (
    fetch_token_report,
    fetch_most_viewed,
    fetch_most_voted,
    resolve_token_identifier,
)

logger = logging.getLogger(__name__)


class RugcheckAgent(AgentCore):
    """Agent for analyzing token safety and trends using the Rugcheck API."""

    def __init__(self, config: Dict[str, Any], llm: Any):
        super().__init__(config, llm)
        self.tools_provided = Config.tools
        self.tool_bound_llm = self.llm.bind_tools(self.tools_provided)
        self.api_base_url = "https://api.rugcheck.xyz/v1"
        self.token_registry = TokenRegistry()

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for token analysis."""
        try:
            messages = [Config.system_message, *request.messages_for_llm]

            result = self.tool_bound_llm.invoke(messages)
            return await self._handle_llm_response(result)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute the appropriate Rugcheck API tool based on function name."""
        try:
            if func_name == RugcheckToolType.GET_TOKEN_REPORT.value:
                identifier = args.get("identifier")
                if not identifier:
                    return AgentResponse.error(error_message="Please provide a token name or mint address")

                try:
                    mint_address = await resolve_token_identifier(self.token_registry, identifier)
                    if not mint_address:
                        return AgentResponse.error(error_message=f"Could not resolve token identifier: {identifier}")

                    report_response = await fetch_token_report(self.api_base_url, mint_address)
                    return AgentResponse.success(
                        content=report_response.formatted_response,
                        metadata=report_response.model_dump(),
                        action_type=RugcheckToolType.GET_TOKEN_REPORT.value,
                    )

                except Exception as e:
                    return AgentResponse.error(error_message=f"Failed to get token report: {str(e)}")

            elif func_name == RugcheckToolType.GET_MOST_VIEWED.value:
                try:
                    viewed_response = await fetch_most_viewed(self.api_base_url)
                    return AgentResponse.success(
                        content=viewed_response.formatted_response,
                        metadata=viewed_response.model_dump(),
                        action_type=RugcheckToolType.GET_MOST_VIEWED.value,
                    )

                except Exception as e:
                    return AgentResponse.error(error_message=f"Failed to get most viewed tokens: {str(e)}")

            elif func_name == RugcheckToolType.GET_MOST_VOTED.value:
                try:
                    voted_response = await fetch_most_voted(self.api_base_url)
                    return AgentResponse.success(
                        content=voted_response.formatted_response,
                        metadata=voted_response.model_dump(),
                        action_type=RugcheckToolType.GET_MOST_VOTED.value,
                    )

                except Exception as e:
                    return AgentResponse.error(error_message=f"Failed to get most voted tokens: {str(e)}")

            else:
                return AgentResponse.error(error_message=f"Unknown tool function: {func_name}")

        except Exception as e:
            logger.error(f"Error executing tool {func_name}: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

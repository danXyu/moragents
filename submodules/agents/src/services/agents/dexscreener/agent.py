import logging
from typing import Dict, Any, Union
from models.service.agent_core import AgentCore
from models.service.chat_models import ChatRequest, AgentResponse
from .config import Config
from . import tools
from .tool_types import DexScreenerToolType
from .models import (
    TokenProfileResponse,
    BoostedTokenResponse,
    DexPairSearchResponse,
)

logger = logging.getLogger(__name__)


class DexScreenerAgent(AgentCore):
    """Agent for interacting with DexScreener Token API."""

    def __init__(self, config: Dict[str, Any], llm: Any):
        super().__init__(config, llm)
        self.tools_provided = Config.tools
        self.tool_bound_llm = self.llm.bind_tools(self.tools_provided)

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for DexScreener API interactions."""
        try:
            messages = [Config.system_message, *request.messages_for_llm]
            result = self.tool_bound_llm.invoke(messages)
            return await self._handle_llm_response(result)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute the appropriate DexScreener API tool based on function name."""
        try:
            api_result: Union[DexPairSearchResponse, TokenProfileResponse, BoostedTokenResponse]

            if func_name == DexScreenerToolType.SEARCH_DEX_PAIRS.value:
                api_result = await tools.search_dex_pairs(args["query"])
                return AgentResponse.success(
                    content=api_result.formatted_response,
                    metadata=api_result.model_dump(),
                    action_type=DexScreenerToolType.SEARCH_DEX_PAIRS.value,
                )
            elif func_name == DexScreenerToolType.GET_LATEST_TOKEN_PROFILES.value:
                api_result = await tools.get_latest_token_profiles(args.get("chain_id"))
                return AgentResponse.success(
                    content=api_result.formatted_response,
                    metadata=api_result.model_dump(),
                    action_type=DexScreenerToolType.GET_LATEST_TOKEN_PROFILES.value,
                )
            elif func_name == DexScreenerToolType.GET_LATEST_BOOSTED_TOKENS.value:
                api_result = await tools.get_latest_boosted_tokens(args.get("chain_id"))
                return AgentResponse.success(
                    content=api_result.formatted_response,
                    metadata=api_result.model_dump(),
                    action_type=DexScreenerToolType.GET_LATEST_BOOSTED_TOKENS.value,
                )
            elif func_name == DexScreenerToolType.GET_TOP_BOOSTED_TOKENS.value:
                api_result = await tools.get_top_boosted_tokens(args.get("chain_id"))
                return AgentResponse.success(
                    content=api_result.formatted_response,
                    metadata=api_result.model_dump(),
                    action_type=DexScreenerToolType.GET_TOP_BOOSTED_TOKENS.value,
                )
            else:
                return AgentResponse.error(error_message=f"Unknown tool: {func_name}")

        except Exception as e:
            logger.error(f"Error executing tool {func_name}: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

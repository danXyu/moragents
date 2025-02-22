import logging
from typing import Dict, Any
from models.service.agent_core import AgentCore
from models.service.chat_models import ChatRequest, AgentResponse
from .config import Config
from . import tools
from .models import TopTokensResponse, TopHoldersResponse, NftSearchResponse
from .tool_types import CodexToolType

logger = logging.getLogger(__name__)


class CodexAgent(AgentCore):
    """Agent for interacting with Codex.io API."""

    def __init__(self, config: Dict[str, Any], llm: Any, embeddings: Any):
        super().__init__(config, llm, embeddings)
        self.tools_provided = Config.tools
        self.tool_bound_llm = self.llm.bind_tools(self.tools_provided)

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for Codex API interactions."""
        try:
            messages = [Config.system_message, *request.messages_for_llm]

            result = self.tool_bound_llm.invoke(messages)
            return await self._handle_llm_response(result)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute the appropriate Codex API tool based on function name."""
        try:
            if func_name == CodexToolType.LIST_TOP_TOKENS.value:
                top_tokens_response: TopTokensResponse = await tools.list_top_tokens(
                    limit=args.get("limit"),
                    network_filter=args.get("networkFilter"),
                    resolution=args.get("resolution"),
                )
                return AgentResponse.success(
                    content=top_tokens_response.formatted_response,
                    metadata=top_tokens_response.model_dump(),
                    action_type=CodexToolType.LIST_TOP_TOKENS.value,
                )

            elif func_name == CodexToolType.GET_TOP_HOLDERS_PERCENT.value:
                holders_response: TopHoldersResponse = await tools.get_top_holders_percent(
                    token_id=args["tokenId"],
                )
                return AgentResponse.success(
                    content=holders_response.formatted_response,
                    metadata=holders_response.model_dump(),
                    action_type=CodexToolType.GET_TOP_HOLDERS_PERCENT.value,
                )

            elif func_name == CodexToolType.SEARCH_NFTS.value:
                nft_search_response: NftSearchResponse = await tools.search_nfts(
                    search=args["search"],
                    limit=args.get("limit"),
                    network_filter=args.get("networkFilter"),
                    filter_wash_trading=args.get("filterWashTrading"),
                    window=args.get("window"),
                )
                return AgentResponse.success(
                    content=nft_search_response.formatted_response,
                    metadata=nft_search_response.model_dump(),
                    action_type=CodexToolType.SEARCH_NFTS.value,
                )

            else:
                return AgentResponse.error(error_message=f"Unknown tool: {func_name}")

        except Exception as e:
            logger.error(f"Error executing tool {func_name}: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

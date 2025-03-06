import logging
from typing import Dict, Any
from models.service.agent_core import AgentCore
from models.service.chat_models import ChatRequest, AgentResponse
from .config import Config
from .tools import list_top_tokens, get_top_holders_percent, search_nfts
from .models import TopTokensResponse, TopHoldersResponse, NftSearchResponse
from .utils.tool_types import CodexToolType
from .utils.networks import NETWORK_TO_ID_MAPPING

logger = logging.getLogger(__name__)


class CodexAgent(AgentCore):
    """Agent for interacting with Codex.io API."""

    def __init__(self, config: Dict[str, Any], llm: Any):
        super().__init__(config, llm)
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
                top_tokens_response: TopTokensResponse = await list_top_tokens(
                    limit=args.get("limit"),
                    networks=args.get("networks"),
                    resolution=args.get("resolution"),
                )
                return AgentResponse.success(
                    content=top_tokens_response.formatted_response,
                    metadata=top_tokens_response.model_dump(),
                    action_type=CodexToolType.LIST_TOP_TOKENS.value,
                )

            elif func_name == CodexToolType.GET_TOP_HOLDERS_PERCENT.value:
                if args.get("tokenName") is None:
                    return AgentResponse.needs_info(
                        content="Please specify both the token name and network you'd like to get top holders for"
                    )

                if args.get("network") is None:
                    return AgentResponse.needs_info(
                        content=f"Please specify the network (Ethereum, Solana, etc.) you'd like to search for {args.get('tokenName')}"
                    )

                if args.get("network") not in NETWORK_TO_ID_MAPPING:
                    return AgentResponse.needs_info(
                        content=f"Please specify a valid network (Ethereum, Solana, etc.) you'd like to search for {args.get('tokenName')}"
                    )

                holders_response: TopHoldersResponse = await get_top_holders_percent(
                    token_name=args["tokenName"],
                    network=args["network"],
                )
                return AgentResponse.success(
                    content=holders_response.formatted_response,
                    metadata=holders_response.model_dump(),
                    action_type=CodexToolType.GET_TOP_HOLDERS_PERCENT.value,
                )

            elif func_name == CodexToolType.SEARCH_NFTS.value:
                nft_search_response: NftSearchResponse = await search_nfts(
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

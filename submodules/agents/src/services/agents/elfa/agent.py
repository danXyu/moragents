import logging
from typing import Dict, Any
from models.service.agent_core import AgentCore
from models.service.chat_models import ChatRequest, AgentResponse

from .config import Config
from .tool_types import ElfaToolType
from .models import (
    ElfaMentionsResponse,
    ElfaTopMentionsResponse,
    ElfaTrendingTokensResponse,
    ElfaAccountSmartStatsResponse,
)
from .tools import (
    get_mentions,
    get_top_mentions,
    search_mentions,
    get_trending_tokens,
    get_account_smart_stats,
)

logger = logging.getLogger(__name__)


class ElfaAgent(AgentCore):
    """Agent for interacting with Elfa Social API."""

    def __init__(self, config: Dict[str, Any], llm: Any, embeddings: Any):
        super().__init__(config, llm, embeddings)
        self.tools_provided = Config.tools
        self.tool_bound_llm = self.llm.bind_tools(self.tools_provided)

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for Elfa API interactions."""
        try:
            messages = [Config.system_message, *request.messages_for_llm]

            result = self.tool_bound_llm.invoke(messages)
            return await self._handle_llm_response(result)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute the appropriate Elfa API tool based on function name."""
        try:
            if func_name == ElfaToolType.GET_MENTIONS.value:
                mentions_response: ElfaMentionsResponse = await get_mentions(limit=args.get("limit"))
                return AgentResponse.success(
                    content=mentions_response.formatted_response,
                    metadata=mentions_response.model_dump(),
                    action_type=ElfaToolType.GET_MENTIONS.value,
                )

            elif func_name == ElfaToolType.GET_TOP_MENTIONS.value:
                top_mentions_response: ElfaTopMentionsResponse = await get_top_mentions(
                    ticker=args["ticker"],
                    time_window=args.get("timeWindow"),
                    include_account_details=args.get("includeAccountDetails"),
                )
                return AgentResponse.success(
                    content=top_mentions_response.formatted_response,
                    metadata=top_mentions_response.model_dump(),
                    action_type=ElfaToolType.GET_TOP_MENTIONS.value,
                )

            elif func_name == ElfaToolType.SEARCH_MENTIONS.value:
                keywords = args.get("keywords", ["crypto"])
                if isinstance(keywords, str):
                    keywords = [keywords]

                search_mentions_response: ElfaMentionsResponse = await search_mentions(keywords=keywords)
                return AgentResponse.success(
                    content=search_mentions_response.formatted_response,
                    metadata=search_mentions_response.model_dump(),
                    action_type=ElfaToolType.SEARCH_MENTIONS.value,
                )

            elif func_name == ElfaToolType.GET_TRENDING_TOKENS.value:
                trending_tokens_response: ElfaTrendingTokensResponse = await get_trending_tokens(
                    time_window=args.get("timeWindow"), min_mentions=args.get("minMentions")
                )
                return AgentResponse.success(
                    content=trending_tokens_response.formatted_response,
                    metadata=trending_tokens_response.model_dump(),
                    action_type=ElfaToolType.GET_TRENDING_TOKENS.value,
                )

            elif func_name == ElfaToolType.GET_ACCOUNT_SMART_STATS.value:
                smart_stats_response: ElfaAccountSmartStatsResponse = await get_account_smart_stats(args["username"])
                return AgentResponse.success(
                    content=smart_stats_response.formatted_response,
                    metadata=smart_stats_response.model_dump(),
                    action_type=ElfaToolType.GET_ACCOUNT_SMART_STATS.value,
                )

            else:
                return AgentResponse.error(error_message=f"Unknown tool: {func_name}")

        except Exception as e:
            logger.error(f"Error executing tool {func_name}: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

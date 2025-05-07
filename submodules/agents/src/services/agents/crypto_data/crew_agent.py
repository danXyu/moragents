# import logging
# from typing import Any, Dict, List

# from crewai.tools import Tool as CrewTool

# from models.service.chat_models import AgentResponse, ChatRequest
# from services.agents.crypto_data import tools
# from services.agents.crypto_data.config import Config
# from services.agents.crypto_data.tool_types import CryptoDataToolType
# from models.service.agent_core_crew import CrewAgentCore


# logger = logging.getLogger(__name__)


# class CryptoDataAgent(CrewAgentCore):
#     """Agent for handling cryptocurrency-related queries using CrewAI."""

#     def __init__(self, config: Dict[str, Any], llm: Any) -> None:
#         super().__init__(config, llm)

#     def _create_tools(self) -> List[CrewTool]:
#         """Create CrewAI tool instances for crypto operations"""
#         return [
#             CrewTool(
#                 name=CryptoDataToolType.GET_PRICE.value,
#                 description="Get the current price of a cryptocurrency.",
#                 func=self._get_coin_price,
#             ),
#             CrewTool(
#                 name=CryptoDataToolType.GET_FLOOR_PRICE.value,
#                 description="Get the floor price of an NFT collection.",
#                 func=self._get_nft_floor_price,
#             ),
#             CrewTool(
#                 name=CryptoDataToolType.GET_TOTAL_VALUE_LOCKED.value,
#                 description="Get the total value locked in a DeFi protocol.",
#                 func=self._get_protocol_tvl,
#             ),
#             CrewTool(
#                 name=CryptoDataToolType.GET_FULLY_DILUTED_VALUATION.value,
#                 description="Get the fully diluted valuation of a cryptocurrency.",
#                 func=self._get_fdv,
#             ),
#             CrewTool(
#                 name=CryptoDataToolType.GET_MARKET_CAP.value,
#                 description="Get the market capitalization of a cryptocurrency.",
#                 func=self._get_market_cap,
#             ),
#         ]

#     def _get_coin_price(self, coin_name: str) -> str:
#         """Get the current price of a cryptocurrency."""
#         return tools.get_coin_price_tool(coin_name)

#     def _get_nft_floor_price(self, nft_name: str) -> str:
#         """Get the floor price of an NFT collection."""
#         return tools.get_nft_floor_price_tool(nft_name)

#     def _get_protocol_tvl(self, protocol_name: str) -> str:
#         """Get the total value locked in a DeFi protocol."""
#         return tools.get_protocol_total_value_locked_tool(protocol_name)

#     def _get_fdv(self, coin_name: str) -> str:
#         """Get the fully diluted valuation of a cryptocurrency."""
#         return tools.get_fully_diluted_valuation_tool(coin_name)

#     def _get_market_cap(self, coin_name: str) -> str:
#         """Get the market capitalization of a cryptocurrency."""
#         return tools.get_coin_market_cap_tool(coin_name)

#     async def _process_result(self, result: str, request: ChatRequest) -> AgentResponse:
#         """Process the result from CrewAI execution"""
#         # Check if result contains error indicators
#         if "error" in result.lower() or "not found" in result.lower():
#             return AgentResponse.needs_info(content=result)

#         # Extract metadata if available
#         metadata = {}

#         # Check if the result mentions a specific coin
#         # This is a simplified approach - in a real implementation, you would
#         # parse the crew_agent's execution trace to identify which tools were called
#         import re

#         # Try to detect coin mentions with a basic regex pattern
#         coin_pattern = re.compile(
#             r"(bitcoin|btc|ethereum|eth|litecoin|ltc|ripple|xrp|cardano|ada|solana|sol)", re.IGNORECASE
#         )
#         coin_match = coin_pattern.search(result)

#         if coin_match:
#             coin_name = coin_match.group(0)
#             trading_symbol = tools.get_tradingview_symbol(tools.get_coingecko_id(coin_name))
#             if trading_symbol:
#                 metadata["coinId"] = trading_symbol

#         return AgentResponse.success(content=result, metadata=metadata)

#     def _create_task_description(self, request: ChatRequest) -> str:
#         """Create a task description based on the request"""
#         return f"""
#         {Config.system_message.content}

#         Process the following user request about cryptocurrency:
#         "{request.prompt}"

#         First, determine what type of crypto information the user is looking for.
#         Then, use the appropriate tool to fetch accurate information.

#         Available tools:
#         - get_price: Get current price of a cryptocurrency
#         - get_floor_price: Get floor price of an NFT collection
#         - get_total_value_locked: Get TVL of a DeFi protocol
#         - get_fully_diluted_valuation: Get FDV of a cryptocurrency
#         - get_market_cap: Get market cap of a cryptocurrency

#         Return your answer in a clear and helpful format.
#         """

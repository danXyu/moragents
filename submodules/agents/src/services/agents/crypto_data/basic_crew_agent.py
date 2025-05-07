import logging
from typing import Any, Dict, List

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.crypto_data import tools
from services.agents.crypto_data.config import Config
from services.agents.crypto_data.tool_types import CryptoDataToolType


logger = logging.getLogger(__name__)


# Create the tools using the tool decorator
@tool("Get Cryptocurrency Price")
def get_coin_price_tool(coin_name: str) -> str:
    """Get the current price of a cryptocurrency."""
    return tools.get_coin_price_tool(coin_name)


@tool("Get NFT Floor Price")
def get_nft_floor_price_tool(nft_name: str) -> str:
    """Get the floor price of an NFT collection."""
    return tools.get_nft_floor_price_tool(nft_name)


@tool("Get Protocol Total Value Locked")
def get_protocol_tvl_tool(protocol_name: str) -> str:
    """Get the total value locked in a DeFi protocol."""
    return tools.get_protocol_total_value_locked_tool(protocol_name)


@tool("Get Fully Diluted Valuation")
def get_fdv_tool(coin_name: str) -> str:
    """Get the fully diluted valuation of a cryptocurrency."""
    return tools.get_fully_diluted_valuation_tool(coin_name)


@tool("Get Market Capitalization")
def get_market_cap_tool(coin_name: str) -> str:
    """Get the market capitalization of a cryptocurrency."""
    return tools.get_coin_market_cap_tool(coin_name)


# Create the agent directly
crypto_data_agent = Agent(
    role="Cryptocurrency Data Expert",
    goal="Provide accurate cryptocurrency data and analysis",
    backstory="You are a specialized cryptocurrency analyst with expertise in market data, NFTs, and DeFi protocols.",
    verbose=True,
    tools=[get_coin_price_tool, get_nft_floor_price_tool, get_protocol_tvl_tool, get_fdv_tool, get_market_cap_tool],
    allow_delegation=False,
)

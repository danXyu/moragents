import logging
from typing import Any, Dict, List, Optional

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.dexscreener import tools
from services.agents.dexscreener.config import Config
from services.agents.dexscreener.tool_types import DexScreenerToolType


logger = logging.getLogger(__name__)


# Create the tools using the tool decorator
@tool("Search DEX Pairs")
def search_dex_pairs_tool(query: str) -> str:
    """Search for DEX trading pairs and their activity."""
    result = tools.search_dex_pairs(query=query)
    return result.formatted_response


@tool("Get Latest Token Profiles")
def get_latest_token_profiles_tool(chain_id: Optional[str] = None) -> str:
    """Get the latest token profiles from DexScreener."""
    result = tools.get_latest_token_profiles(chain_id=chain_id)
    return result.formatted_response


@tool("Get Latest Boosted Tokens")
def get_latest_boosted_tokens_tool(chain_id: Optional[str] = None) -> str:
    """Get the latest boosted tokens from DexScreener."""
    result = tools.get_latest_boosted_tokens(chain_id=chain_id)
    return result.formatted_response


@tool("Get Top Boosted Tokens")
def get_top_boosted_tokens_tool(chain_id: Optional[str] = None) -> str:
    """Get the tokens with most active boosts."""
    result = tools.get_top_boosted_tokens(chain_id=chain_id)
    return result.formatted_response


# Create the agent directly
dexscreener_agent = Agent(
    role="DexScreener Analyst",
    goal="Provide accurate DEX trading pair data and token analysis",
    backstory="You are a specialized analyst with expertise in cryptocurrency trading pairs, token profiles, and boosted tokens data from DexScreener.",
    verbose=True,
    tools=[
        search_dex_pairs_tool,
        get_latest_token_profiles_tool,
        get_latest_boosted_tokens_tool,
        get_top_boosted_tokens_tool,
    ],
    allow_delegation=False,
)

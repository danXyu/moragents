import logging
from typing import Any, Dict, List, Optional

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.codex import tools
from services.agents.codex.config import Config
from services.agents.codex.utils.tool_types import CodexToolType


logger = logging.getLogger(__name__)


# Create the tools using the tool decorator
@tool("List Top Tokens")
def list_top_tokens_tool(
    limit: Optional[int] = None, networks: Optional[List[str]] = None, resolution: Optional[str] = None
) -> str:
    """Get a list of trending tokens across specified networks."""
    result = tools.list_top_tokens(limit=limit, networks=networks, resolution=resolution)
    return result.formatted_response


@tool("Get Top Holders Percentage")
def get_top_holders_percent_tool(token_name: str, network: str) -> str:
    """Get the percentage owned by top 10 holders for a token."""
    result = tools.get_top_holders_percent(token_name=token_name, network=network)
    return result.formatted_response


@tool("Search NFT Collections")
def search_nfts_tool(
    search: str,
    limit: Optional[int] = None,
    network_filter: Optional[List[int]] = None,
    filter_wash_trading: Optional[bool] = None,
    window: Optional[str] = None,
) -> str:
    """Search for NFT collections by name or address."""
    result = tools.search_nfts(
        search=search,
        limit=limit,
        network_filter=network_filter,
        filter_wash_trading=filter_wash_trading,
        window=window,
    )
    return result.formatted_response


# Create the agent directly
codex_agent = Agent(
    role="Codex Market Analyst",
    goal="Provide accurate cryptocurrency market data and NFT collection analysis",
    backstory="You are a specialized market analyst with expertise in cryptocurrency tokens, holder analysis, and NFT collections data from Codex.io.",
    verbose=True,
    tools=[list_top_tokens_tool, get_top_holders_percent_tool, search_nfts_tool],
    allow_delegation=False,
)

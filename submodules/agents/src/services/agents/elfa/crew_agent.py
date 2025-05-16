import logging
from typing import List, Optional

from crewai import Agent
from crewai.tools import tool

from services.agents.elfa import tools

logger = logging.getLogger(__name__)


# Create the tools using the tool decorator
@tool("Get Top Mentions")
def get_top_mentions_tool(
    ticker: str, time_window: Optional[str] = None, include_account_details: Optional[bool] = None
) -> str:
    """Get the most viewed and engaged-with social media posts mentioning a specific cryptocurrency ticker symbol."""
    result = tools.get_top_mentions(
        ticker=ticker, time_window=time_window, include_account_details=include_account_details
    )
    return result.formatted_response


@tool("Search Mentions")
def search_mentions_tool(
    keywords: List[str] = ["crypto"],
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> str:
    """Search through all social media posts using custom keywords to find relevant cryptocurrency discussions."""
    result = tools.search_mentions(
        keywords=keywords, from_timestamp=from_timestamp, to_timestamp=to_timestamp, limit=limit, cursor=cursor
    )
    return result.formatted_response


@tool("Get Trending Tokens")
def get_trending_tokens_tool(time_window: Optional[str] = None, min_mentions: Optional[int] = None) -> str:
    """Get trending tokens based on social media mentions."""
    result = tools.get_trending_tokens(time_window=time_window, min_mentions=min_mentions)
    return result.formatted_response


@tool("Get Account Smart Stats")
def get_account_smart_stats_tool(username: str) -> str:
    """Get smart stats and social metrics for a given username."""
    result = tools.get_account_smart_stats(username=username)
    return result.formatted_response


# Create the agent directly
elfa_agent = Agent(
    role="Elfa Social Analyst",
    goal="Provide accurate cryptocurrency social media data and sentiment analysis",
    backstory="You are a specialized social media analyst with expertise in "
    "cryptocurrency mentions, trending tokens, and influential accounts "
    "across social platforms.",
    verbose=True,
    tools=[
        get_top_mentions_tool,
        search_mentions_tool,
        get_trending_tokens_tool,
        get_account_smart_stats_tool,
    ],
    allow_delegation=False,
)

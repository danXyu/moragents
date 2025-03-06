import logging
import os
from typing import Optional, List, Any

from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urlencode

from .tool_types import ElfaToolType
from .config import Config
from .models import (
    ElfaMentionsResponse,
    ElfaTopMentionsResponse,
    ElfaTrendingTokensResponse,
    ElfaAccountSmartStatsResponse,
)
from services.secrets import get_secret

logger = logging.getLogger(__name__)


async def _make_request(endpoint: str, params: Optional[dict] = None) -> Any:
    """Make an API request to Elfa."""
    url = f"{Config.BASE_URL}{endpoint}"
    if params:
        url = f"{url}?{urlencode(params)}"

    # Get API key from environment
    api_key = get_secret("ElfaApiKey")
    if not api_key:
        raise Exception("ELFA_API_KEY environment variable is not set")

    headers = {"x-elfa-api-key": api_key}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise Exception(f"API request failed with status {response.status}: {error_data}")
                return await response.json()
    except Exception as e:
        logger.error(f"API request failed: {str(e)}", exc_info=True)
        raise Exception(f"Failed to fetch data: {str(e)}")


async def get_top_mentions(
    ticker: str, time_window: Optional[str] = None, include_account_details: Optional[bool] = None
) -> ElfaTopMentionsResponse:
    """Get top mentions for a specific ticker."""
    try:
        params = {"ticker": ticker, "timeWindow": time_window or "1d", "page": 1, "pageSize": 10}  # Sensible defaults

        # Only add if explicitly set to True
        if include_account_details:
            params["includeAccountDetails"] = "true"

        response = await _make_request(Config.ENDPOINTS[ElfaToolType.GET_TOP_MENTIONS.value], params)
        return ElfaTopMentionsResponse.model_validate(response)
    except Exception as e:
        logger.error(f"Failed to get top mentions: {str(e)}", exc_info=True)
        raise Exception(f"Failed to get top mentions: {str(e)}")


async def search_mentions(
    keywords: List[str] = ["crypto"],
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> ElfaMentionsResponse:
    """Search for mentions by keywords within a time range. Defaults to last 7 days."""
    try:
        # Default to last 7 days if not specified
        now = datetime.now()
        default_to = int(now.timestamp())
        default_from = int((now - timedelta(days=7)).timestamp())

        params = {
            "keywords": ",".join(keywords[:5]),  # API limit of 5 keywords
            "from": from_timestamp or default_from,
            "to": to_timestamp or default_to,
            "limit": min(limit or 20, 30),  # Default 20, max 30
        }
        if cursor:
            params["cursor"] = cursor

        response = await _make_request(Config.ENDPOINTS[ElfaToolType.SEARCH_MENTIONS.value], params)
        return ElfaMentionsResponse.model_validate(response)
    except Exception as e:
        logger.error(f"Failed to search mentions: {str(e)}", exc_info=True)
        raise Exception(f"Failed to search mentions: {str(e)}")


async def get_trending_tokens(
    time_window: Optional[str] = None, min_mentions: Optional[int] = None
) -> ElfaTrendingTokensResponse:
    """Get trending tokens based on social media mentions."""
    try:
        params = {
            "timeWindow": time_window or "24h",
            "page": 1,  # Sensible defaults
            "pageSize": 50,
            "minMentions": min_mentions or 5,
        }
        response = await _make_request(Config.ENDPOINTS[ElfaToolType.GET_TRENDING_TOKENS.value], params)
        return ElfaTrendingTokensResponse.model_validate(response)
    except Exception as e:
        logger.error(f"Failed to get trending tokens: {str(e)}", exc_info=True)
        raise Exception(f"Failed to get trending tokens: {str(e)}")


async def get_account_smart_stats(username: str) -> ElfaAccountSmartStatsResponse:
    """Get smart stats and social metrics for a given username."""
    try:
        params = {"username": username}
        response = await _make_request(Config.ENDPOINTS[ElfaToolType.GET_ACCOUNT_SMART_STATS.value], params)
        return ElfaAccountSmartStatsResponse.model_validate(response)
    except Exception as e:
        logger.error(f"Failed to get account stats: {str(e)}", exc_info=True)
        raise Exception(f"Failed to get account stats: {str(e)}")

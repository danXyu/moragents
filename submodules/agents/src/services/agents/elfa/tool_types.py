from enum import Enum


class ElfaToolType(Enum):
    """Enum for different Elfa API tool types"""

    GET_TOP_MENTIONS = "get_top_mentions"
    SEARCH_MENTIONS = "search_mentions"
    GET_TRENDING_TOKENS = "get_trending_tokens"
    GET_ACCOUNT_SMART_STATS = "get_account_smart_stats"

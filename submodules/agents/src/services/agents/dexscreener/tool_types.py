from enum import Enum


class DexScreenerToolType(Enum):
    """Enum for different DexScreener API tool types"""

    SEARCH_DEX_PAIRS = "search_dex_pairs"
    GET_LATEST_TOKEN_PROFILES = "get_latest_token_profiles"
    GET_LATEST_BOOSTED_TOKENS = "get_latest_boosted_tokens"
    GET_TOP_BOOSTED_TOKENS = "get_top_boosted_tokens"

from enum import Enum


class CryptoDataToolType(Enum):
    """Enum for different Crypto Data API tool types"""

    GET_PRICE = "get_price"
    GET_FLOOR_PRICE = "get_floor_price"
    GET_FULLY_DILUTED_VALUATION = "get_fdv"
    GET_TOTAL_VALUE_LOCKED = "get_tvl"
    GET_MARKET_CAP = "get_market_cap"

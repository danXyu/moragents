from enum import Enum


class SwapToolType(Enum):
    """Tool types for the Token Swap Agent."""

    SWAP_TOKENS = "swap_tokens"
    GET_TRANSACTION_STATUS = "get_transaction_status"

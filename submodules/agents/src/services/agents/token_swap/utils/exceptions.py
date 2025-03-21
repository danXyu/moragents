class InsufficientFundsError(Exception):
    """Exception raised when user has insufficient funds for a swap."""

    pass


class TokenNotFoundError(Exception):
    """Exception raised when a token cannot be found."""

    pass


class SwapNotPossibleError(Exception):
    """Exception raised when a swap cannot be executed."""

    pass

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TokenInfo(BaseModel):
    """Model for token information."""

    symbol: str
    address: str


class TransactionStatus(str, Enum):
    """Status of a blockchain transaction."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REJECTED = "rejected"


class TransactionResponse(BaseModel):
    """Model for transaction response."""

    success: bool = True
    status: TransactionStatus
    tx_hash: Optional[str] = None
    from_address: str
    to_address: str
    value: Optional[float] = None
    token_address: Optional[str] = None
    token_symbol: Optional[str] = None
    error_message: Optional[str] = None
    network_id: int
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def formatted_response(self) -> str:
        """Format transaction response for display."""
        if not self.success:
            return f"Transaction failed: {self.error_message}"

        response = f"# Transaction {self.status.value.title()}\n\n"

        if self.tx_hash:
            response += f"Transaction Hash: `{self.tx_hash}`\n\n"

        response += f"From: `{self.from_address}`\n"
        response += f"To: `{self.to_address}`\n"

        if self.token_address and self.token_symbol:
            response += f"Token: {self.token_symbol} (`{self.token_address}`)\n"

        if self.value is not None:
            response += f"Value: {self.value}\n"

        if self.gas_used is not None and self.gas_price is not None:
            gas_cost = self.gas_used * self.gas_price / 1e18
            response += f"Gas Used: {self.gas_used}\n"
            response += f"Gas Price: {self.gas_price} wei\n"
            response += f"Gas Cost: {gas_cost:.8f} ETH\n"

        return response


class SwapRoute(BaseModel):
    """Model for swap route information."""

    name: str
    part: float
    from_token_address: str
    to_token_address: str


class SwapQuoteResponse(BaseModel):
    """Model for swap quote response."""

    success: bool = True
    src: str
    src_address: str
    src_amount: float
    dst: str
    dst_address: str
    dst_amount: float
    approve_tx_cb: str = "/approve"
    swap_tx_cb: str = "/swap"
    estimated_gas: Optional[int] = None
    routes: Optional[List[SwapRoute]] = None
    error_message: Optional[str] = None

    @property
    def formatted_response(self) -> str:
        """Format swap quote for response."""
        if not self.success:
            return f"Failed to generate swap quote: {self.error_message}"

        response = (
            f"Swap Quote: {self.src_amount} {self.src}\n"
            f"for {self.dst_amount} {self.dst}\n"
            f"Rate: 1 {self.src} = {self.dst_amount / self.src_amount:.2f} {self.dst}\n"
        )

        if self.estimated_gas:
            response += f"## Estimated Gas\n{self.estimated_gas} units\n\n"

        if self.routes and len(self.routes) > 0:
            response += f"## Routes\n"
            for idx, route in enumerate(self.routes):
                response += f"{idx+1}. {route.name} ({route.part * 100:.1f}%)\n"

        return response


class ApproveTransactionRequest(BaseModel):
    """Model for approve transaction request."""

    token_address: str
    spender_address: str
    amount: int
    wallet_address: str
    chain_id: int


class SwapTransactionRequest(BaseModel):
    """Model for swap transaction request."""

    from_token_address: str
    to_token_address: str
    amount: int
    from_address: str
    slippage: float = 0.5
    chain_id: int
    receiver_address: Optional[str] = None

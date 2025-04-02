import logging
from typing import Optional

from .client import RugcheckClient
from .config import TokenRegistry
from .models import (
    TokenReport,
    TokenReportResponse,
    TokenRisk,
    ViewedToken,
    ViewedTokensResponse,
    VotedToken,
    VotedTokensResponse,
)

logger = logging.getLogger(__name__)


# Tool Functions
async def fetch_token_report(api_base_url: str, mint: str) -> TokenReportResponse:
    """Fetch token report from Rugcheck API."""
    client = RugcheckClient(api_base_url)
    try:
        report_data = await client.get_token_report(mint)
        return TokenReportResponse(
            report=TokenReport(
                score=report_data.get("score"),
                risks=[TokenRisk(**risk) for risk in report_data.get("risks", [])],
            ),
            mint_address=mint,
            token_name=report_data.get("token_name", ""),
            identifier=mint,
        )
    finally:
        await client.close()


async def fetch_most_viewed(api_base_url: str) -> ViewedTokensResponse:
    """Fetch most viewed tokens from Rugcheck API."""
    client = RugcheckClient(api_base_url)
    try:
        viewed_data = await client.get_most_viewed()
        tokens = [ViewedToken(**token) for token in viewed_data]
        return ViewedTokensResponse(tokens=tokens)
    finally:
        await client.close()


async def fetch_most_voted(api_base_url: str) -> VotedTokensResponse:
    """Fetch most voted tokens from Rugcheck API."""
    client = RugcheckClient(api_base_url)
    try:
        voted_data = await client.get_most_voted()
        tokens = [VotedToken(**token) for token in voted_data]
        return VotedTokensResponse(tokens=tokens)
    finally:
        await client.close()


async def resolve_token_identifier(token_registry: TokenRegistry, identifier: str) -> Optional[str]:
    """
    Resolve a token identifier (name or mint address) to a mint address.
    Returns None if the identifier cannot be resolved.
    """
    # If it's already a mint address, return it directly
    if token_registry.is_valid_mint_address(identifier):
        return identifier

    # Try to resolve token name to mint address
    mint_address = token_registry.get_mint_by_name(identifier)
    if mint_address:
        return mint_address

    return None

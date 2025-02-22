from typing import List, Optional
from pydantic import BaseModel


class TokenLink(BaseModel):
    """Model representing a link associated with a token."""

    type: str
    label: str
    url: str


class TokenProfile(BaseModel):
    """Model representing a token's profile information."""

    url: str
    chainId: str
    tokenAddress: str
    icon: Optional[str] = None
    header: Optional[str] = None
    description: Optional[str] = None
    links: Optional[List[TokenLink]] = None


class TokenProfileResponse(BaseModel):
    """Model for token profile API responses with formatting capabilities."""

    tokens: List[TokenProfile]
    chain_id: Optional[str] = None

    @property
    def formatted_response(self) -> str:
        """Format token profile data into a readable markdown string."""
        if not self.tokens:
            chain_msg = f" for chain {self.chain_id}" if self.chain_id else ""
            return f"No tokens found{chain_msg}."

        tokens = self.tokens[:10]
        formatted = f"# Top {len(tokens)} Tokens"
        if self.chain_id:
            formatted += f" on {self.chain_id}"
        formatted += "\n\n"

        for token in tokens:
            if token.icon:
                formatted += f"![Token Icon]({token.icon})\n\n"

            formatted += f"### `{token.tokenAddress}`\n\n"

            if token.description:
                formatted += f"{token.description}\n\n"

            if token.links:
                formatted += "**Links**: "
                link_parts = [f"[DexScreener]({token.url})"]

                for link in token.links:
                    link_parts.append(f"[{link.type or link.label}]({link.url})")

                formatted += " • ".join(link_parts) + "\n\n"

            formatted += "\n---\n\n\n"

        return formatted


class BoostedToken(TokenProfile):
    """Model representing a boosted token, extending TokenProfile with boost amounts."""

    amount: float
    totalAmount: float


class BoostedTokenResponse(BaseModel):
    """Model for boosted token API responses with formatting capabilities."""

    tokens: List[BoostedToken]
    chain_id: Optional[str] = None

    @property
    def formatted_response(self) -> str:
        """Format boosted token data into a readable markdown string."""
        return TokenProfileResponse(tokens=self.tokens, chain_id=self.chain_id).formatted_response


class DexPair(BaseModel):
    """Model representing a DEX trading pair with detailed market information."""

    chainId: str
    dexId: str
    url: str
    pairAddress: str
    baseToken: TokenProfile
    quoteToken: TokenProfile
    priceNative: float
    priceUsd: Optional[float] = None
    txns: Optional[dict] = None
    volume: Optional[dict] = None
    priceChange: Optional[dict] = None
    liquidity: Optional[dict] = None
    fdv: Optional[float] = None
    pairCreatedAt: Optional[int] = None


class DexPairSearchResponse(BaseModel):
    """Model for DEX pair search responses with formatting capabilities."""

    pairs: List[DexPair]

    @property
    def formatted_response(self) -> str:
        """Format DEX pair data into a readable markdown string."""
        if not self.pairs:
            return "No DEX pairs found matching your search."

        pairs = self.pairs[:10]
        formatted = f"# Found {len(pairs)} popular DEX Trading Pairs\n\n"

        for pair in pairs:
            formatted += f"## {pair.baseToken.symbol} / {pair.quoteToken.symbol} on {pair.dexId.title()}\n"
            formatted += f"Chain: {pair.chainId.upper()}\n\n"

            if pair.priceUsd:
                formatted += f"Price: ${float(pair.priceUsd):.4f}\n"

                price_change = pair.priceChange.get("h24") if pair.priceChange else None
                if price_change is not None:
                    change_symbol = "📈" if float(price_change) > 0 else "📉"
                    formatted += f"24h Change: {change_symbol} {price_change:.2f}%\n"

            if pair.volume and pair.volume.get("h24"):
                formatted += f"24h Volume: ${float(pair.volume['h24']):,.2f}\n"

            if pair.liquidity and pair.liquidity.get("usd"):
                formatted += f"Liquidity: ${float(pair.liquidity['usd']):,.2f}\n"

            if pair.txns and pair.txns.get("h24"):
                txns = pair.txns["h24"]
                buys = txns.get("buys", 0)
                sells = txns.get("sells", 0)
                formatted += f"24h Transactions: {buys + sells} (🟢 {buys} buys, 🔴 {sells} sells)\n"

            formatted += "\n**Links**: "
            link_parts = [f"[DexScreener]({pair.url})"]

            if pair.info:
                for website in pair.info.get("websites", []):
                    link_parts.append(f"[{website.get('label', 'Website')}]({website.get('url')})")

                for social in pair.info.get("socials", []):
                    social_type = social.get("type", "").title()
                    link_parts.append(f"[{social_type}]({social.get('url')})")

            formatted += " • ".join(link_parts) + "\n\n"
            formatted += "\n---\n\n"

        return formatted

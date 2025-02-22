from pydantic import BaseModel
from typing import Dict, Any, Optional, List


# Response Models
class TokenRisk(BaseModel):
    """Model for token risk assessment."""

    name: str
    description: str
    score: float

    @property
    def formatted_response(self) -> str:
        """Format risk assessment for display."""
        return f"- {self.name}: {self.description} (Risk Score: {self.score:.2f})"


class TokenReport(BaseModel):
    """Model for complete token analysis report."""

    score: Optional[float]
    risks: List[TokenRisk]

    @property
    def formatted_response(self) -> str:
        """Format complete report for display."""
        formatted = "# Token Risk Analysis Report\n\n"
        formatted += f"Overall Risk Score: {self.score:.2f if self.score else 'Unknown'}\n\n"
        formatted += "## Risk Assessments:\n\n"
        for risk in self.risks:
            formatted += f"{risk.formatted_response}\n"
        return formatted


class TokenReportResponse(BaseModel):
    """Model for token report API response."""

    report: TokenReport
    mint_address: str
    token_name: str
    identifier: str

    @property
    def formatted_response(self) -> str:
        """Format complete response for display."""
        formatted = f"# Analysis Report for {self.token_name}\n\n"
        formatted += f"Mint Address: {self.mint_address}\n"
        formatted += f"Identifier: {self.identifier}\n\n"
        formatted += self.report.formatted_response
        return formatted


class ViewedToken(BaseModel):
    """Model for token view statistics."""

    mint: str
    metadata: Dict[str, Any]
    visits: int
    user_visits: int

    @property
    def formatted_response(self) -> str:
        """Format view statistics for display."""
        name = self.metadata.get("name", "Unknown Token")
        symbol = self.metadata.get("symbol", "???")
        formatted = f"## {name} ({symbol})\n"
        formatted += f"- Mint Address: {self.mint}\n"
        formatted += f"- Total Visits: {self.visits:,}\n"
        formatted += f"- Unique Visitors: {self.user_visits:,}\n"
        return formatted


class ViewedTokensResponse(BaseModel):
    """Model for viewed tokens API response."""

    tokens: List[ViewedToken]

    @property
    def formatted_response(self) -> str:
        """Format complete response for display."""
        formatted = "# Most Viewed Tokens (24h)\n\n"
        for token in self.tokens:
            formatted += f"{token.formatted_response}\n"
        return formatted


class VotedToken(BaseModel):
    """Model for token voting statistics."""

    mint: str
    up_count: int
    vote_count: int

    @property
    def formatted_response(self) -> str:
        """Format voting statistics for display."""
        formatted = f"## Token {self.mint}\n"
        formatted += f"- Upvotes: {self.up_count:,}\n"
        formatted += f"- Total Votes: {self.vote_count:,}\n"
        formatted += f"- Approval Rate: {(self.up_count/self.vote_count)*100:.1f}%\n"
        return formatted


class VotedTokensResponse(BaseModel):
    """Model for voted tokens API response."""

    tokens: List[VotedToken]

    @property
    def formatted_response(self) -> str:
        """Format complete response for display."""
        formatted = "# Most Voted Tokens (24h)\n\n"
        for token in self.tokens:
            formatted += f"{token.formatted_response}\n"
        return formatted

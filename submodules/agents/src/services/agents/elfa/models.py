from typing import List, Optional
from pydantic import BaseModel


class ElfaAccountData(BaseModel):
    """Model representing account profile data."""

    profileBannerUrl: Optional[str] = None
    profileImageUrl: Optional[str] = None
    description: Optional[str] = None
    userSince: str
    location: Optional[str] = None
    name: str


class ElfaAccount(BaseModel):
    """Model representing a social media account."""

    id: int
    username: str
    data: ElfaAccountData
    followerCount: int
    followingCount: int
    isVerified: bool


class ElfaMention(BaseModel):
    """Model representing a social media mention."""

    id: int
    type: str
    content: str
    originalUrl: Optional[str] = None
    data: Optional[str] = None
    likeCount: int
    quoteCount: int
    replyCount: int
    repostCount: int
    viewCount: int
    mentionedAt: str
    bookmarkCount: int
    account: ElfaAccount


class ElfaMentionsResponse(BaseModel):
    """Model for mentions API responses."""

    success: bool
    data: List[ElfaMention]

    @property
    def formatted_response(self) -> str:
        """Format mentions data into a readable markdown string."""
        if not self.success:
            return "Failed to get mentions."

        if not self.data:
            return "No mentions found."

        formatted = f"# Latest {len(self.data)} Social Media Mentions\n\n"

        for mention in self.data:
            formatted += f"## @{mention.account.username}\n\n"
            formatted += f"{mention.content}\n\n"

            formatted += "**Metrics**:\n"
            formatted += f"- 👁️ Views: {mention.viewCount:,}\n"
            formatted += f"- 🔄 Reposts: {mention.repostCount:,}\n"
            formatted += f"- 💬 Replies: {mention.replyCount:,}\n"
            formatted += f"- ❤️ Likes: {mention.likeCount:,}\n\n"

            formatted += f"Posted at: {mention.mentionedAt}\n\n"

            if mention.originalUrl:
                formatted += f"[View Original]({mention.originalUrl})\n\n"

            formatted += "---\n\n"

        return formatted


class ElfaMentionMetrics(BaseModel):
    """Model representing engagement metrics for a mention."""

    view_count: int
    repost_count: int
    reply_count: int
    like_count: int


class ElfaTopMention(BaseModel):
    """Model representing a top mention."""

    id: int
    content: str
    mentioned_at: str
    metrics: ElfaMentionMetrics


class ElfaTopMentionsData(BaseModel):
    """Model representing paginated top mentions data."""

    pageSize: int
    page: int
    total: int
    data: List[ElfaTopMention]


class ElfaTopMentionsResponse(BaseModel):
    """Model for top mentions API responses."""

    success: bool
    data: ElfaTopMentionsData

    @property
    def formatted_response(self) -> str:
        """Format top mentions data into a readable markdown string."""
        if not self.success:
            return "Failed to get top mentions."

        if not self.data.data:
            return "No top mentions found for this ticker."

        formatted = f"# Top Mentions (Total: {self.data.total})\n\n"

        for mention in self.data.data:
            formatted += f"### Post ID: {mention.id}\n\n"
            formatted += f"{mention.content}\n\n"

            formatted += "**Engagement**:\n"
            formatted += f"- 👁️ Views: {mention.metrics.view_count:,}\n"
            formatted += f"- 🔄 Reposts: {mention.metrics.repost_count:,}\n"
            formatted += f"- 💬 Replies: {mention.metrics.reply_count:,}\n"
            formatted += f"- ❤️ Likes: {mention.metrics.like_count:,}\n\n"

            formatted += f"Posted at: {mention.mentioned_at}\n\n"
            formatted += "---\n\n"

        return formatted


class ElfaTrendingToken(BaseModel):
    """Model representing a trending token."""

    change_percent: float
    previous_count: int
    current_count: int
    token: str


class ElfaTrendingTokensData(BaseModel):
    """Model representing paginated trending tokens data."""

    pageSize: int
    page: int
    total: int
    data: List[ElfaTrendingToken]


class ElfaTrendingTokensResponse(BaseModel):
    """Model for trending tokens API responses."""

    success: bool
    data: ElfaTrendingTokensData

    @property
    def formatted_response(self) -> str:
        """Format trending tokens data into a readable markdown string."""
        if not self.success:
            return "Failed to get trending tokens."

        if not self.data.data:
            return "No trending tokens found."

        formatted = "# Trending Tokens\n\n"

        for token in self.data.data:
            formatted += f"## ${token.token}\n\n"
            formatted += f"Current Mentions: {token.current_count:,}\n"
            formatted += f"Previous Period: {token.previous_count:,}\n"

            emoji = "📈" if token.change_percent > 0 else "📉" if token.change_percent < 0 else "➡️"
            formatted += f"Change: {emoji} {token.change_percent:+.2f}%\n\n"
            formatted += "---\n\n"

        return formatted


class ElfaAccountSmartStats(BaseModel):
    """Model representing account smart statistics."""

    followerEngagementRatio: float
    averageEngagement: float
    smartFollowingCount: int


class ElfaAccountSmartStatsResponse(BaseModel):
    """Model for account smart stats API responses."""

    success: bool
    data: ElfaAccountSmartStats

    @property
    def formatted_response(self) -> str:
        """Format account smart stats into a readable markdown string."""
        if not self.success:
            return "Failed to get account statistics."

        formatted = "# Account Smart Statistics\n\n"

        formatted += "## Engagement Metrics\n\n"
        formatted += f"Smart Following Count: {self.data.smartFollowingCount:,}\n"
        formatted += f"Average Engagement: {self.data.averageEngagement:.2f}\n"
        formatted += f"Follower Engagement Ratio: {self.data.followerEngagementRatio:.2%}\n"

        return formatted

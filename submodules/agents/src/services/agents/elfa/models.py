from typing import List, Optional

from pydantic import BaseModel


class ElfaAccountData(BaseModel):
    """Model representing account profile data."""

    profileBannerUrl: Optional[str] = None
    profileImageUrl: Optional[str] = None
    description: Optional[str] = None
    userSince: Optional[str] = None
    location: Optional[str] = None
    name: Optional[str] = None


class ElfaAccount(BaseModel):
    """Model representing a social media account."""

    id: Optional[int] = None
    username: Optional[str] = None
    data: Optional[ElfaAccountData] = None
    followerCount: Optional[int] = None
    followingCount: Optional[int] = None
    isVerified: Optional[bool] = None


class MediaUrl(BaseModel):
    """Model representing a media URL."""

    url: Optional[str] = None
    type: Optional[str] = None


class MentionData(BaseModel):
    """Model representing mention data."""

    mediaUrls: Optional[List[MediaUrl]] = []


class ElfaMention(BaseModel):
    """Model representing a social media mention."""

    id: Optional[int] = None
    type: Optional[str] = None
    content: Optional[str] = None
    originalUrl: Optional[str] = None
    data: Optional[MentionData] = None
    likeCount: Optional[int] = None
    quoteCount: Optional[int] = None
    replyCount: Optional[int] = None
    repostCount: Optional[int] = None
    viewCount: Optional[int] = None
    mentionedAt: Optional[str] = None
    bookmarkCount: Optional[int] = None
    account: Optional[ElfaAccount] = None


class ElfaMentionsResponse(BaseModel):
    """Model for mentions API responses."""

    success: Optional[bool] = None
    data: Optional[List[ElfaMention]] = None

    @property
    def formatted_response(self) -> str:
        """Format mentions data into a readable markdown string."""
        if not self.success:
            return "Failed to get mentions."

        if not self.data:
            return "No mentions found."

        mentions = self.data[:5]  # Limit to 5 mentions
        formatted = f"# Latest {len(mentions)} Social Media Mentions\n\n"

        for mention in mentions:
            if mention.account and mention.account.username:
                formatted += f"## @{mention.account.username}\n\n"
            else:
                formatted += "## Unknown User\n\n"

            if mention.content:
                formatted += f"{mention.content}\n\n"

            formatted += "**Metrics**:\n"
            formatted += f"- 👁️ Views: {mention.viewCount or 0:,}\n"
            formatted += f"- 🔄 Reposts: {mention.repostCount or 0:,}\n"
            formatted += f"- 💬 Replies: {mention.replyCount or 0:,}\n"
            formatted += f"- ❤️ Likes: {mention.likeCount or 0:,}\n\n"

            if mention.mentionedAt:
                formatted += f"Posted at: {mention.mentionedAt}\n\n"

            if mention.originalUrl:
                formatted += f"[View Original]({mention.originalUrl})\n\n"

            formatted += "---\n\n"

        return formatted


class ElfaMentionMetrics(BaseModel):
    """Model representing engagement metrics for a mention."""

    view_count: Optional[int] = None
    repost_count: Optional[int] = None
    reply_count: Optional[int] = None
    like_count: Optional[int] = None


class ElfaTopMention(BaseModel):
    """Model representing a top mention."""

    id: Optional[int] = None
    content: Optional[str] = None
    mentioned_at: Optional[str] = None
    metrics: Optional[ElfaMentionMetrics] = None


class ElfaTopMentionsData(BaseModel):
    """Model representing paginated top mentions data."""

    pageSize: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[ElfaTopMention]] = None


class ElfaTopMentionsResponse(BaseModel):
    """Model for top mentions API responses."""

    success: Optional[bool] = None
    data: Optional[ElfaTopMentionsData] = None

    @property
    def formatted_response(self) -> str:
        """Format top mentions data into a readable markdown string."""
        if not self.success:
            return "Failed to get top mentions."

        if not self.data or not self.data.data:
            return "No top mentions found for this ticker."

        mentions = self.data.data[:5]  # Limit to 5 top mentions
        formatted = f"# Top {len(mentions)} Mentions (Total: {self.data.total or 0})\n\n"

        for mention in mentions:
            if mention.id:
                formatted += f"### Post ID: {mention.id}\n\n"
            else:
                formatted += "### Unknown Post\n\n"

            if mention.content:
                formatted += f"{mention.content}\n\n"

            formatted += "**Engagement**:\n"
            if mention.metrics:
                formatted += f"- 👁️ Views: {mention.metrics.view_count or 0:,}\n"
                formatted += f"- 🔄 Reposts: {mention.metrics.repost_count or 0:,}\n"
                formatted += f"- 💬 Replies: {mention.metrics.reply_count or 0:,}\n"
                formatted += f"- ❤️ Likes: {mention.metrics.like_count or 0:,}\n\n"
            else:
                formatted += "No metrics available\n\n"

            if mention.mentioned_at:
                formatted += f"Posted at: {mention.mentioned_at}\n\n"

            formatted += "---\n\n"

        return formatted


class ElfaTrendingToken(BaseModel):
    """Model representing a trending token."""

    change_percent: Optional[float] = None
    previous_count: Optional[int] = None
    current_count: Optional[int] = None
    token: Optional[str] = None


class ElfaTrendingTokensData(BaseModel):
    """Model representing paginated trending tokens data."""

    pageSize: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[ElfaTrendingToken]] = None


class ElfaTrendingTokensResponse(BaseModel):
    """Model for trending tokens API responses."""

    success: Optional[bool] = None
    data: Optional[ElfaTrendingTokensData] = None

    @property
    def formatted_response(self) -> str:
        """Format trending tokens data into a readable markdown string."""
        if not self.success:
            return "Failed to get trending tokens."

        if not self.data or not self.data.data:
            return "No trending tokens found."

        tokens = self.data.data[:5]  # Limit to 5 trending tokens
        formatted = f"# Top {len(tokens)} Trending Tokens\n\n"

        for token in tokens:
            if token.token:
                formatted += f"## ${token.token}\n\n"
            else:
                formatted += "## Unknown Token\n\n"

            formatted += f"Current Mentions: {token.current_count or 0:,}\n"
            formatted += f"Previous Period: {token.previous_count or 0:,}\n"

            if token.change_percent is not None:
                emoji = "📈" if token.change_percent > 0 else "📉" if token.change_percent < 0 else "➡️"
                formatted += f"Change: {emoji} {token.change_percent:+.2f}%\n\n"
            else:
                formatted += "Change: Not available\n\n"

            formatted += "---\n\n"

        return formatted


class ElfaAccountSmartStats(BaseModel):
    """Model representing account smart statistics."""

    followerEngagementRatio: Optional[float] = None
    averageEngagement: Optional[float] = None
    smartFollowingCount: Optional[int] = None


class ElfaAccountSmartStatsResponse(BaseModel):
    """Model for account smart stats API responses."""

    success: Optional[bool] = None
    data: Optional[ElfaAccountSmartStats] = None

    @property
    def formatted_response(self) -> str:
        """Format account smart stats into a readable markdown string."""
        if not self.success:
            return "Failed to get account statistics."

        if not self.data:
            return "No account statistics available."

        formatted = "# Account Smart Statistics\n\n"
        formatted += "## Engagement Metrics\n\n"
        formatted += f"Smart Following Count: {self.data.smartFollowingCount or 0:,}\n"
        formatted += f"Average Engagement: {self.data.averageEngagement or 0:.2f}\n"

        if self.data.followerEngagementRatio is not None:
            formatted += f"Follower Engagement Ratio: {self.data.followerEngagementRatio:.2%}\n"
        else:
            formatted += "Follower Engagement Ratio: Not available\n"

        return formatted

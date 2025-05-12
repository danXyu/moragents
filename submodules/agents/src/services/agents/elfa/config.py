from langchain.schema import SystemMessage

from models.service.agent_config import AgentConfig

from .tool_types import ElfaToolType


class Config:
    """Configuration for Elfa Social API."""

    # *************
    # AGENT CONFIG
    # ------------
    # This must be defined in every agent config file
    # It is required to load the agent
    # *************

    agent_config = AgentConfig(
        path="services.agents.elfa.agent",
        class_name="ElfaAgent",
        description="Fetches and analyzes social media data related to cryptocurrency from Elfa.",
        delegator_description="Monitors and analyzes social sentiment and engagement metrics across crypto communities, "
        "including trending topics, influential accounts, sentiment shifts, and community growth patterns. "
        "Use when users want insights about social perception of crypto projects.",
        human_readable_name="Elfa Social Analyst",
        command="elfa",
        upload_required=False,
    )

    # *************
    # SYSTEM MESSAGE
    # *************

    system_message = SystemMessage(
        content=(
            "You are an agent that can fetch and analyze social media data "
            "from Elfa. You can get trending tokens, mentions, and smart account "
            "statistics. The data is focused on cryptocurrency and blockchain "
            "related social media activity."
        )
    )

    # *************

    tools = [
        {
            "name": ElfaToolType.GET_TOP_MENTIONS.value,
            "description": "Get the most viewed and engaged-with social media posts mentioning a specific cryptocurrency ticker symbol, sorted by total view count",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The ticker symbol to get mentions for",
                        "required": True,
                    },
                    "timeWindow": {
                        "type": "string",
                        "description": "Time window for mentions (e.g., '1h', '24h', '7d')",
                        "required": False,
                    },
                    "includeAccountDetails": {
                        "type": "boolean",
                        "description": "Include account details in response",
                        "required": False,
                    },
                },
            },
        },
        {
            "name": ElfaToolType.SEARCH_MENTIONS.value,
            "description": "Search through all social media posts using custom keywords and date filters to find relevant cryptocurrency discussions and trends",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to search for (max 5). Defaults to ['crypto']",
                        "required": False,
                    },
                    "from": {
                        "type": "number",
                        "description": "Start timestamp (unix). Defaults to 7 days ago",
                        "required": False,
                    },
                    "to": {
                        "type": "number",
                        "description": "End timestamp (unix). Defaults to now",
                        "required": False,
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of results to return (default: 20, max: 30)",
                        "required": False,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Cursor for pagination",
                        "required": False,
                    },
                },
            },
        },
        {
            "name": ElfaToolType.GET_TRENDING_TOKENS.value,
            "description": "Get trending tokens based on social media mentions",
            "parameters": {
                "type": "object",
                "properties": {
                    "timeWindow": {
                        "type": "string",
                        "description": "Time window for trending analysis (default: '24h')",
                        "required": False,
                    },
                    "minMentions": {
                        "type": "number",
                        "description": "Minimum number of mentions required (default: 5)",
                        "required": False,
                    },
                },
            },
        },
        {
            "name": ElfaToolType.GET_ACCOUNT_SMART_STATS.value,
            "description": "Get smart stats and social metrics for a given username",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username to get stats for",
                        "required": True,
                    },
                },
            },
        },
    ]

    # *************
    # API CONFIG
    # *************

    BASE_URL = "https://api.elfa.ai"
    API_VERSION = "v1"
    RATE_LIMIT = 60  # requests per minute

    # Headers configuration
    API_KEY_HEADER = "x-elfa-api-key"  # Updated header name for API key

    ENDPOINTS = {
        ElfaToolType.GET_TOP_MENTIONS.value: f"/{API_VERSION}/top-mentions",
        ElfaToolType.SEARCH_MENTIONS.value: f"/{API_VERSION}/mentions/search",
        ElfaToolType.GET_TRENDING_TOKENS.value: f"/{API_VERSION}/trending-tokens",
        ElfaToolType.GET_ACCOUNT_SMART_STATS.value: f"/{API_VERSION}/account/smart-stats",
    }

from langchain.schema import SystemMessage

from models.service.agent_config import AgentConfig
from .tool_types import CodexToolType


class Config:
    """Configuration for Codex.io API."""

    # *************
    # AGENT CONFIG
    # ------------
    # This must be defined in every agent config file
    # It is required to load the agent
    # *************

    agent_config = AgentConfig(
        path="src.services.agents.codex.agent",
        class_name="CodexAgent",
        description="Fetches and analyzes advanced token and NFT data from Codex.io such as trending tokens, top holders, and more",
        delegator_description="Retrieves and analyzes advanced on-chain metrics and token data from Codex.io, including holder behavior patterns, whale movements, token distribution analytics, and contract interactions. Use for sophisticated blockchain data analysis beyond basic price information.",
        human_readable_name="Codex Market Analyst",
        command="codex",
        upload_required=False,
    )

    # **************
    # SYSTEM MESSAGE
    # **************

    system_message = SystemMessage(
        content=(
            "You are an agent that can fetch and analyze token and NFT data "
            "from Codex.io. You can get trending tokens, analyze token holder "
            "concentration, and search for NFT collections."
        )
    )

    # *************
    # TOOLS CONFIG
    # *************

    tools = [
        {
            "name": CodexToolType.LIST_TOP_TOKENS.value,
            "description": "Get a list of trending tokens across specified networks",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tokens to return (max 50)",
                        "required": False,
                    },
                    "networkFilter": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of network IDs to filter by",
                        "required": False,
                    },
                    "resolution": {
                        "type": "string",
                        "description": "Time frame for trending results (1, 5, 15, 30, 60, 240, 720, or 1D)",
                        "required": False,
                    },
                },
            },
        },
        {
            "name": CodexToolType.GET_TOP_HOLDERS_PERCENT.value,
            "description": "Get the top holders for a token",
            "parameters": {
                "type": "object",
                "properties": {
                    "tokenId": {
                        "type": "string",
                        "description": "Token ID",
                        "required": True,
                    },
                },
            },
        },
        {
            "name": CodexToolType.SEARCH_NFTS.value,
            "description": "Search for NFT collections by name or address",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Query string to search for",
                        "required": True,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "required": False,
                    },
                    "networkFilter": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of network IDs to filter by",
                        "required": False,
                    },
                    "filterWashTrading": {
                        "type": "boolean",
                        "description": "Whether to filter collections linked to wash trading",
                        "required": False,
                    },
                    "window": {
                        "type": "string",
                        "description": "Time frame for stats (1h, 4h, 12h, or 1d)",
                        "required": False,
                    },
                },
            },
        },
    ]

    # *************
    # API CONFIG
    # *************

    GRAPHQL_URL = "https://graph.codex.io/graphql"

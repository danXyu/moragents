from models.service.agent_config import AgentConfig


class Config:
    """Configuration for MCP Hacker News Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.mcp_agent.agent",
        class_name="MCPAgent",
        description="Provides access to Hacker News API for fetching stories, comments, user information, and searching content.",
        delegator_description=(
            "A specialized agent that retrieves information from Hacker News. "
            "This agent excels at fetching top stories, new stories, Ask HN, Show HN posts, story comments, "
            "searching for specific content, and retrieving user information. "
            "Use this agent when you need to find trending tech discussions, developer opinions, "
            "or specific information shared on Hacker News. The agent can get the latest stories, "
            "search for relevant discussions, and provide insights from this tech-focused community."
        ),
        human_readable_name="Hacker News",
        command="hackernews",
        upload_required=False,
        is_enabled=True,
        mcp_server_url="https://mcp-server-34a4e8c0-97ee-43c5-9c59-6468d4972012.supermachine.app",
        name="hacker_news",
        # Note: The actual tools will be fetched at runtime from the MCP server
        # using the MultiServerMCPClient in the agent_manager.py
        # The tools below are placeholders and will be replaced with actual tools
        # fetched from the MCP server when the agent is initialized
        tools=[],
    )

from models.service.agent_config import AgentConfig


class Config:
    """Configuration for MCP Reddit Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.mcp_agent.agent",
        class_name="MCPAgent",
        description="Provides access to Reddit API for searching and retrieving content from Reddit communities and discussions.",
        delegator_description=(
            "A specialized agent that searches and retrieves information from Reddit. "
            "This agent excels at finding discussions, opinions, and community knowledge across Reddit's diverse communities. "
            "Use this agent when you need to find specific Reddit posts, comments, or understand what different communities "
            "are saying about a particular topic. The agent can search subreddits, find trending discussions, "
            "and retrieve valuable insights from this social platform."
        ),
        human_readable_name="Reddit Search",
        command="reddit",
        upload_required=False,
        is_enabled=True,
        mcp_server_url="https://mcp-server-ef4f15ca-7bef-435b-a9c7-ed6d2beab0bb.supermachine.app",
        name="reddit_search",
        # Note: The actual tools will be fetched at runtime from the MCP server
        # using the MultiServerMCPClient in the agent_manager.py
        # The tools below are placeholders and will be replaced with actual tools
        # fetched from the MCP server when the agent is initialized
        tools=[],
    )

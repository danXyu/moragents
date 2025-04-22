from models.service.agent_config import AgentConfig


class Config:
    """Configuration for MCP Brave Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.mcp_agent.agent",
        class_name="MCPAgent",
        description="Provides access to Brave Search API for comprehensive web search capabilities with enhanced privacy features.",
        delegator_description=(
            "A specialized search agent that uses Brave Search API to find information on the web. "
            "This agent excels at retrieving current information, news, and factual data from across the internet "
            "while respecting user privacy. Use this agent when you need to search for specific information, "
            "current events, or when you need to verify facts from reliable web sources. "
            "The agent provides comprehensive search results with better privacy protections than traditional search engines."
        ),
        human_readable_name="Brave Search",
        command="brave",
        upload_required=False,
        is_enabled=True,
        mcp_server_url="https://mcp-server-2954d583-ada5-4069-9b2a-9388bd220868.supermachine.app",
        name="brave_search",
        # Note: The actual tools will be fetched at runtime from the MCP server
        # using the MultiServerMCPClient in the agent_manager.py
        # The tools below are placeholders and will be replaced with actual tools
        # fetched from the MCP server when the agent is initialized
        tools=[],
    )

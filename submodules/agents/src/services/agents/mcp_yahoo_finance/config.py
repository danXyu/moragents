from models.service.agent_config import AgentConfig


class Config:
    """Configuration for MCP Yahoo Finance Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.mcp_agent.agent",
        class_name="MCPAgent",
        description="Provides access to Yahoo Finance API for fetching stock data, news, and other financial information.",
        delegator_description=(
            "A specialized agent that retrieves financial information from Yahoo Finance. "
            "This agent excels at fetching stock data, company information, financial metrics, news articles, "
            "and performing searches for financial entities. Use this agent when you need to analyze stocks, "
            "get company financials, find recent news about specific symbols, or discover top performing companies "
            "in various sectors. The agent provides comprehensive financial data through Yahoo Finance's extensive database."
        ),
        human_readable_name="Yahoo Finance",
        command="yahoo-finance",
        upload_required=False,
        is_enabled=True,
        mcp_server_url="https://mcp-server-3b6b2717-9a04-4051-8ce0-3ce5ad787fd0.supermachine.app",
        name="yahoo_finance",
        # Note: The actual tools will be fetched at runtime from the MCP server
        # using the MultiServerMCPClient in the agent_manager.py
        # The tools below are placeholders and will be replaced with actual tools
        # fetched from the MCP server when the agent is initialized
        tools=[],
    )

from models.service.agent_config import AgentConfig


class Config:
    """Configuration for MCP Puppeteer Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.mcp_agent.agent",
        class_name="MCPAgent",
        description="Provides browser automation capabilities using Puppeteer for web navigation, screenshots, and JavaScript execution.",
        delegator_description=(
            "A specialized web automation agent that uses Puppeteer to interact with websites. "
            "This agent excels at navigating web pages, taking screenshots, clicking elements, filling forms, "
            "and executing JavaScript in a real browser environment. Use this agent when you need to "
            "automate browser interactions, capture visual information from websites, or perform complex "
            "web-based tasks that require a full browser environment. The agent provides comprehensive "
            "browser automation capabilities through Puppeteer's navigation, interaction, and evaluation tools."
        ),
        human_readable_name="Puppeteer",
        command="puppeteer",
        upload_required=False,
        is_enabled=True,
        mcp_server_url="https://mcp-server-49110872-8cfd-41a6-aa0d-aa5a32128570.supermachine.app",
        name="puppeteer",
        # Note: The actual tools will be fetched at runtime from the MCP server
        # using the MultiServerMCPClient in the agent_manager.py
        # The tools below are placeholders and will be replaced with actual tools
        # fetched from the MCP server when the agent is initialized
        tools=[],
    )

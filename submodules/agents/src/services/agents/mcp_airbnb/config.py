from models.service.agent_config import AgentConfig


class Config:
    """Configuration for MCP Airbnb Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.mcp_agent.agent",
        class_name="MCPAgent",
        description="Provides access to Airbnb listings for searching and retrieving detailed information about accommodations.",
        delegator_description=(
            "A specialized agent that searches and retrieves information from Airbnb. "
            "This agent excels at finding accommodations, getting listing details, and exploring "
            "vacation rental options across different locations. Use this agent when you need to "
            "search for places to stay, get detailed information about specific listings including "
            "amenities, pricing, availability, and host details. The agent can search by location, "
            "dates, number of guests, and price range to find suitable Airbnb options."
        ),
        human_readable_name="Airbnb",
        command="airbnb",
        upload_required=False,
        is_enabled=True,
        mcp_server_url="https://mcp-server-3d6eee47-9908-49ee-a9c5-370aeb2c6e81.supermachine.app",
        name="airbnb",
        # Note: The actual tools will be fetched at runtime from the MCP server
        # using the MultiServerMCPClient in the agent_manager.py
        # The tools below are placeholders and will be replaced with actual tools
        # fetched from the MCP server when the agent is initialized
        tools=[],
    )

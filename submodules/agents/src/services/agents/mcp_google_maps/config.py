from models.service.agent_config import AgentConfig


class Config:
    """Configuration for MCP Google Maps Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.mcp_agent.agent",
        class_name="MCPAgent",
        description="Provides access to Google Maps API for geocoding, place search, directions, and other location-based services.",
        delegator_description=(
            "A specialized agent that provides access to Google Maps services. "
            "This agent excels at geocoding addresses to coordinates, finding places, getting directions, "
            "calculating distances between locations, and retrieving detailed place information. "
            "Use this agent when you need to work with location data, find places of interest, "
            "get travel directions, or analyze geographic information. The agent supports various "
            "mapping functions including address lookup, place search, route planning, and elevation data."
        ),
        human_readable_name="Google Maps",
        command="google-maps",
        upload_required=False,
        is_enabled=True,
        mcp_server_url="https://mcp-server-d596c301-7d7e-4796-9cdb-5f64fa16c436.supermachine.app",
        name="google_maps",
        # Note: The actual tools will be fetched at runtime from the MCP server
        # using the MultiServerMCPClient in the agent_manager.py
        # The tools below are placeholders and will be replaced with actual tools
        # fetched from the MCP server when the agent is initialized
        tools=[],
    )

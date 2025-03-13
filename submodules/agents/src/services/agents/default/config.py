from models.service.agent_config import AgentConfig


class Config:
    """Configuration for Default Agent."""

    # *************
    # AGENT CONFIG
    # ------------
    # This must be defined in every agent config file
    # It is required to load the agent
    # *************

    agent_config = AgentConfig(
        path="services.agents.default.agent",
        class_name="DefaultAgent",
        description="Ask about active Morpheus agents, and also handles general questions",
        delegator_description="Handles meta-queries about Morpheus itself, available agents, system capabilities, and "
        "general cryptocurrency questions that don't require specialized agents. Use when no other agent is clearly "
        "applicable or for simple informational requests.",
        human_readable_name="Morpheus Default",
        command="morpheus",
        upload_required=False,
    )

    # *************
    # TOOLS CONFIG
    # *************

    tools = [
        {
            "name": "get_available_agents",
            "description": "Get list of all available agents and their descriptions",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "get_agent_info",
            "description": "Get detailed information about a specific agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent to get info for",
                        "required": True,
                    }
                },
            },
        },
    ]

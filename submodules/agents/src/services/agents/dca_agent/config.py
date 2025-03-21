from models.service.agent_config import AgentConfig


class Config:
    """Configuration for DCA (Dollar Cost Averaging) Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.dca_agent.agent",
        class_name="DCAAgent",
        description="Handles automated dollar cost averaging transactions. Use when the user wants to set up recurring purchases of crypto assets.",
        delegator_description="Manages dollar-cost averaging setup and execution, including schedule creation, "
        "asset allocation adjustment, and transaction automation across multiple networks. Use when users mention "
        "recurring purchases, DCA strategies, or automated investment approaches.",
        human_readable_name="DCA Transaction Manager",
        command="dca",
        upload_required=False,
    )

    # *************
    # TOOLS CONFIG
    # *************

    tools = [
        {
            "name": "setup_dca",
            "description": "Set up a new DCA schedule for recurring asset purchases",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "string", "description": "Amount to invest per interval"},
                    "asset_id": {"type": "string", "description": "Asset ID to purchase"},
                    "interval": {
                        "type": "string",
                        "description": "Time interval between purchases (daily/weekly/monthly)",
                    },
                },
                "required": ["amount", "asset_id", "interval"],
            },
        },
        {
            "name": "get_dca_schedule",
            "description": "Get current DCA schedule details",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "cancel_dca",
            "description": "Cancel an existing DCA schedule",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string", "description": "ID of the DCA schedule to cancel"},
                },
                "required": ["schedule_id"],
            },
        },
    ]

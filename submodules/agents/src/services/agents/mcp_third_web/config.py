from models.service.agent_config import AgentConfig


class Config:
    """Configuration for MCP ThirdWeb Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.mcp_agent.agent",
        class_name="MCPAgent",
        description="Provides access to thirdweb's suite of blockchain tools and services for smart contract interactions, on-chain analysis, and decentralized storage.",
        delegator_description=(
            "A specialized blockchain agent that uses thirdweb's services to interact with blockchain networks. "
            "This agent excels at smart contract analysis, on-chain data queries, contract deployments, and IPFS storage operations. "
            "Use this agent when you need to analyze blockchain data, deploy or interact with smart contracts, "
            "or store data on IPFS. The agent provides comprehensive blockchain capabilities through thirdweb's "
            "Nebula (autonomous onchain execution), Insight (blockchain data analysis), Engine (contract deployments), "
            "and Storage (decentralized IPFS storage) services."
        ),
        human_readable_name="ThirdWeb",
        command="thirdweb",
        upload_required=False,
        is_enabled=True,
        mcp_server_url="https://mcp-server-a0c4ee2a-343f-4ef6-840e-5f4caea54c1f.supermachine.app",
        name="third_web",
        # Note: The actual tools will be fetched at runtime from the MCP server
        # using the MultiServerMCPClient in the agent_manager.py
        # The tools below are placeholders and will be replaced with actual tools
        # fetched from the MCP server when the agent is initialized
        tools=[],
    )

from models.service.agent_config import AgentConfig
from services.agents.base_agent.tool_types import BaseAgentToolType


class Config:
    """Configuration for Base Network Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.base_agent.agent",
        class_name="BaseAgent",
        description="Interact with the Base network and developer-managed wallets",
        delegator_description=(
            "Specializes in transactions and interactions specifically on the Base network via developer-managed wallets."
            "Use ONLY when users explicitly reference Base, base network, or Coinbase."
        ),
        human_readable_name="Base Transaction Manager",
        command="base",
        upload_required=False,
    )

    # *************
    # TOOLS CONFIG
    # *************

    tools = [
        {
            "name": BaseAgentToolType.SWAP_ASSETS.value,
            "description": "Swap one asset for another (Base Mainnet only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "string", "description": "Amount to swap"},
                    "from_asset_id": {
                        "type": "string",
                        "description": "Asset ID to swap from",
                    },
                    "to_asset_id": {
                        "type": "string",
                        "description": "Asset ID to swap to",
                    },
                },
                "required": ["amount", "from_asset_id", "to_asset_id"],
            },
        },
        {
            "name": BaseAgentToolType.TRANSFER_ASSET.value,
            "description": "Transfer an asset to another address",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "string", "description": "Amount to transfer"},
                    "asset_id": {
                        "type": "string",
                        "description": "Asset ID to transfer",
                    },
                },
                "required": ["amount", "asset_id"],
            },
        },
        {
            "name": BaseAgentToolType.GET_BALANCE.value,
            "description": "Get balance of a specific asset",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_id": {
                        "type": "string",
                        "description": "Asset ID to check balance for",
                    }
                },
                "required": ["asset_id"],
            },
        },
        # TODO: Add more base tools / functionality
        # {
        #     "name": BaseAgentToolType.CREATE_TOKEN.value,
        #     "description": "Create a new ERC-20 token",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "name": {"type": "string", "description": "Name of the token"},
        #             "symbol": {"type": "string", "description": "Symbol of the token"},
        #             "initial_supply": {
        #                 "type": "integer",
        #                 "description": "Initial supply of tokens",
        #             },
        #         },
        #         "required": ["name", "symbol", "initial_supply"],
        #     },
        # },
        # {
        #     "name": BaseAgentToolType.REQUEST_ETH_FROM_FAUCET.value,
        #     "description": "Request ETH from testnet faucet",
        #     "parameters": {"type": "object", "properties": {}},
        # },
        # {
        #     "name": BaseAgentToolType.MINT_NFT.value,
        #     "description": "Mint an NFT to an address",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "contract_address": {"type": "string", "description": "NFT contract address"},
        #             "mint_to": {"type": "string", "description": "Address to mint NFT to"},
        #         },
        #         "required": ["contract_address", "mint_to"],
        #     },
        # },
        # {
        #     "name": BaseAgentToolType.REGISTER_BASENAME.value,
        #     "description": "Register a basename for the agent's wallet",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "basename": {"type": "string", "description": "Basename to register"},
        #             "amount": {
        #                 "type": "number",
        #                 "description": "Amount of ETH to pay for registration",
        #                 "default": 0.002,
        #             },
        #         },
        #         "required": ["basename"],
        #     },
        # },
    ]

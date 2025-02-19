from src.models.service.agent_config import AgentConfig


class Config:
    """Configuration for Crypto Data Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="src.services.agents.crypto_data.agent",
        class_name="CryptoDataAgent",
        description="Fetches basic cryptocurrency data such as price, market cap, TVL, and FDV from various sources.",
        human_readable_name="Crypto Data Analyst",
        command="cryptodata",
        upload_required=False,
    )

    # *************
    # TOOLS CONFIG
    # *************
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_price",
                "description": "Get the price of a cryptocurrency",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin_name": {
                            "type": "string",
                            "description": "The name of the coin.",
                        }
                    },
                    "required": ["coin_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_floor_price",
                "description": "Get the floor price of an NFT",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nft_name": {
                            "type": "string",
                            "description": "Name of the NFT",
                        }
                    },
                    "required": ["nft_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_tvl",
                "description": "Get the TVL (Total Value Locked) of a protocol.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "protocol_name": {
                            "type": "string",
                            "description": "Name of the protocol",
                        }
                    },
                    "required": ["protocol_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_fdv",
                "description": "Get the fdv or fully diluted valuation of a coin",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin_name": {
                            "type": "string",
                            "description": "Name of the coin",
                        }
                    },
                    "required": ["coin_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_market_cap",
                "description": "Get the mc or market cap of a coin",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin_name": {
                            "type": "string",
                            "description": "Name of the coin",
                        }
                    },
                    "required": ["coin_name"],
                },
            },
        },
    ]

    # *************
    # API CONFIG
    # *************

    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    DEFILLAMA_BASE_URL = "https://api.llama.fi"

    # Response messages
    PRICE_SUCCESS_MESSAGE = "The price of {coin_name} is ${price:,}"
    PRICE_FAILURE_MESSAGE = "Failed to retrieve price. Please enter a valid coin name."
    FLOOR_PRICE_SUCCESS_MESSAGE = "The floor price of {nft_name} is ${floor_price:,}"
    FLOOR_PRICE_FAILURE_MESSAGE = "Failed to retrieve floor price. Please enter a valid NFT name."
    TVL_SUCCESS_MESSAGE = "The TVL of {protocol_name} is ${tvl:,}"
    TVL_FAILURE_MESSAGE = "Failed to retrieve TVL. Please enter a valid protocol name."
    FDV_SUCCESS_MESSAGE = "The fully diluted valuation of {coin_name} is ${fdv:,}"
    FDV_FAILURE_MESSAGE = "Failed to retrieve FDV. Please enter a valid coin name."
    MARKET_CAP_SUCCESS_MESSAGE = "The market cap of {coin_name} is ${market_cap:,}"
    MARKET_CAP_FAILURE_MESSAGE = "Failed to retrieve market cap. Please enter a valid coin name."
    API_ERROR_MESSAGE = "I can't seem to access the API at the moment."

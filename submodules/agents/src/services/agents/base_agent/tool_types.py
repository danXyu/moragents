from enum import Enum


class BaseAgentToolType(Enum):
    """Enum for different Base blockchain transaction tool types"""

    SWAP_ASSETS = "swap_assets"
    TRANSFER_ASSET = "transfer_asset"
    GET_BALANCE = "get_balance"
    CREATE_TOKEN = "create_token"
    REQUEST_ETH_FROM_FAUCET = "request_eth_from_faucet"
    MINT_NFT = "mint_nft"
    REGISTER_BASENAME = "register_basename"

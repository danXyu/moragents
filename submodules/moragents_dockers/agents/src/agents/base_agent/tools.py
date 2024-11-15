import logging
import time
<<<<<<< HEAD:submodules/moragents_dockers/agents/src/agents/base_agent/tools.py

import requests
from cdp import Cdp, Transaction, Wallet
from src.agents.base_agent.config import Config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class InsufficientFundsError(Exception):
    pass


def send_gasless_usdc_transaction(toAddress, amount):

    client = Cdp.configure("", "")
=======
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from cdp import Cdp, Wallet, Transaction
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Custom exceptions
class ToolError(Exception):
    """Base exception for tool operations"""
    pass

class InsufficientFundsError(ToolError):
    """Raised when there are insufficient funds"""
    pass
>>>>>>> domsteil/main:submodules/moragents_dockers/agents/src/base_agent/src/tools.py

class ConfigurationError(ToolError):
    """Raised when there are configuration issues"""
    pass

# Global CDP client management
_client: Optional[Cdp] = None
_client_lock = threading.Lock()

def get_cdp_client() -> Cdp:
    """Get or create CDP client singleton with thread safety"""
    global _client
    with _client_lock:
        if not _client:
            # Get credentials from Flask config
            api_key = current_app.config.get("cdpApiKey")
            api_secret = current_app.config.get("cdpApiSecret")
            
            if not api_key or not api_secret:
                raise ConfigurationError("CDP credentials not found in config")
            
            try:
                _client = Cdp.configure(
                    api_key,
                    api_secret
                )
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize CDP client: {str(e)}")
        
        return _client

<<<<<<< HEAD:submodules/moragents_dockers/agents/src/agents/base_agent/tools.py
    eth_faucet_tx = wallet1.faucet()

    usdc_faucet_tx = wallet1.faucet(asset_id="usdc")
=======
def reset_cdp_client() -> None:
    """Reset the CDP client (useful when credentials change)"""
    global _client
    with _client_lock:
        _client = None
>>>>>>> domsteil/main:submodules/moragents_dockers/agents/src/base_agent/src/tools.py

async def create_wallet() -> Wallet:
    """Create and fund a new wallet"""
    try:
        wallet = Wallet.create()
        logger.info(f"Wallet created: {wallet.default_address}")
        return wallet
    except Exception as e:
        raise ToolError(f"Failed to create wallet: {str(e)}")

async def fund_wallet(wallet: Wallet, asset_id: Optional[str] = None) -> Transaction:
    """Fund wallet from faucet"""
    try:
        if asset_id:
            tx = wallet.faucet(asset_id=asset_id)
        else:
            tx = wallet.faucet()
        logger.info(f"Faucet transaction sent for {asset_id or 'ETH'}")
        time.sleep(2)  # Wait for faucet
        return tx
    except Exception as e:
        raise InsufficientFundsError(f"Failed to fund wallet: {str(e)}")

async def send_gasless_usdc_transaction(
    toAddress: str,
    amount: str
) -> Tuple[Dict[str, Any], str]:
    """Send a gasless USDC transaction"""
    try:
        # Ensure client is configured
        client = get_cdp_client()
        logger.info("CDP client configured")

        # Create and fund wallet
        wallet = await create_wallet()
        
        # Get ETH and USDC from faucet
        await fund_wallet(wallet)  # ETH for gas
        await fund_wallet(wallet, "usdc")  # USDC for transfer
        
        # Execute transfer
        tx = wallet.default_address.transfer(
            amount=amount,
            token="usdc",
            to_address=toAddress,
            gasless=True
        ).wait()
        
        logger.info(f"USDC Transfer completed: {tx.hash}")
        
        return {
            'success': True,
            'tx_hash': tx.hash,
            'from': wallet.default_address,
            'to': toAddress,
            'amount': amount,
            'token': 'USDC',
            'timestamp': datetime.now().isoformat()
        }, "gasless_usdc_transfer"

    except InsufficientFundsError as e:
        raise
    except Exception as e:
        logger.error(f"Error in gasless USDC transfer: {str(e)}")
        raise ToolError(f"Failed to send USDC: {str(e)}")

async def send_eth_transaction(
    toAddress: str,
    amount: str
) -> Tuple[Dict[str, Any], str]:
    """Send an ETH transaction"""
    try:
        # Ensure client is configured
        client = get_cdp_client()
        logger.info("CDP client configured")

        # Create and fund wallet
        wallet = await create_wallet()
        await fund_wallet(wallet)  # Get ETH from faucet
        
        # Execute transfer
        tx = wallet.transfer(
            amount=amount,
            token="eth",
            to_address=toAddress
        ).wait()
        
        logger.info(f"ETH Transfer completed: {tx.hash}")
        
        return {
            'success': True,
            'tx_hash': tx.hash,
            'from': wallet.default_address,
            'to': toAddress,
            'amount': amount,
            'token': 'ETH',
            'timestamp': datetime.now().isoformat()
        }, "eth_transfer"

<<<<<<< HEAD:submodules/moragents_dockers/agents/src/agents/base_agent/tools.py
    return {"success": "Transfer transaction successful"}, "gasless_usdc_transfer"


def send_eth_transaction(toAddress, amount):

    client = Cdp.configure("", "")

    logger.info(f"Client successfully configured: {client}")

    wallet1 = Wallet.create()

    logger.info(f"Wallet successfully created: {wallet1}")
    logger.info(f"Wallet address: {wallet1.default_address}")

    faucet_tx = wallet1.faucet()

    logger.info(f"Faucet transaction successfully sent: {faucet_tx}")

    logger.info(f"Faucet transaction successfully completed: {faucet_tx}")

    address = wallet1.default_address

    logger.info(f"Address: {address}")

    time.sleep(2)

    transfer = wallet1.transfer(amount, "eth", toAddress).wait()

    logger.info(f"Transfer transaction: {transfer}")

    return {"success": "Transfer transaction successful"}, "eth_transfer"


def get_tools():
=======
    except InsufficientFundsError as e:
        raise
    except Exception as e:
        logger.error(f"Error in ETH transfer: {str(e)}")
        raise ToolError(f"Failed to send ETH: {str(e)}")

def get_tools() -> List[Dict[str, Any]]:
    """Get available tool definitions"""
>>>>>>> domsteil/main:submodules/moragents_dockers/agents/src/base_agent/src/tools.py
    return [
        {
            "type": "function",
            "function": {
                "name": "gasless_usdc_transfer",
                "description": "Transfer USDC to another user without gas fees",
                "parameters": {
                    "type": "object",
                    "properties": {
<<<<<<< HEAD:submodules/moragents_dockers/agents/src/agents/base_agent/tools.py
                        "toAddress": {"type": "string", "description": "Recipient's address."},
                        "amount": {"type": "string", "description": "Amount of USDC to transfer."},
=======
                        "toAddress": {
                            "type": "string",
                            "description": "Recipient's address"
                        },
                        "amount": {
                            "type": "string",
                            "description": "Amount of USDC to transfer"
                        }
>>>>>>> domsteil/main:submodules/moragents_dockers/agents/src/base_agent/src/tools.py
                    },
                    "required": ["toAddress", "amount"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "eth_transfer",
                "description": "Transfer ETH to another user",
                "parameters": {
                    "type": "object",
                    "properties": {
<<<<<<< HEAD:submodules/moragents_dockers/agents/src/agents/base_agent/tools.py
                        "toAddress": {"type": "string", "description": "Recipient's address."},
                        "amount": {"type": "string", "description": "Amount of ETH to transfer."},
                    },
                    "required": ["toAddress", "amount"],
                },
            },
        },
    ]
=======
                        "toAddress": {
                            "type": "string",
                            "description": "Recipient's address"
                        },
                        "amount": {
                            "type": "string",
                            "description": "Amount of ETH to transfer"
                        }
                    },
                    "required": ["toAddress", "amount"]
                }
            }
        }
    ]
>>>>>>> domsteil/main:submodules/moragents_dockers/agents/src/base_agent/src/tools.py

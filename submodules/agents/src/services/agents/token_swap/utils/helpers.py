import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import requests
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput, ContractLogicError

from services.secrets import get_secret

from ..config import Config
from ..models import SwapRoute, TokenInfo
from .exceptions import InsufficientFundsError, SwapNotPossibleError, TokenNotFoundError

logger = logging.getLogger(__name__)


def get_api_headers() -> Dict[str, str]:
    """Get headers for API requests with API key."""
    return {
        "Authorization": f"Bearer {get_secret('1inchApiKey')}",
        "accept": "application/json",
    }


async def search_token(
    query: str,
    chain_id: int,
    limit: int = 1,
    ignore_listed: str = "false",
) -> List[TokenInfo]:
    """
    Search for token by name or symbol.

    Args:
        query: Token symbol or name to search for
        chain_id: Blockchain network ID
        limit: Maximum number of results to return
        ignore_listed: Whether to ignore listed tokens

    Returns:
        List of matching TokenInfo objects

    Raises:
        TokenNotFoundError: If token cannot be found
    """
    logger.info(f"Searching for token - Query: {query}, Chain ID: {chain_id}")
    endpoint = f"/v1.2/{chain_id}/search"
    params = {
        "query": str(query),
        "limit": str(limit),
        "ignore_listed": str(ignore_listed),
    }

    try:
        response = requests.get(Config.INCH_URL + endpoint, params=params, headers=get_api_headers())
        logger.info(f"Search token response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Found token results: {result}")

            if not result:
                raise TokenNotFoundError(f"Token '{query}' not found on chain {chain_id}.")

            return [TokenInfo(symbol=token["symbol"], address=token["address"]) for token in result]
        else:
            error_message = f"API error searching for token '{query}': {response.status_code}"
            try:
                error_details = response.json()
                error_message += f" - {error_details.get('description', '')}"
            except json.JSONDecodeError as json_error:
                error_message += f" - JSON Error: {str(json_error)} - Response: {response.text}"

            logger.error(error_message)
            raise TokenNotFoundError(error_message)
    except requests.RequestException as e:
        error_message = f"Network error searching for token '{query}': {str(e)}"
        logger.error(error_message)
        raise TokenNotFoundError(error_message)


def get_token_balance(web3: Web3, wallet_address: str, token_address: str, abi: List[Any]) -> int:
    """
    Get the balance of a token for a given wallet address.

    Args:
        web3: Web3 instance
        wallet_address: Address of the wallet to check balance for
        token_address: Address of the token (empty for native token)
        abi: ABI for the token contract

    Returns:
        Token balance in smallest units

    Raises:
        InsufficientFundsError: If balance cannot be checked
    """
    try:
        # Ensure wallet address is valid
        checksum_wallet = web3.to_checksum_address(wallet_address)

        if not token_address:  # Native token (ETH, BNB, etc.)
            return web3.eth.get_balance(checksum_wallet)
        else:
            # ERC-20 token
            checksum_token = web3.to_checksum_address(token_address)
            contract = web3.eth.contract(address=checksum_token, abi=abi)
            return contract.functions.balanceOf(checksum_wallet).call()
    except ValueError as e:
        raise InsufficientFundsError(f"Invalid wallet or token address: {str(e)}")
    except (ContractLogicError, BadFunctionCallOutput) as e:
        raise InsufficientFundsError(f"Contract error checking balance: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting token balance: {str(e)}", exc_info=True)
        raise InsufficientFundsError(f"Failed to check token balance: {str(e)}")


def get_token_decimals(web3: Web3, token_address: str) -> int:
    """
    Get the number of decimals for a token.

    Args:
        web3: Web3 instance
        token_address: Address of the token (empty for native token)

    Returns:
        Number of decimals (defaults to 18 for native tokens or if error)
    """
    try:
        if not token_address:
            return 18  # Native tokens (ETH, BNB, etc.) use 18 decimals
        else:
            checksum_address = web3.to_checksum_address(token_address)
            contract = web3.eth.contract(address=checksum_address, abi=Config.ERC20_ABI)
            return contract.functions.decimals().call()
    except Exception as e:
        logger.warning(f"Error getting token decimals for {token_address}: {str(e)}")
        return 18  # Default to 18 decimals if we can't get it


def convert_to_smallest_unit(web3: Web3, amount: float, token_address: str) -> int:
    """
    Convert a human-readable amount to the smallest token unit.

    Args:
        web3: Web3 instance
        amount: Amount in human-readable format
        token_address: Address of the token (empty for native token)

    Returns:
        Amount in smallest units (wei, satoshi, etc.)

    Raises:
        SwapNotPossibleError: If conversion fails
    """
    try:
        decimals = get_token_decimals(web3, token_address)
        # Convert using raw multiplication to avoid web3 unit issues
        return int(amount * (10**decimals))
    except Exception as e:
        logger.error(f"Error converting to smallest unit: {str(e)}", exc_info=True)
        raise SwapNotPossibleError(f"Failed to convert token amount: {str(e)}")


def convert_to_readable_unit(web3: Web3, smallest_unit_amount: int, token_address: str) -> float:
    """
    Convert from smallest unit to human-readable amount.

    Args:
        web3: Web3 instance
        smallest_unit_amount: Amount in smallest units
        token_address: Address of the token (empty for native token)

    Returns:
        Human-readable amount
    """
    try:
        decimals = get_token_decimals(web3, token_address)
        # Convert using raw division to avoid web3 unit issues
        return float(smallest_unit_amount) / (10**decimals)
    except Exception as e:
        logger.error(f"Error converting to readable unit: {str(e)}", exc_info=True)
        # Return 0 as fallback
        return 0.0


async def validate_token_pair(
    web3: Web3,
    source_token: str,
    destination_token: str,
    chain_id: int,
    amount: float,
    wallet_address: str,
) -> Tuple[str, str, str, str]:
    """
    Validate that a swap can be performed and return token addresses and symbols.

    Args:
        web3: Web3 instance
        source_token: Symbol of source token
        destination_token: Symbol of destination token
        chain_id: Blockchain network ID
        amount: Amount to swap
        wallet_address: User's wallet address

    Returns:
        Tuple of (source_token_address, source_token_symbol, destination_token_address, destination_token_symbol)

    Raises:
        TokenNotFoundError: If either token cannot be found
        InsufficientFundsError: If user has insufficient balance
        SwapNotPossibleError: If swap validation fails for other reasons
    """
    try:
        chain_id_str = str(chain_id)
        native_tokens = Config.NATIVE_TOKENS

        # Validate chain ID
        if chain_id_str not in native_tokens:
            raise SwapNotPossibleError(f"Unsupported chain ID: {chain_id}")

        native_token_symbol = native_tokens[chain_id_str]

        # Get source token information
        if source_token.lower() == native_token_symbol.lower():
            # Source is native token (ETH, BNB, etc.)
            source_token_info = TokenInfo(
                symbol=native_token_symbol,
                address=Config.INCH_NATIVE_TOKEN_ADDRESS,
            )
            source_token_balance = get_token_balance(web3, wallet_address, "", Config.ERC20_ABI)
            amount_in_wei = Web3.to_wei(amount, "ether")
        else:
            # Source is ERC-20 token
            source_token_results = await search_token(source_token, chain_id)
            source_token_info = source_token_results[0]
            source_token_balance = get_token_balance(web3, wallet_address, source_token_info.address, Config.ERC20_ABI)
            amount_in_wei = convert_to_smallest_unit(web3, amount, source_token_info.address)

        # Get destination token information
        if destination_token.lower() == native_token_symbol.lower():
            # Destination is native token
            destination_token_info = TokenInfo(
                symbol=native_token_symbol,
                address=Config.INCH_NATIVE_TOKEN_ADDRESS,
            )
        else:
            # Destination is ERC-20 token
            destination_token_results = await search_token(destination_token, chain_id)
            destination_token_info = destination_token_results[0]

        # Check if user has sufficient balance
        if source_token_balance < amount_in_wei:
            readable_balance = (
                web3.from_wei(source_token_balance, "ether")
                if source_token.lower() == native_token_symbol.lower()
                else convert_to_readable_unit(web3, source_token_balance, source_token_info.address)
            )

            raise InsufficientFundsError(
                f"Insufficient funds to perform the swap. You have {readable_balance} {source_token_info.symbol} "
                f"but need {amount} {source_token_info.symbol}."
            )

        # Successful validation
        return (
            source_token_info.address,
            source_token_info.symbol,
            destination_token_info.address,
            destination_token_info.symbol,
        )

    except (TokenNotFoundError, InsufficientFundsError):
        # Let specific exceptions pass through
        raise
    except Exception as e:
        logger.error(f"Error validating swap: {str(e)}", exc_info=True)
        raise SwapNotPossibleError(f"Failed to validate swap: {str(e)}")


async def get_swap_quote(
    source_token_address: str,
    destination_token_address: str,
    amount_in_wei: int,
    chain_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Get a quote for swapping between tokens.

    Args:
        source_token_address: Address of source token
        destination_token_address: Address of destination token
        amount_in_wei: Amount to swap in smallest units
        chain_id: Blockchain network ID

    Returns:
        Quote information dictionary or None if quote fails

    Raises:
        SwapNotPossibleError: If quote cannot be obtained
    """
    logger.info(
        f"Getting quote - Source: {source_token_address}, "
        f"Destination: {destination_token_address}, "
        f"Amount: {amount_in_wei}, "
        f"Chain ID: {chain_id}"
    )

    try:
        endpoint = f"/v6.0/{chain_id}/quote"
        params = {
            "src": source_token_address,
            "dst": destination_token_address,
            "amount": str(amount_in_wei),  # Convert to string to avoid potential overflow
        }

        logger.debug(f"Quote request - URL: {Config.QUOTE_URL + endpoint}, Params: {params}")

        response = requests.get(Config.QUOTE_URL + endpoint, params=params, headers=get_api_headers())
        logger.info(f"Quote response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            logger.info("Quote received successfully")
            return result
        else:
            error_message = f"Failed to get quote. Status code: {response.status_code}"
            try:
                error_details = response.json()
                error_message += f" - {error_details.get('description', '')}"
            except Exception:
                error_message += f" - {response.text}"

            logger.error(error_message)
            raise SwapNotPossibleError(error_message)

    except requests.RequestException as e:
        error_message = f"Network error getting quote: {str(e)}"
        logger.error(error_message)
        raise SwapNotPossibleError(error_message)
    except Exception as e:
        error_message = f"Unexpected error getting quote: {str(e)}"
        logger.error(error_message, exc_info=True)
        raise SwapNotPossibleError(error_message)


def parse_swap_routes(route_data: Dict[str, Any]) -> List[SwapRoute]:
    """
    Parse routing information from a swap quote.

    Args:
        route_data: Raw route data from API

    Returns:
        List of SwapRoute objects
    """
    routes = []

    try:
        if "protocols" in route_data:
            for protocol_group in route_data["protocols"]:
                for protocol in protocol_group:
                    if not protocol:
                        continue

                    for route in protocol:
                        routes.append(
                            SwapRoute(
                                name=route.get("name", "Unknown"),
                                part=float(route.get("part", 0)),
                                from_token_address=route.get("fromTokenAddress", ""),
                                to_token_address=route.get("toTokenAddress", ""),
                            )
                        )
    except Exception as e:
        logger.warning(f"Error parsing swap routes: {str(e)}")

    return routes

import logging
import time

from web3 import Web3

from .config import Config
from .models import SwapQuoteResponse, TransactionResponse, TransactionStatus
from .utils.exceptions import (
    InsufficientFundsError,
    SwapNotPossibleError,
    TokenNotFoundError,
)
from .utils.helpers import (
    convert_to_readable_unit,
    convert_to_smallest_unit,
    get_swap_quote,
    validate_token_pair,
)

logger = logging.getLogger(__name__)


async def swap_coins(
    source_token: str,
    destination_token: str,
    amount: float,
    chain_id: int,
    wallet_address: str,
) -> SwapQuoteResponse:
    """
    Get a quote for swapping tokens.

    Args:
        source_token: Symbol of source token
        destination_token: Symbol of destination token
        amount: Amount of source token to swap
        chain_id: Blockchain network ID
        wallet_address: User's wallet address

    Returns:
        SwapQuoteResponse object with swap details
    """
    logger.info(
        f"Swapping {amount} {source_token} to {destination_token} on chain {chain_id} for wallet {wallet_address}"
    )

    try:
        # Validate inputs
        if not source_token or not destination_token:
            raise ValueError("Source and destination tokens must be provided")

        if amount <= 0:
            raise ValueError("Swap amount must be greater than zero")

        if not wallet_address:
            raise ValueError("Wallet address must be provided")

        if not chain_id:
            raise ValueError("Chain ID must be provided")

        # Initialize Web3 with appropriate provider
        if str(chain_id) not in Config.WEB3RPCURL:
            raise SwapNotPossibleError(f"Unsupported chain ID: {chain_id}")

        web3 = Web3(Web3.HTTPProvider(Config.WEB3RPCURL[str(chain_id)]))

        if not web3.is_connected():
            raise SwapNotPossibleError(f"Cannot connect to RPC for chain ID: {chain_id}")

        # Validate the swap and get token addresses and symbols
        (
            source_token_address,
            source_token_symbol,
            destination_token_address,
            destination_token_symbol,
        ) = await validate_token_pair(web3, source_token, destination_token, chain_id, amount, wallet_address)

        # Get quote from exchange API
        time.sleep(1)  # Rate limiting
        source_amount_in_wei = convert_to_smallest_unit(web3, amount, source_token_address)

        quote_result = await get_swap_quote(
            source_token_address,
            destination_token_address,
            source_amount_in_wei,
            chain_id,
        )

        if not quote_result:
            raise SwapNotPossibleError(
                f"Failed to generate a quote for {source_token_symbol} to {destination_token_symbol}. "
                "Please ensure you're on the correct network."
            )

        # Extract estimated destination amount from quote
        destination_amount_in_wei = int(quote_result["dstAmount"])
        destination_amount = convert_to_readable_unit(web3, destination_amount_in_wei, destination_token_address)

        # Create successful response
        return SwapQuoteResponse(
            success=True,
            src=source_token_symbol,
            src_address=source_token_address,
            src_amount=amount,
            dst=destination_token_symbol,
            dst_address=destination_token_address,
            dst_amount=float(destination_amount),
            approve_tx_cb="/approve",
            swap_tx_cb="/swap",
            estimated_gas=quote_result.get("estimatedGas"),
        )
    except (
        TokenNotFoundError,
        InsufficientFundsError,
        SwapNotPossibleError,
        ValueError,
    ) as e:
        # Convert ValueError to SwapNotPossibleError for consistency
        if isinstance(e, ValueError):
            error = SwapNotPossibleError(str(e))
        else:
            error = e

        # Let expected errors propagate to be handled by the agent
        logger.error(f"Swap error: {str(error)}", exc_info=True)
        raise error
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during swap: {str(e)}", exc_info=True)
        return SwapQuoteResponse(
            success=False,
            src=source_token,
            src_address="",
            src_amount=amount,
            dst=destination_token,
            dst_address="",
            dst_amount=0.0,
            error_message=f"Swap failed: {str(e)}",
        )


async def get_transaction_status(tx_hash: str, chain_id: int, wallet_address: str) -> TransactionResponse:
    """
    Get the status of a transaction.

    Args:
        tx_hash: Transaction hash
        chain_id: Blockchain network ID
        wallet_address: User's wallet address

    Returns:
        TransactionResponse object with transaction details
    """
    logger.info(f"Getting status for transaction {tx_hash} on chain {chain_id}")

    try:
        # Validate inputs
        if not tx_hash:
            raise ValueError("Transaction hash must be provided")

        if not chain_id:
            raise ValueError("Chain ID must be provided")

        if not wallet_address:
            raise ValueError("Wallet address must be provided")

        # Check if chain is supported
        if str(chain_id) not in Config.WEB3RPCURL:
            raise ValueError(f"Unsupported chain ID: {chain_id}")

        # Initialize Web3 with appropriate provider
        web3 = Web3(Web3.HTTPProvider(Config.WEB3RPCURL[str(chain_id)]))

        if not web3.is_connected():
            raise ValueError(f"Cannot connect to RPC for chain ID: {chain_id}")

        # Get transaction receipt
        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
        except Exception as e:
            logger.warning(f"Failed to get transaction receipt: {str(e)}")
            receipt = None

        # Get transaction details
        try:
            tx = web3.eth.get_transaction(tx_hash)
        except Exception as e:
            logger.warning(f"Failed to get transaction: {str(e)}")
            # If we can't get the transaction, return a minimal response
            return TransactionResponse(
                success=False,
                status=TransactionStatus.PENDING,
                tx_hash=tx_hash,
                from_address=wallet_address,
                to_address="",
                network_id=chain_id,
                error_message=f"Transaction not found: {str(e)}",
            )

        # Determine status
        if receipt is None:
            status = TransactionStatus.PENDING
        elif receipt.status == 1:
            status = TransactionStatus.CONFIRMED
        else:
            status = TransactionStatus.FAILED

        # Create response
        return TransactionResponse(
            success=True,
            status=status,
            tx_hash=tx_hash,
            from_address=tx["from"],
            to_address=tx["to"],
            value=web3.from_wei(tx["value"], "ether") if tx["value"] else None,
            network_id=chain_id,
            gas_used=receipt.gasUsed if receipt else None,
            gas_price=tx["gasPrice"],
            metadata={
                "block_number": receipt.blockNumber if receipt else None,
                "block_hash": receipt.blockHash.hex() if receipt and receipt.blockHash else None,
                "confirmations": web3.eth.block_number - receipt.blockNumber if receipt and receipt.blockNumber else 0,
            },
        )

    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error in transaction status: {str(e)}")
        return TransactionResponse(
            success=False,
            status=TransactionStatus.FAILED,
            tx_hash=tx_hash if tx_hash else "",
            from_address=wallet_address,
            to_address="",
            network_id=chain_id if chain_id else 0,
            error_message=str(e),
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error getting transaction status: {str(e)}", exc_info=True)
        return TransactionResponse(
            success=False,
            status=TransactionStatus.FAILED,
            tx_hash=tx_hash if tx_hash else "",
            from_address=wallet_address if wallet_address else "",
            to_address="",
            network_id=chain_id if chain_id else 0,
            error_message=f"Failed to get transaction status: {str(e)}",
        )

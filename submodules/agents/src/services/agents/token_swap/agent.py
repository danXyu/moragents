import logging
from typing import Any, Dict

from models.service.agent_core import AgentCore
from models.service.chat_models import AgentResponse, ChatRequest

from .config import Config
from .tools import get_transaction_status, swap_coins
from .utils.exceptions import InsufficientFundsError, SwapNotPossibleError, TokenNotFoundError
from .utils.tool_types import SwapToolType

logger = logging.getLogger(__name__)


import logging
from typing import Any, Dict, Optional, Union

from models.service.agent_core import AgentCore
from models.service.chat_models import AgentResponse, ChatRequest

from .config import Config
from .models import SwapQuoteResponse, TransactionResponse
from .tools import get_transaction_status, swap_coins
from .utils.exceptions import InsufficientFundsError, SwapNotPossibleError, TokenNotFoundError
from .utils.tool_types import SwapToolType

logger = logging.getLogger(__name__)


class TokenSwapAgent(AgentCore):
    """Agent for token swapping operations."""

    def __init__(self, config: Dict[str, Any], llm: Any):
        super().__init__(config, llm)
        self.tools_provided = Config.tools
        self.tool_bound_llm = self.llm.bind_tools(self.tools_provided)
        self.wallet_address = None
        self.chain_id = None

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for token swap operations."""
        try:
            messages = [Config.system_message, *request.messages_for_llm]

            # Store wallet and chain information
            self.wallet_address = request.wallet_address
            self.chain_id = request.chain_id

            # Validate wallet connection
            if not self.wallet_address or not self.chain_id:
                return AgentResponse.needs_info(content="Please connect your wallet to enable swap functionality")

            result = self.tool_bound_llm.invoke(messages)
            return await self._handle_llm_response(result)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=f"Failed to process request: {str(e)}")

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute the appropriate token swap tool based on function name."""
        try:
            if func_name == SwapToolType.SWAP_TOKENS.value:
                return await self._execute_swap_tokens(args)
            elif func_name == SwapToolType.GET_TRANSACTION_STATUS.value:
                return await self._execute_get_transaction_status(args)
            else:
                return AgentResponse.error(error_message=f"Unknown tool: {func_name}")

        except Exception as e:
            logger.error(
                f"Unexpected error in tool execution {func_name}: {str(e)}",
                exc_info=True,
            )
            return AgentResponse.error(error_message=f"Unexpected error: {str(e)}")

    async def _execute_swap_tokens(self, args: Dict[str, Any]) -> AgentResponse:
        """Execute the swap tokens operation with comprehensive error handling."""
        try:
            # Revalidate wallet connection
            if not self.wallet_address or not self.chain_id:
                return AgentResponse.needs_info(content="Please connect your wallet to enable swap functionality")

            # Validate required parameters
            required_params = ["source_token", "destination_token", "amount"]
            missing_params = [param for param in required_params if param not in args or args[param] is None]

            if missing_params:
                return AgentResponse.needs_info(
                    content=f"Please provide the following information: {', '.join(missing_params)}"
                )

            # Validate amount is a positive number
            try:
                amount = float(args["amount"])
                if amount <= 0:
                    return AgentResponse.error(error_message="Swap amount must be greater than zero")
            except ValueError:
                return AgentResponse.error(error_message=f"Invalid amount format: {args['amount']}")

            # Execute swap operation
            swap_response = await swap_coins(
                source_token=args["source_token"],
                destination_token=args["destination_token"],
                amount=amount,
                chain_id=self.chain_id,
                wallet_address=self.wallet_address,
            )

            return AgentResponse.success(
                content=swap_response.formatted_response,
                metadata=swap_response.model_dump(),
                action_type="swap",
            )

        except TokenNotFoundError as e:
            logger.error(f"Token not found: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=f"Token not found: {str(e)}")

        except InsufficientFundsError as e:
            logger.error(f"Insufficient funds: {str(e)}", exc_info=True)
            logger.info("We get here")
            return AgentResponse.error(error_message=f"Insufficient funds: {str(e)}")

        except SwapNotPossibleError as e:
            logger.error(f"Swap not possible: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=f"Swap not possible: {str(e)}")

        except Exception as e:
            logger.error(f"Error executing swap: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=f"Error executing swap: {str(e)}")

    async def _execute_get_transaction_status(self, args: Dict[str, Any]) -> AgentResponse:
        """Execute the get transaction status operation with comprehensive error handling."""
        try:
            # Extract and validate transaction hash
            tx_hash = args.get("tx_hash")
            if not tx_hash:
                return AgentResponse.needs_info(content="Please provide a transaction hash")

            # Use provided chain_id and wallet_address from args if available, otherwise use class values
            chain_id = args.get("chainId", self.chain_id)
            wallet_address = args.get("walletAddress", self.wallet_address)

            # Validate we have the necessary parameters
            if not chain_id:
                return AgentResponse.needs_info(content="Please provide a chain ID or connect your wallet")

            if not wallet_address:
                return AgentResponse.needs_info(content="Please provide a wallet address or connect your wallet")

            # Execute transaction status check
            tx_response = await get_transaction_status(
                tx_hash=tx_hash,
                chain_id=chain_id,
                wallet_address=wallet_address,
            )

            return AgentResponse.success(
                content=tx_response.formatted_response,
                metadata=tx_response.model_dump(),
                action_type="transaction_status",
            )

        except Exception as e:
            logger.error(f"Error getting transaction status: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=f"Error retrieving transaction status: {str(e)}")

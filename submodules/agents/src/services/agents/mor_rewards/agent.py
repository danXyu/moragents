import logging
from decimal import Decimal

from models.service.agent_core import AgentCore
from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.mor_rewards import tools

logger = logging.getLogger(__name__)


class MorRewardsAgent(AgentCore):
    def __init__(self, config, llm):
        super().__init__(config, llm)
        self.tools_provided = tools.get_tools()

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for MOR rewards."""
        try:
            if not request.wallet_address:
                return AgentResponse.needs_info(content="Please provide a wallet address to check rewards.")

            logger.info(f"Checking rewards for wallet address: {request.wallet_address}")

            # Get rewards
            rewards_decimal = {
                0: tools.get_current_user_reward(request.wallet_address, 0),
                1: tools.get_current_user_reward(request.wallet_address, 1),
            }

            # Convert Decimal objects to float for JSON serialization
            rewards_json_serializable = {pool_id: float(amount) for pool_id, amount in rewards_decimal.items()}

            response = "Your current MOR rewards:\n"
            response += f"Capital Providers Pool (Pool 0): {rewards_decimal[0]} MOR\n"
            response += f"Code Providers Pool (Pool 1): {rewards_decimal[1]} MOR"

            logger.info(f"Rewards retrieved successfully for {request.wallet_address}")
            return AgentResponse.success(content=response, metadata={"rewards": rewards_json_serializable})

        except Exception as e:
            logger.error(f"Error occurred while checking rewards: {str(e)}")
            return AgentResponse.error(error_message=f"An error occurred while checking your rewards: {str(e)}")

    async def _execute_tool(self, func_name: str, args: dict) -> AgentResponse:
        """Not implemented as this agent doesn't use tools."""
        return AgentResponse.error(error_message="This agent does not support tool execution")

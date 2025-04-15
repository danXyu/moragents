import logging
from typing import Any, Dict

from langchain.schema import SystemMessage
from models.service.agent_core import AgentCore
from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.base_agent import tools
from services.agents.base_agent.config import Config
from services.agents.base_agent.tool_types import BaseAgentToolType
from stores.wallet_manager import wallet_manager_instance

logger = logging.getLogger(__name__)


class BaseAgent(AgentCore):
    """Agent for handling Base blockchain transactions."""

    def __init__(self, config: Dict[str, Any], llm: Any):
        super().__init__(config, llm)
        self.tools_provided = Config.tools
        self.tool_bound_llm = self.llm.bind_tools(self.tools_provided)

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for Base transactions."""
        # Check CDP client initialization
        if not wallet_manager_instance.configure_cdp_client():
            # Return user-friendly error for missing credentials
            return AgentResponse.success(
                content="I'm not able to help with transactions right now because the CDP client is not initialized. "
                "Please set up your API credentials first."
            )

        # Check for active wallet
        active_wallet = wallet_manager_instance.get_active_wallet()
        if not active_wallet:
            # Return user-friendly error for missing wallet
            return AgentResponse.success(
                content="You'll need to select or create a wallet before I can help with transactions. "
                "Please set up a wallet first."
            )

        try:
            messages = [
                SystemMessage(
                    content=(
                        "You are an agent that can perform various financial transactions on Base. "
                        "When you need to perform an action, use the appropriate function with the correct arguments."
                    )
                ),
                *request.messages_for_llm,
            ]

            result = self.tool_bound_llm.invoke(messages)
            return await self._handle_llm_response(result)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute the appropriate Base transaction tool based on function name."""
        try:
            if func_name == BaseAgentToolType.SWAP_ASSETS.value:
                return AgentResponse.action_required(content="Ready to perform swap", action_type="swap")
            elif func_name == BaseAgentToolType.TRANSFER_ASSET.value:
                return AgentResponse.action_required(content="Ready to perform transfer", action_type="transfer")
            elif func_name == BaseAgentToolType.GET_BALANCE.value:
                wallet = wallet_manager_instance.get_active_wallet()
                if not wallet:
                    return AgentResponse.success(
                        content="I can't check the balance because no wallet is selected. Please select a wallet first."
                    )

                asset_id = args.get("asset_id")
                if not asset_id:
                    return AgentResponse.needs_info(
                        content="Please specify which asset you'd like to check the balance for."
                    )

                tool_result = tools.get_balance(wallet, asset_id=asset_id.lower())
                content = (
                    f"Your wallet {tool_result['address']} has a balance of {tool_result['balance']} "
                    f"{tool_result['asset']}"
                )
                return AgentResponse.success(content=content)
            else:
                return AgentResponse.needs_info(
                    content=f"I don't know how to {func_name} yet. Please try a different action."
                )

        except Exception as e:
            logger.error(f"Error executing tool {func_name}: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

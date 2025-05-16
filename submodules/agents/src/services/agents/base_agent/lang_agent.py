import logging
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import BaseTool, Tool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.base_agent.tool_types import BaseAgentToolType
from services.langchain_agent import LangChainAgent
from stores.wallet_manager import wallet_manager_instance

logger = logging.getLogger(__name__)


class BaseAgent(LangChainAgent):
    """
    Agent for handling Base blockchain transactions using LangChain.
    """

    def __init__(self, config: Dict[str, Any], llm: BaseLanguageModel):
        self.base_tools = self._create_base_tools()
        super().__init__(llm, self.base_tools, config)

    def _create_base_tools(self) -> List[BaseTool]:
        """Create LangChain tool instances for Base operations"""

        # Define tool functions first
        def swap_assets(amount: str, from_asset_id: str, to_asset_id: str) -> str:
            """Swap one asset for another on Base network."""
            # We'll return an action required response in _to_agent_response
            return f"Preparing to swap {amount} {from_asset_id} to {to_asset_id}"

        def transfer_asset(amount: str, asset_id: str) -> str:
            """Transfer an asset to another address on Base network."""
            # We'll return an action required response in _to_agent_response
            return f"Preparing to transfer {amount} {asset_id}"

        def get_balance(asset_id: str) -> str:
            """Get the balance of a specific asset in the active wallet."""
            wallet = wallet_manager_instance.get_active_wallet()
            if not wallet:
                return "No wallet selected. Please select a wallet first."

            from services.agents.base_agent import tools

            tool_result = tools.get_balance(wallet, asset_id=asset_id.lower())
            return (
                f"Your wallet {tool_result['address']} has a balance of "
                f"{tool_result['balance']} {tool_result['asset']}"
            )

        # Create the tools using the Tool class directly
        return [
            Tool(
                name=BaseAgentToolType.SWAP_ASSETS.value,
                description="Swap one asset for another (Base Mainnet only)",
                func=swap_assets,
            ),
            Tool(
                name=BaseAgentToolType.TRANSFER_ASSET.value,
                description="Transfer an asset to another address",
                func=transfer_asset,
            ),
            Tool(
                name=BaseAgentToolType.GET_BALANCE.value,
                description="Get balance of a specific asset",
                func=get_balance,
            ),
        ]

    def _create_agent_executor(self) -> AgentExecutor:
        """Create and configure the LangChain agent executor"""

        # First validate wallet and CDP client
        # Note: We'll check this again at runtime, this is just for initialization
        if not wallet_manager_instance.configure_cdp_client():
            logger.warning("CDP client not initialized")

        if not wallet_manager_instance.get_active_wallet():
            logger.warning("No active wallet selected")

        # Create the prompt with system message
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(
                        "You are an agent that can perform various financial transactions on Base. "
                        "When you need to perform an action, use the appropriate function with the correct arguments."
                    )
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Create the OpenAI Functions agent
        agent = create_openai_functions_agent(llm=self.llm, tools=self.base_tools, prompt=prompt)

        # Create the executor
        return AgentExecutor(agent=agent, tools=self.base_tools, verbose=True, handle_parsing_errors=True)

    def _validate_request(self, request: ChatRequest) -> Optional[AgentResponse]:
        """Validate common request parameters and check for required initializations"""
        # First do the standard validation
        validation = super()._validate_request(request)
        if validation:
            return validation

        # Check CDP client initialization
        if not wallet_manager_instance.configure_cdp_client():
            return AgentResponse.success(
                content="I'm not able to help with transactions right now because the CDP client is not initialized. "
                "Please set up your API credentials first."
            )

        # Check for active wallet
        active_wallet = wallet_manager_instance.get_active_wallet()
        if not active_wallet:
            return AgentResponse.success(
                content="You'll need to select or create a wallet before I can help with transactions. "
                "Please set up a wallet first."
            )

        return None

    def _to_agent_response(self, result: Dict[str, Any]) -> AgentResponse:
        """Convert LangChain agent output to standardized AgentResponse"""

        output = result.get("output", "")

        # Check intermediate steps for tool executions
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if len(step) >= 2:
                    tool_name = getattr(step[0], "name", None)
                    tool_args = getattr(step[0], "args", {})

                    # Handle action required tools
                    if tool_name == BaseAgentToolType.SWAP_ASSETS.value:
                        return AgentResponse.action_required(
                            content=f"Ready to swap {tool_args.get('amount')} "
                            f"{tool_args.get('from_asset_id')} to {tool_args.get('to_asset_id')}",
                            action_type="swap",
                        )
                    elif tool_name == BaseAgentToolType.TRANSFER_ASSET.value:
                        return AgentResponse.action_required(
                            content=f"Ready to transfer {tool_args.get('amount')} " f"{tool_args.get('asset_id')}",
                            action_type="transfer",
                        )

        # If we made it here, return the standard output
        return AgentResponse.success(content=output)

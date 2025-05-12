from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar

from langchain.agents import AgentExecutor
from langchain.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import Runnable, RunnableConfig
from models.service.chat_models import AgentResponse, ChatRequest

T = TypeVar("T")


class LangChainAgent(Runnable[ChatRequest, AgentResponse], ABC):
    """
    Standardized agent interface compatible with LangChain and LangGraph.
    Implements the Runnable protocol for seamless integration with LangGraph.
    """

    def __init__(self, llm: BaseLanguageModel, tools: List[BaseTool], config: Dict[str, Any]):
        self.llm = llm
        self.tools = tools
        self.config = config
        self.agent_executor = self._create_agent_executor()

    @abstractmethod
    def _create_agent_executor(self) -> AgentExecutor:
        """Create and return the agent executor with tools and LLM configured"""
        pass

    async def ainvoke(
        self, input: ChatRequest, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> AgentResponse:
        """Async invocation for LangGraph compatibility"""
        try:
            # Validate the request
            validation_result = self._validate_request(input)
            if validation_result:
                return validation_result

            # Process using LangChain agent executor
            result = await self.agent_executor.ainvoke({"messages": input.messages_for_llm}, config=config)

            # Convert to standardized AgentResponse
            return self._to_agent_response(result)
        except Exception as e:
            return AgentResponse.error(error_message=str(e))

    def invoke(self, input: ChatRequest, config: Optional[RunnableConfig] = None, **kwargs: Any) -> AgentResponse:
        """Synchronous invocation (required by Runnable protocol)"""
        try:
            # Validate the request
            validation_result = self._validate_request(input)
            if validation_result:
                return validation_result

            # Process using LangChain agent executor
            result = self.agent_executor.invoke({"messages": input.messages_for_llm}, config=config)

            # Convert to standardized AgentResponse
            return self._to_agent_response(result)
        except Exception as e:
            return AgentResponse.error(error_message=str(e))

    def _validate_request(self, request: ChatRequest) -> Optional[AgentResponse]:
        """Validate common request parameters"""
        if not request.prompt:
            return AgentResponse.error(error_message="Please provide a prompt to process your request")
        return None

    @abstractmethod
    def _to_agent_response(self, result: Dict[str, Any]) -> AgentResponse:
        """Convert LangChain agent output to standardized AgentResponse"""
        pass

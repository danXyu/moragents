import logging
from typing import Any, Dict, List

from langchain.schema import StructuredTool

from models.service.agent_core import AgentCore
from models.service.chat_models import AgentResponse, ChatRequest

from .config import Config

logger = logging.getLogger(__name__)


class RAGAgent(AgentCore):
    """Agent for handling retrieval-augmented generation."""

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.tools_provided: List[StructuredTool] = []

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for RAG-based responses."""
        try:
            # Simple example for direct RAG response
            messages = [Config.system_message, *request.messages_for_llm]
            response = await self._call_llm_with_tools(messages, self.tools_provided)

            if response.content:
                return AgentResponse.success(content=response.content)
            else:
                return AgentResponse.error(error_message="Failed to generate a response")

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """RAG agent doesn't use any tools."""
        return AgentResponse.error(error_message=f"Unknown tool: {func_name}")

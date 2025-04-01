import logging
from typing import Any, Dict

from config import RAG_VECTOR_STORE
from langchain.schema import HumanMessage
from models.service.agent_core import AgentCore
from models.service.chat_models import AgentResponse, ChatRequest

from .config import Config

logger = logging.getLogger(__name__)


class RagAgent(AgentCore):
    """Agent for handling document Q&A using RAG."""

    def __init__(self, config: Dict[str, Any], llm: Any) -> None:
        super().__init__(config, llm)

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for RAG."""
        try:
            if RAG_VECTOR_STORE.retriever is None:
                return AgentResponse.needs_info(content="Please upload a file first")

            retrieved_docs = await RAG_VECTOR_STORE.retrieve(request.prompt.content)
            formatted_context = "\n\n".join(doc.page_content for doc in retrieved_docs)

            messages = [
                Config.system_message,
                HumanMessage(content=f"Context from documents:\n{formatted_context}"),
                *request.messages_for_llm,
            ]

            result = self.llm.invoke(messages)
            return AgentResponse.success(content=result.content.strip())

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    async def _execute_tool(
        self, func_name: str, args: Dict[str, Any]
    ) -> AgentResponse:
        """RAG agent doesn't use any tools."""
        return AgentResponse.error(error_message=f"Unknown tool: {func_name}")

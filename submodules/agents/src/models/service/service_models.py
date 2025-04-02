from typing import List

from langchain.schema import AIMessage, BaseMessage, HumanMessage
from models.service.chat_models import ChatMessage
from pydantic import BaseModel, Field


class GenerateConversationTitleRequest(BaseModel):
    """Request model for generating a conversation title"""

    conversation_id: str = Field(default="default")
    chat_history: List[ChatMessage] = Field(default_factory=list)

    @property
    def messages_for_llm(self) -> List[BaseMessage]:
        """Get formatted message history for LLM"""
        messages: List[BaseMessage] = []

        # Add chat history messages up to the past 10 messages
        for msg in self.chat_history[:10]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        return messages

from models.service.agent_config import AgentConfig
from langchain.schema import SystemMessage


class Config:
    """Configuration for RAG Agent."""

    # *************
    # AGENT CONFIG
    # ------------
    # This must be defined in every agent config file
    # It is required to load the agent
    # *************

    agent_config = AgentConfig(
        path="services.agents.rag.agent",
        class_name="RagAgent",
        description="Processes and analyzes uploaded documents to answer questions about their contents",
        delegator_description="Specializes in analyzing and extracting insights from uploaded documents, PDFs, "
        "and text files. Use when users need to ask questions about specific documents they've "
        "provided or want to analyze document contents. Only activates when users have uploaded "
        "files to analyze.",
        human_readable_name="Document Q&A",
        command="rag",
        upload_required=True,
    )

    # *************
    # SYSTEM MESSAGE
    # *************

    system_message = SystemMessage(
        content=(
            "You are a helpful assistant that can answer questions about uploaded documents. "
            "You must only answer questions based on the provided context from the documents. "
            "If asked about topics outside the documents, politely explain that you can only "
            "answer questions about the uploaded documents' contents. "
            "Always maintain a helpful and professional tone. "
            "If the context is insufficient to fully answer a question, acknowledge this "
            "and explain what information is missing."
        )
    )

from models.service.agent_config import AgentConfig


class Config:
    """Configuration for RAG Agent."""

    # *************
    # AGENT CONFIG
    # ------------
    # This must be defined in every agent config file
    # It is required to load the agent
    # *************

    agent_config = AgentConfig(
        path="src.services.agents.rag.agent",
        class_name="RAGAgent",
        description="Processes and analyzes uploaded documents to answer questions about their contents",
        delegator_description="Specializes in analyzing and extracting insights from uploaded documents, PDFs, "
        "and text files. Use when users need to ask questions about specific documents they've "
        "provided or want to analyze document contents. Only activates when users have uploaded "
        "files to analyze.",
        human_readable_name="Document Q&A",
        command="rag",
        upload_required=True,
        is_enabled=False,
    )

    # *************
    # RAG CONFIG
    # *************

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_LENGTH = 16 * 1024 * 1024

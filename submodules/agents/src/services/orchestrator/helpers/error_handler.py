"""Global error handler for orchestration flow."""

import logging
from typing import Any, Dict, Optional

from models.service.chat_models import AgentResponse

logger = logging.getLogger(__name__)


class OrchestrationError(Exception):
    """Custom exception for orchestration errors."""

    pass


def safe_orchestration_response(
    success: bool = False,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[Exception] = None,
) -> AgentResponse:
    """Create a safe response even when errors occur."""
    if error:
        logger.error(f"Orchestration error: {str(error)}")

        # Provide a user-friendly error message
        error_content = (
            "I encountered an issue while processing your request. "
            "I'll do my best to provide a response based on what I could process."
        )

        # Include partial results if available
        if metadata and metadata.get("subtask_outputs"):
            partial_results = []
            for output in metadata["subtask_outputs"]:
                if hasattr(output, "output") and output.output:
                    partial_results.append(output.output)

            if partial_results:
                error_content += "\n\nHere's what I was able to gather:\n" + "\n".join(partial_results)

        return AgentResponse.success(content=content or error_content, metadata=metadata or {})

    return AgentResponse.success(content=content or "Request completed.", metadata=metadata or {})

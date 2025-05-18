"""Context utilities."""

from typing import List, Optional
from services.orchestrator.orchestration_state import SubtaskOutput
from .task_composition import TaskComponents, optimize_previous_outputs, compose_task_description


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Safely truncate text to a maximum number of characters."""
    if not text:
        return ""

    max_chars = int(max_chars)

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "... (truncated)"


def summarize_previous_outputs(previous_outputs: Optional[List[SubtaskOutput]], max_total_context: int = 2000) -> str:
    """Create a summary of previous subtask outputs using intelligent optimization."""
    return optimize_previous_outputs(previous_outputs, max_total_context)


def create_focused_task_description(
    subtask: str, chat_prompt: str, chat_summary: str, previous_context: str, max_total_length: int = 1500
) -> str:
    """Create a focused task description with proper context using intelligent optimization."""
    components = TaskComponents(
        core_task=subtask, original_goal=chat_prompt, chat_context=chat_summary, previous_work=previous_context
    )

    return compose_task_description(components, max_total_length)

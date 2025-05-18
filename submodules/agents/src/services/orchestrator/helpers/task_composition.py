"""Task description composition utilities with clear separation of concerns."""

from typing import List, Optional
from dataclasses import dataclass

from .context_optimization import optimize_context_block
from ..orchestration_state import SubtaskOutput


@dataclass
class TaskComponents:
    """Components that make up a task description."""

    core_task: str
    original_goal: str
    chat_context: Optional[str] = None
    previous_work: Optional[str] = None

    def __post_init__(self):
        """Ensure all components are strings."""
        self.core_task = str(self.core_task) if self.core_task else ""
        self.original_goal = str(self.original_goal) if self.original_goal else ""
        self.chat_context = str(self.chat_context) if self.chat_context else ""
        self.previous_work = str(self.previous_work) if self.previous_work else ""


def optimize_previous_outputs(previous_outputs: Optional[List[SubtaskOutput]], max_total_length: int = 10000) -> str:
    """Create an optimized summary of previous subtask outputs."""
    if not previous_outputs:
        return ""

    # Convert outputs to text format
    outputs_text = ""
    for i, output in enumerate(previous_outputs):
        task_num = len(previous_outputs) - i
        outputs_text += f"Task {task_num}: {output.subtask}\n"
        outputs_text += f"Result: {output.output}\n"
        if output.agents:
            agent_list = list(output.agents)[:2]  # Limit to 2 agents for brevity
            outputs_text += f"Executed by: {', '.join(agent_list)}\n"
        outputs_text += "---\n"

    # Optimize the outputs text
    optimized = optimize_context_block(
        outputs_text, max_length=max_total_length, preserve_start=200, preserve_end=100  # Preserve more recent context
    )

    return "Summary of completed work:\n" + optimized if optimized else ""


def optimize_chat_context(chat_summary: str, max_length: int = 500) -> str:
    """Optimize chat context to preserve important information."""
    if not chat_summary:
        return ""

    optimized = optimize_context_block(chat_summary, max_length=max_length, preserve_start=150, preserve_end=150)

    return optimized


def compose_task_description(components: TaskComponents, max_total_length: int = 1500) -> str:
    """
    Compose a focused task description from components while respecting length limits.
    Uses intelligent context optimization to preserve important information.
    """
    # Start with core components that must be included
    description = f"Task: {components.core_task}\n\n"

    # Add original goal with optimization if needed
    if len(components.original_goal) <= 400:
        description += f"Original goal: {components.original_goal}\n\n"
    else:
        optimized_goal = optimize_context_block(components.original_goal, 400)
        description += f"Original goal: {optimized_goal}\n\n"

    # Calculate remaining length
    remaining_length = max_total_length - len(description)

    # Allocate remaining space between chat context and previous work
    if components.chat_context and components.previous_work:
        # Split remaining length between context types
        context_length = remaining_length // 2

        # Add optimized chat context
        if components.chat_context:
            chat_context = optimize_chat_context(components.chat_context, context_length)
            if chat_context:
                description += f"Context from conversation:\n{chat_context}\n\n"
                remaining_length -= len(chat_context)

        # Add previous work context
        if components.previous_work and remaining_length > 100:
            work_context = optimize_context_block(
                components.previous_work, remaining_length, preserve_start=150, preserve_end=100
            )
            if work_context:
                description += work_context + "\n"

    # Add focused instructions
    description += (
        "Instructions:\n"
        "1. Focus on completing the specific task above\n"
        "2. Build upon previous work without repeating it\n"
        "3. Use tools efficiently to get accurate results\n"
        "4. Provide a complete answer addressing all aspects of the task\n"
    )

    return description

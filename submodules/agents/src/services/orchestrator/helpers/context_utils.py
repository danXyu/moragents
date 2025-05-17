"""Context utilities."""

from typing import List, Optional
from services.orchestrator.orchestration_state import SubtaskOutput


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Safely truncate text to a maximum number of characters."""
    if not text:
        return ""
    
    max_chars = int(max_chars)
    
    if len(text) <= max_chars:
        return text
        
    return text[:max_chars] + "... (truncated)"


def summarize_previous_outputs(
    previous_outputs: Optional[List[SubtaskOutput]],
    max_context_per_output: int = 200,
    max_total_context: int = 800
) -> str:
    """Create a summary of previous subtask outputs."""
    if not previous_outputs:
        return ""
    
    # Ensure integers
    max_context_per_output = int(max_context_per_output)
    max_total_context = int(max_total_context)
    
    context_parts = []
    total_chars = 0
    
    # Convert to list to ensure we can reverse it properly
    outputs_list = list(previous_outputs)
    for i, output in enumerate(reversed(outputs_list)):
        # Calculate max characters for this output
        if i == 0:  # Most recent
            max_chars = int(max_context_per_output * 1.5)
        elif i == 1:  # Second most recent  
            max_chars = max_context_per_output
        else:  # Older outputs
            max_chars = max_context_per_output // 2
        
        # Ensure positive
        max_chars = max(50, max_chars)
        
        # Build summary
        task_num = len(outputs_list) - i
        summary = f"Task {task_num}: {truncate_text(output.subtask, 100)}\n"
        
        # Get output text
        output_text = truncate_text(output.output, max_chars)
        summary += f"Result: {output_text}\n"
        
        # Add agent info
        if output.agents:
            # Ensure agents is a list and slice it properly
            agent_list = list(output.agents)
            agents_str = ', '.join(agent_list[:2])
            summary += f"Executed by: {agents_str}\n"
        
        # Check total length
        if total_chars + len(summary) < max_total_context:
            context_parts.append(summary)
            total_chars += len(summary)
        else:
            break
    
    # Reverse to maintain chronological order
    context_parts.reverse()
    
    if context_parts:
        return "Summary of completed work:\n" + "\n---\n".join(context_parts)
    return ""


def create_focused_task_description(
    subtask: str,
    chat_prompt: str,
    chat_summary: str,
    previous_context: str,
    max_total_length: int = 1500
) -> str:
    """Create a focused task description with proper context."""
    max_total_length = int(max_total_length)
    
    # Ensure all inputs are strings
    subtask = str(subtask) if subtask else ""
    chat_prompt = str(chat_prompt) if chat_prompt else ""
    chat_summary = str(chat_summary) if chat_summary else ""
    previous_context = str(previous_context) if previous_context else ""
    
    # Start with the core task
    description = f"Task: {subtask}\n\n"
    
    # Add original goal
    if len(chat_prompt) <= 400:
        description += f"Original goal: {chat_prompt}\n\n"
    else:
        truncated_prompt = truncate_text(chat_prompt, 400)
        description += f"Original goal: {truncated_prompt}\n\n"
    
    # Add chat context if relevant
    if chat_summary and len(description) + len(chat_summary) < max_total_length - 300:
        description += f"Context from conversation: {chat_summary}\n\n"
    
    # Add previous work context if available and fits  
    if previous_context and len(description) + len(previous_context) < max_total_length:
        description += previous_context + "\n"
    
    # Add focused instructions
    description += (
        "Instructions:\n"
        "1. Focus on completing the specific task above\n"
        "2. Build upon previous work without repeating it\n"
        "3. Use tools efficiently to get accurate results\n"
        "4. Provide a complete answer addressing all aspects of the task\n"
    )
    
    return description
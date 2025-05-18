"""Utilities for optimizing agent-related token usage."""

from typing import List

from services.orchestrator.registry.agent_registry import AgentRegistry


def get_optimized_agent_descriptions(subtasks: List[str]) -> str:
    """Get agent descriptions optimized for the specific subtasks."""
    # Get all available agents
    all_agents = AgentRegistry.llm_choice_payload()

    # If we have specific task keywords, we can filter agents
    task_keywords = []
    for subtask in subtasks:
        task_lower = subtask.lower()
        if "image" in task_lower or "visual" in task_lower:
            task_keywords.append("image")
        if "code" in task_lower or "program" in task_lower:
            task_keywords.append("code")
        if "search" in task_lower or "find" in task_lower:
            task_keywords.append("search")
        if "data" in task_lower or "analyze" in task_lower:
            task_keywords.append("data")
        if "tweet" in task_lower or "twitter" in task_lower:
            task_keywords.append("tweet")
        if "crypto" in task_lower or "token" in task_lower:
            task_keywords.append("crypto")

    # If we have specific keywords, filter descriptions
    if task_keywords:
        filtered_descriptions = []
        agent_lines = all_agents.strip().split("\n")

        for line in agent_lines:
            line_lower = line.lower()
            # Always include the line if it matches our keywords
            if any(keyword in line_lower for keyword in task_keywords):
                filtered_descriptions.append(line)
            # Also include general-purpose agents
            elif "default" in line_lower or "general" in line_lower:
                filtered_descriptions.append(line)

        # If we filtered too aggressively, return original
        if len(filtered_descriptions) < 3:
            return all_agents

        return "\n".join(filtered_descriptions)

    return all_agents


def create_concise_agent_description(agent_name: str, role: str) -> str:
    """Create a concise agent description for task execution."""
    # Remove verbose backstories and goals, keep only essential info
    if len(role) > 150:
        # Extract first sentence or key capability
        sentences = role.split(". ")
        if sentences:
            return sentences[0] + "."
    return role

"""
Tool registry – stores tool instances and exposes
metadata so the LLM can decide which ones to use for each sub‑task.
"""

from __future__ import annotations

from typing import Any, Dict, List, Type


class ToolRegistry:
    _tools: Dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # registration helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def register(cls, name: str, tool: Any) -> None:
        """
        Register a tool with the registry.

        Args:
            name: Unique identifier for the tool
            tool: The tool instance to register
        """
        cls._tools[name] = tool

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    @classmethod
    def get(cls, name: str) -> Any:
        """
        Get a tool by name.

        Args:
            name: The name of the tool to retrieve

        Returns:
            The tool instance

        Raises:
            KeyError: If the tool is not found
        """
        return cls._tools[name]

    @classmethod
    def all_names(cls) -> List[str]:
        """
        Get the names of all registered tools.

        Returns:
            List of tool names
        """
        return list(cls._tools.keys())

    @classmethod
    def get_tools_by_type(cls, tool_type: Type) -> Dict[str, Any]:
        """
        Get all tools of a specific type.

        Args:
            tool_type: The type of tools to retrieve

        Returns:
            Dictionary of tool names to tool instances
        """
        return {name: tool for name, tool in cls._tools.items() if isinstance(tool, tool_type)}

    @classmethod
    def llm_choice_payload(cls) -> List[dict]:
        """
        Describe tools so the planner LLM can choose among them.

        Returns:
            List of tool descriptions
        """
        payload = []
        for name, tool in cls._tools.items():
            # Extract useful metadata from the tool
            # This will vary based on what tool classes provide
            tool_info = {
                "name": name,
                "type": tool.__class__.__name__,
            }

            # Add description if available
            if hasattr(tool, "description"):
                tool_info["description"] = tool.description

            payload.append(tool_info)
        return payload

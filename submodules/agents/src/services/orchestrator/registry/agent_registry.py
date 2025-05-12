"""
Minimal registry – stores real crewAI.Agent instances and exposes
metadata so the LLM can decide which one to use for each sub‑task.
"""

from __future__ import annotations
from typing import Dict, List
from crewai import Agent


class AgentRegistry:
    _agents: Dict[str, Agent] = {}

    # ------------------------------------------------------------------ #
    # registration helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def register(cls, name: str, agent: Agent) -> None:
        cls._agents[name] = agent

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    @classmethod
    def get(cls, name: str) -> Agent:
        return cls._agents[name]

    @classmethod
    def all_names(cls) -> List[str]:
        return list(cls._agents.keys())

    @classmethod
    def llm_choice_payload(cls) -> List[dict]:
        """Describe agents so the planner LLM can choose among them."""
        payload = []
        for name, ag in cls._agents.items():
            payload.append(
                {
                    "name": name,
                    "role": ag.role,
                    "goal": ag.goal,
                    "tools": [t.__class__.__name__ for t in ag.tools],
                }
            )
        return payload

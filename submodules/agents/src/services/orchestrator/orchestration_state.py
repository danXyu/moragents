# --------------------------------------------------------------------- #
# pydantic models for flow state & LLM tool schemas
# --------------------------------------------------------------------- #

from typing import List

from pydantic import BaseModel


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_prompt_tokens: int = 0


class ProcessingTime(BaseModel):
    start_time: float = 0
    end_time: float = 0
    duration: float = 0


class Telemetry(BaseModel):
    token_usage: TokenUsage = TokenUsage()
    processing_time: ProcessingTime = ProcessingTime()


class SubtaskOutput(BaseModel):
    subtask: str
    output: str
    agents: List[str]
    telemetry: Telemetry = Telemetry()


class SubtaskPlan(BaseModel):
    subtasks: List[str]


class Assignment(BaseModel):
    subtask: str
    agents: List[str]


class AssignmentPlan(BaseModel):
    assignments: List[Assignment]


class OrchestrationState(BaseModel):
    chat_prompt: str = ""
    chat_history: List[str] = []
    chat_history_summary: str = ""
    subtasks: List[str] = []
    assignments: List[Assignment] = []
    subtask_outputs: List[SubtaskOutput] = []
    final_answer: str | None = None

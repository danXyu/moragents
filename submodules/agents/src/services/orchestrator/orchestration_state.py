# --------------------------------------------------------------------- #
# pydantic models for flow state & LLM tool schemas
# --------------------------------------------------------------------- #

from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_prompt_tokens: int = 0

    class Config:
        # Ensure proper type coercion
        arbitrary_types_allowed = False


class ProcessingTime(BaseModel):
    start_time: float = 0
    end_time: float = 0
    duration: float = 0

    class Config:
        # Ensure proper type coercion
        arbitrary_types_allowed = False


class Telemetry(BaseModel):
    token_usage: TokenUsage = TokenUsage()
    processing_time: ProcessingTime = ProcessingTime()

    class Config:
        # Ensure proper type coercion
        arbitrary_types_allowed = False


class SubtaskOutput(BaseModel):
    subtask: str = ""
    output: str = ""
    agents: List[str] = []
    telemetry: Telemetry = Telemetry()

    class Config:
        # Ensure proper type coercion
        arbitrary_types_allowed = False


class SubtaskPlan(BaseModel):
    subtasks: List[str]


class Assignment(BaseModel):
    subtask: str
    agents: List[str]


class AssignmentPlan(BaseModel):
    assignments: List[Assignment]


class FinalAnswerActionType(str, Enum):
    TWEET = "tweet"
    SWAP = "swap"
    TRANSFER = "transfer"
    IMAGE_GENERATION = "image_generation"
    ANALYSIS = "analysis"


class FinalAnswerActionBaseMetadata(BaseModel):
    agent: str
    action_id: Optional[str] = None
    timestamp: Optional[int] = None


class TweetActionMetadata(FinalAnswerActionBaseMetadata):
    content: str
    hashtags: Optional[List[str]] = None
    image_url: Optional[str] = None


class SwapActionMetadata(FinalAnswerActionBaseMetadata):
    from_token: str
    to_token: str
    amount: str
    slippage: Optional[float] = None


class TransferActionMetadata(FinalAnswerActionBaseMetadata):
    token: str
    to_address: str
    amount: str


class ImageGenerationActionMetadata(FinalAnswerActionBaseMetadata):
    prompt: str
    negative_prompt: Optional[str] = None
    style: Optional[str] = None


class AnalysisActionMetadata(FinalAnswerActionBaseMetadata):
    type: str
    subject: str
    parameters: Optional[Dict[str, Any]] = None


# Union type for all action metadata types
FinalAnswerActionMetadata = Union[
    TweetActionMetadata, 
    SwapActionMetadata,
    TransferActionMetadata,
    ImageGenerationActionMetadata,
    AnalysisActionMetadata
]


class FinalAnswerAction(BaseModel):
    action_type: FinalAnswerActionType
    metadata: FinalAnswerActionMetadata
    description: Optional[str] = None


# List of supported final answer actions
SUPPORTED_FINAL_ANSWER_ACTIONS = [
    {
        "type": FinalAnswerActionType.TWEET,
        "name": "Tweet",
        "description": "Create and share a tweet",
        "agent": "tweet_sizzler",
    },
    {
        "type": FinalAnswerActionType.SWAP,
        "name": "Token Swap",
        "description": "Swap one token for another",
        "agent": "token_swap",
    },
    {
        "type": FinalAnswerActionType.TRANSFER,
        "name": "Token Transfer",
        "description": "Transfer tokens to an address",
        "agent": "token_swap",
    },
    {
        "type": FinalAnswerActionType.IMAGE_GENERATION,
        "name": "Generate Image",
        "description": "Generate an image based on a prompt",
        "agent": "imagen",
    },
    {
        "type": FinalAnswerActionType.ANALYSIS,
        "name": "Analysis",
        "description": "Analyze tokens, wallets, or trades",
        "agent": "codex",
    },
]


class OrchestrationState(BaseModel):
    chat_prompt: str = ""
    chat_history: List[str] = []
    chat_history_summary: str = ""
    subtasks: List[str] = []
    assignments: List[Assignment] = []
    subtask_outputs: List[SubtaskOutput] = []
    final_answer: str | None = None
    final_answer_actions: List[FinalAnswerAction] = []

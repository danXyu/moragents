import json
import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

from config import TOGETHER_CLIENT
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from models.service.chat_models import AgentResponse, ChatRequest
from pydantic import BaseModel, Field

T = TypeVar("T")


class ToolCall(BaseModel):
    """Model for a tool call from an LLM."""

    name: str = Field(..., description="The name of the tool to call")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool call")


class LLMResponse(BaseModel):
    """Structured response format for LLM output."""

    content: Optional[str] = Field(None, description="Direct text response if no tool is used")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls to execute")


def handle_exceptions(func: Callable[..., Awaitable[AgentResponse]]) -> Callable[..., Awaitable[AgentResponse]]:
    """Decorator to handle exceptions uniformly across agent methods"""

    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> AgentResponse:
        try:
            return await func(self, *args, **kwargs)
        except ValueError as e:
            # Handle validation errors - these are expected and should return as needs_info
            self.logger.info(f"Validation error in {func.__name__}: {str(e)}")
            return AgentResponse.error(error_message=str(e))
        except Exception as e:
            # Handle unexpected errors - these are breaking errors
            self.logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message="An unexpected error occurred. Please try again later.")

    return wrapper


class AgentCore(ABC):
    """Enhanced core agent functionality that all specialized agents inherit from."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._setup_logging()
        self.together_client = TOGETHER_CLIENT
        self.model = self.config.get("llm_model", "meta-llama/Llama-3.3-70B-Instruct-Turbo")

    def _setup_logging(self) -> None:
        """Set up logging for the agent"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def _validate_request(self, request: ChatRequest) -> Optional[AgentResponse]:
        """Validate common request parameters and return appropriate response type"""
        if not request.prompt:
            return AgentResponse.error(error_message="Please provide a prompt to process your request")

        return None

    @handle_exceptions
    async def chat(self, request: ChatRequest) -> AgentResponse:
        """Main entry point for chat interactions"""
        self.logger.info(f"Received chat request: {request}")

        # Validate request
        validation_result = await self._validate_request(request)
        if validation_result:
            return validation_result

        # Process the request
        response = await self._process_request(request)

        # Log response for monitoring
        if response.error_message:
            self.logger.warning(f"Response error: {response.error_message}")

        return response

    def _convert_tools_for_api(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Together API format for function calling"""
        api_tools = []

        for tool in tools:
            api_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            api_tools.append(api_tool)

        return api_tools

    @abstractmethod
    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """
        Process the validated request. Must be implemented by subclasses.

        Args:
            request: Validated ChatRequest object

        Returns:
            AgentResponse: Response containing content and optional error/metadata
        """
        raise NotImplementedError("Subclasses must implement _process_request")

    async def _call_llm_with_tools(
        self, messages: List[Union[SystemMessage, HumanMessage, AIMessage]], tools: List[Dict[str, Any]]
    ) -> LLMResponse:
        """Call LLM with tools using Together API"""
        try:
            # Convert tools to Together API format
            api_tools = self._convert_tools_for_api(tools)

            # Convert messages to Together API format
            together_messages = []
            for message in messages:
                if isinstance(message, dict):
                    # Already in Together format
                    together_messages.append(message)
                elif isinstance(message, SystemMessage):
                    together_messages.append({"role": "system", "content": message.content})
                elif isinstance(message, HumanMessage):
                    together_messages.append({"role": "user", "content": message.content})
                elif isinstance(message, AIMessage):
                    together_messages.append({"role": "assistant", "content": message.content})

            # Call the Together API
            response = self.together_client.chat.completions.create(
                model=self.model,
                messages=together_messages,
                tools=api_tools,
                temperature=0.7,
            )

            # Check if there are tool calls
            if response.choices[0].message.tool_calls:
                tool_calls = []
                for tool_call in response.choices[0].message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    tool_calls.append(ToolCall(name=tool_call.function.name, args=args))

                return LLMResponse(content=None, tool_calls=tool_calls)
            else:
                # Return content response
                return LLMResponse(content=response.choices[0].message.content, tool_calls=None)

        except Exception as e:
            self.logger.error(f"Error calling Together API: {str(e)}")
            raise

    async def _handle_llm_response(self, response: LLMResponse) -> AgentResponse:
        """Handle LLM response and convert to appropriate AgentResponse"""
        try:
            # Check for tool calls first
            if response.tool_calls and len(response.tool_calls) > 0:
                # Handle tool calls
                self.logger.info(f"Processing tool calls: {response.tool_calls}")
                return await self._process_tool_calls(response.tool_calls)
            elif response.content:
                # Direct response from LLM
                self.logger.info(f"Received direct response from LLM: {response.content}")
                return AgentResponse.success(content=response.content)
            else:
                self.logger.warning("Received invalid response format from LLM")
                return AgentResponse.error(error_message="Received invalid response format from LLM")

        except Exception as e:
            self.logger.error(f"Error processing LLM response: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message="Error processing the response")

    async def _process_tool_calls(self, tool_calls: List[ToolCall]) -> AgentResponse:
        """Process tool calls from LLM response"""
        try:
            tool_call = tool_calls[0]  # Get first tool call
            func_name = tool_call.name
            args = tool_call.args

            if not func_name:
                return AgentResponse.error(error_message="Invalid tool call format - no function name provided")

            # Execute tool and handle response
            return await self._execute_tool(func_name, args)

        except Exception as e:
            self.logger.error(f"Error processing tool calls: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message="Error executing the requested action")

    @abstractmethod
    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute a tool with given arguments. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _execute_tool")

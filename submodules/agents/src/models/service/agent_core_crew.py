import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

from crewai import Agent as CrewAgent
from crewai import Crew, Process, Task
from crewai.tools import Tool as CrewTool
from models.service.chat_models import AgentResponse, ChatRequest

T = TypeVar("T")


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


class CrewAgentCore(ABC):
    """Enhanced core agent functionality using CrewAI framework."""

    def __init__(self, config: Dict[str, Any], llm: Any):
        self.config = config
        self.llm = llm
        self._setup_logging()
        self._setup_crew_agent()
        self._setup_tools()

    def _setup_logging(self) -> None:
        """Set up logging for the agent"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _setup_crew_agent(self) -> None:
        """Set up the CrewAI agent"""
        agent_name = self.__class__.__name__
        agent_role = self.config.get("role", agent_name)
        agent_goal = self.config.get("goal", f"Process {agent_name} related requests accurately")
        agent_backstory = self.config.get(
            "backstory", f"You are a specialized {agent_name} with expertise in your domain."
        )

        self.crew_agent = CrewAgent(
            role=agent_role, goal=agent_goal, backstory=agent_backstory, verbose=True, llm=self.llm
        )

    def _setup_tools(self) -> None:
        """Set up tools for the CrewAI agent"""
        self.crew_tools = self._create_tools()

        # Add tools to the agent
        if self.crew_tools:
            for tool in self.crew_tools:
                self.crew_agent.add_tool(tool)

    @abstractmethod
    def _create_tools(self) -> List[CrewTool]:
        """Create and return CrewAI tools for this agent"""
        return []

    async def _validate_request(self, request: ChatRequest) -> Optional[AgentResponse]:
        """Validate common request parameters and return appropriate response type"""
        if not request.prompt:
            return AgentResponse.error(error_message="Please provide a prompt to process your request")

        return None

    @handle_exceptions
    async def process_request(self, request: ChatRequest) -> AgentResponse:
        """Main entry point for processing requests"""
        self.logger.info(f"Received request: {request}")

        # Validate request
        validation_result = await self._validate_request(request)
        if validation_result:
            return validation_result

        # Process the request using CrewAI
        return await self.process_with_crew(request)

    async def process_with_crew(self, request: ChatRequest) -> AgentResponse:
        """Process request using CrewAI framework"""
        try:
            # Create a task for the agent
            task = Task(
                description=self._create_task_description(request),
                agent=self.crew_agent,
                context={"request": request.dict()},
            )

            # Create a crew with just this agent
            crew = Crew(agents=[self.crew_agent], tasks=[task], verbose=True, process=Process.sequential)

            # Execute the task
            result = crew.kickoff()

            # Process result
            return self._process_result(result, request)

        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    def _create_task_description(self, request: ChatRequest) -> str:
        """Create a task description based on the request"""
        system_prompt = self.config.get("system_message", {}).get("content", "")

        return f"""
        {system_prompt}

        Process the following user request and provide a helpful response:
        "{request.prompt}"

        If you need to use tools, use them to gather information before responding.
        Return your final answer in a clear, helpful format.
        """

    @abstractmethod
    async def _process_result(self, result: str, request: ChatRequest) -> AgentResponse:
        """Process the result from CrewAI execution"""
        # Base implementation - can be overridden by subclasses
        return AgentResponse.success(content=result)


class CrewAIAgent:
    """
    Adapter for converting existing agents to be compatible with CrewAI.
    This adapter implements the interface expected by the CrewAI Orchestrator.
    """

    def __init__(self, agent_implementation: Any):
        """
        Initialize with an existing agent implementation

        Args:
            agent_implementation: The original agent instance
        """
        self.agent = agent_implementation

    async def process_request(self, request: ChatRequest) -> AgentResponse:
        """
        Process a request using the underlying agent implementation

        Args:
            request: The ChatRequest to process

        Returns:
            AgentResponse: The response from the agent
        """
        # Delegate to the appropriate method based on the agent implementation
        if hasattr(self.agent, "process_request"):
            return await self.agent.process_request(request)
        elif hasattr(self.agent, "chat"):
            return await self.agent.chat(request)
        elif hasattr(self.agent, "ainvoke"):
            return await self.agent.ainvoke(request)
        else:
            # Fallback
            return AgentResponse.error(
                error_message="Agent implementation doesn't support any known request processing method"
            )

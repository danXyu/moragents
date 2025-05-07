import logging
from typing import Any, Dict, List, Optional, Tuple

from crewai import Agent, Crew, Process, Task
from crewai.crew import CrewOutput
from crewai_tools import BraveSearchTool, SeleniumScrapingTool

from models.service.chat_models import AgentResponse, ChatRequest, ChatMessage
from services.agents.crypto_data.basic_crew_agent import crypto_data_agent


logger = logging.getLogger(__name__)


class BasicOrchestrator:
    """
    A basic implementation of the orchestrator pattern using CrewAI.
    Creates a crew with various agents including crypto data, web search, and web scraping.
    """

    def __init__(self, llm_router: Any):
        """
        Initialize the basic CrewAI orchestrator.

        Args:
            llm_router: The language model to use for agents that don't have their own LLM defined
        """
        self.llm_router = llm_router
        self._setup_tools()
        self._setup_agents()

    def _setup_tools(self):
        """Setup the tools used by the agents"""
        try:
            # Web search tool
            self.search_tool = BraveSearchTool()

            # Web scraping tool
            self.scraper_tool = SeleniumScrapingTool()
        except Exception as e:
            logger.error(f"Error setting up tools: {str(e)}")
            logger.error("If using BraveSearchTool, make sure BRAVE_API_KEY is set in environment variables")
            logger.error("If using SeleniumScrapingTool, make sure Chrome and selenium are installed")

            # Fallback to empty tools list if tools can't be initialized
            self.search_tool = None
            self.scraper_tool = None

    def _setup_agents(self):
        """Setup the agents that will be part of the crew"""
        # Web search agent
        self.search_agent = self._create_search_agent()

        # Web scraping agent
        self.scraper_agent = self._create_scraper_agent()

        # Research agent
        self.research_agent = self._create_research_agent()

    def _create_search_agent(self):
        """Create a web search agent"""
        tools = [self.search_tool] if self.search_tool else []

        return Agent(
            role="Internet Search Specialist",
            goal="Find relevant and up-to-date information online",
            backstory="An expert at finding information online using search engines and analyzing results.",
            verbose=True,
            tools=tools,
            llm=self.llm_router,
            allow_delegation=True,
        )

    def _create_scraper_agent(self):
        """Create a web scraping agent"""
        tools = [self.scraper_tool] if self.scraper_tool else []

        return Agent(
            role="Web Content Analyst",
            goal="Extract and analyze content from websites",
            backstory="A specialist in extracting valuable information from websites and processing it for analysis.",
            verbose=True,
            tools=tools,
            llm=self.llm_router,
            allow_delegation=True,
        )

    def _create_research_agent(self):
        """Create a research agent that coordinates between search and scraping"""
        tools = []
        if self.search_tool:
            tools.append(self.search_tool)
        if self.scraper_tool:
            tools.append(self.scraper_tool)

        return Agent(
            role="Research Coordinator",
            goal="Coordinate research efforts and synthesize information",
            backstory="An experienced researcher who excels at coordinating different information sources and synthesizing findings into coherent insights.",
            verbose=True,
            tools=tools,
            llm=self.llm_router,
            allow_delegation=True,
        )

    def _create_task_for_agent(self, agent, prompt: str, chat_history: Optional[List[ChatMessage]] = None):
        """Create a task for a specific agent"""
        # Format chat history for context if provided
        chat_history_text = ""
        if chat_history:
            chat_history_formatted = []
            for msg in chat_history:
                chat_history_formatted.append(f"{msg.role.upper()}: {msg.content}")
            chat_history_text = "\n".join(chat_history_formatted)

        task_description = f"""
        Analyze and respond to the following request:
        
        {prompt}
        
        {"CHAT HISTORY:\n" + chat_history_text if chat_history_text else ""}
        
        Provide a detailed and accurate response based on your expertise.
        """

        return Task(
            description=task_description,
            agent=agent,
            expected_output="A detailed response addressing the user's query",
        )

    async def orchestrate(self, chat_request: ChatRequest) -> Tuple[Optional[str], AgentResponse]:
        """
        Orchestrate the crew to handle the chat request.

        Args:
            chat_request: The chat request to process

        Returns:
            Tuple of (agent_name, AgentResponse)
        """
        try:
            # Extract the prompt and chat history
            prompt = chat_request.prompt.content
            chat_history = chat_request.chat_history

            # Create tasks for each agent
            tasks = []

            # Crypto data task
            crypto_task = self._create_task_for_agent(crypto_data_agent, prompt, chat_history)
            tasks.append(crypto_task)

            # Search task
            search_task = self._create_task_for_agent(self.search_agent, prompt, chat_history)
            tasks.append(search_task)

            # Research coordination task (includes potential scraping)
            research_task = self._create_task_for_agent(self.research_agent, prompt, chat_history)
            tasks.append(research_task)

            # Create the crew with hierarchical process to enable collaboration
            crew = Crew(
                agents=[crypto_data_agent, self.search_agent, self.scraper_agent, self.research_agent],
                tasks=tasks,
                verbose=True,
                process=Process.hierarchical,
                manager_llm=self.llm_router,
                memory=True,
            )

            # Execute the crew to get the result - properly typed as CrewOutput
            crew_output: CrewOutput = crew.kickoff()

            # Extract the raw output as a string directly from the CrewOutput
            result_content = str(crew_output.raw)

            # Create metadata dictionary with contributing agents
            metadata: Dict[str, Any] = {
                "collaboration": "true",
                "contributing_agents": ["crypto_data", "search", "scraper", "research"],
            }

            # Add token usage directly from the CrewOutput
            if crew_output.token_usage:
                metadata["token_usage"] = crew_output.token_usage

            # Process task outputs if they exist
            if crew_output.tasks_output:
                # Create a list of task summary dictionaries
                task_summaries = []
                for i, task_output in enumerate(crew_output.tasks_output):
                    task_result = str(task_output.raw)
                    task_summaries.append(
                        {
                            "task_index": i,
                            "output_length": len(task_result),
                            "output_preview": task_result,
                        }
                    )

                # Add to metadata (properly typed as Any)
                metadata["task_summaries"] = task_summaries

            # Return the successful response with the raw content and metadata
            return "basic_crew", AgentResponse.success(content=result_content, metadata=metadata)

        except Exception as e:
            logger.error(f"Error in basic crew orchestration: {str(e)}", exc_info=True)
            return None, AgentResponse.error(error_message=f"Error in crew processing: {str(e)}")

    async def cleanup(self):
        """Clean up resources when the orchestrator is no longer needed"""
        try:
            # No specific cleanup needed for this basic implementation
            logger.info("Basic orchestrator cleanup completed")
        except Exception as e:
            logger.error(f"Error during basic orchestrator cleanup: {str(e)}", exc_info=True)

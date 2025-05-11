import logging
from typing import Any, Dict, List, Optional, Tuple

from crewai import Agent, Crew, Process, Task
from crewai.crew import CrewOutput
from crewai_tools import BraveSearchTool, SeleniumScrapingTool, ApifyActorsTool

from models.service.chat_models import AgentResponse, ChatRequest, ChatMessage
from services.agents.crypto_data.basic_crew_agent import crypto_data_agent


logger = logging.getLogger(__name__)


class BasicOrchestrator:
    """
    A basic implementation of the orchestrator pattern using CrewAI.
    Creates a crew with various agents including crypto data, web search, web scraping, and Instagram scraping.

    This orchestrator features an Instagram crawler agent built with Apify's instagram-scraper.
    It can extract data from Instagram profiles, posts, hashtags, and comments.

    To enable the Instagram scraper functionality:
    1. Sign up for Apify at https://console.apify.com/sign-up
    2. Get your API token from the Apify Console
    3. Set the environment variable: APIFY_API_TOKEN=your_token_here

    The Instagram agent is automatically included when a chat request contains
    Instagram-related keywords such as "instagram", "ig", "insta", "social media",
    "profile", "hashtag", "followers".
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

            # Instagram scraping tool (using Apify)
            self.instagram_tool = ApifyActorsTool(actor_name="apify/instagram-scraper")
        except Exception as e:
            logger.error(f"Error setting up tools: {str(e)}")
            logger.error("If using BraveSearchTool, make sure BRAVE_API_KEY is set in environment variables")
            logger.error("If using SeleniumScrapingTool, make sure Chrome and selenium are installed")
            logger.error("If using ApifyActorsTool, make sure APIFY_API_TOKEN is set in environment variables")

            # Fallback to empty tools list if tools can't be initialized
            self.search_tool = None
            self.scraper_tool = None
            self.instagram_tool = None

    def _setup_agents(self):
        """Setup the agents that will be part of the crew"""
        # Web search agent
        # self.search_agent = self._create_search_agent()

        # Web scraping agent
        # self.scraper_agent = self._create_scraper_agent()

        # Research agent
        self.research_agent = self._create_research_agent()

        # Instagram scraper agent
        self.instagram_agent = self._create_instagram_agent()

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

    def _create_instagram_agent(self):
        """Create an Instagram scraping agent using Apify's instagram-scraper"""
        tools = [self.instagram_tool] if self.instagram_tool else []

        return Agent(
            role="Instagram Data Specialist",
            goal="Extract and analyze content from Instagram profiles, posts, and hashtags",
            backstory="A social media expert specializing in Instagram data extraction and analysis. Skilled at gathering profiles, posts, comments, and engagement metrics from Instagram.",
            verbose=True,
            tools=tools,
            llm=self.llm_router,
            allow_delegation=True,
        )

    def _create_task_for_request(self, prompt: str, chat_history: Optional[List[ChatMessage]] = None):
        """Create a main task for the crew to handle the request"""
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
        
        Determine which agents would be best suited to handle this request and delegate accordingly.
        Coordinate between agents to gather all necessary information.
        Synthesize the information into a comprehensive response.
        
        Provide a detailed and accurate response based on the collective expertise of the crew.
        """

        return Task(
            description=task_description,
            expected_output="A detailed response addressing the user's query",
            agent=self.instagram_agent,
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

            # Create a single main task for the crew
            main_task = self._create_task_for_request(prompt, chat_history)

            # Determine which agents to include in the crew
            agents = [self.instagram_agent]

            # Add Instagram agent conditionally based on keywords
            # instagram_keywords = ["instagram", "ig", "insta", "social media", "profile", "hashtag", "followers"]
            # instagram_relevant = any(keyword in prompt.lower() for keyword in instagram_keywords)
            # if instagram_relevant:
            #     agents.append(self.instagram_agent)

            # Create the crew with hierarchical process to enable collaboration
            crew = Crew(
                agents=agents,
                tasks=[main_task],
                verbose=True,
                process=Process.hierarchical,
                manager_llm=self.llm_router,
                memory=True,
            )

            # Execute the crew to get the result - properly typed as CrewOutput
            crew_output: CrewOutput = crew.kickoff()

            # Extract the raw output as a string directly from the CrewOutput
            result_content = str(crew_output.raw)

            # Track which agents were actually used in the tasks
            used_agent_names = set()

            # Process task outputs to determine which agents were used
            if crew_output.tasks_output:
                for task_output in crew_output.tasks_output:
                    if hasattr(task_output, "agent") and task_output.agent:
                        # Add the agent's role to the set of used agents
                        if "Research Coordinator" in task_output.agent:
                            used_agent_names.add("orchestrator_agent")
                        elif "Internet Search" in task_output.agent:
                            used_agent_names.add("brave_search_agent")
                        elif "Web Content Analyst" in task_output.agent:
                            used_agent_names.add("puppeteer_scraper_agent")
                        elif "Instagram Data" in task_output.agent:
                            used_agent_names.add("instagram_scraper_agent")
                        elif "Crypto" in task_output.agent:
                            used_agent_names.add("crypto_data_agent")

            # Create metadata dictionary with contributing agents that were actually used
            contributing_agents = list(used_agent_names)

            # Ensure the research agent is always included as it coordinates the response
            if "orchestrator_agent" not in contributing_agents:
                contributing_agents.append("orchestrator_agent")
                contributing_agents.append("brave_search_agent")
                contributing_agents.append("crypto_data_agent")

            metadata: Dict[str, Any] = {
                "collaboration": "true",
                "contributing_agents": contributing_agents,
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

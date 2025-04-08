import logging
from typing import Any, Dict, List, Optional, Tuple
from crewai import Crew, Agent, Task, Process
from crewai.agent import Agent as CrewAgent
from crewai.task import Task as CrewTask
from pydantic import BaseModel, Field

from stores import agent_manager_instance
from models.service.chat_models import AgentResponse, ChatRequest, ResponseType, ChatMessage
from services.orchestrator.system_prompt import get_system_prompt


logger = logging.getLogger(__name__)


class Orchestrator:
    """
    True multi-agent orchestrator using CrewAI for collaborative problem-solving.
    This implementation allows agents to work together, share information, and delegate tasks.
    """

    def __init__(self, llm_router: Any):
        """
        Initialize the multi-agent orchestrator with a primary LLM.

        Args:
            llm_router: The LLM to use for agents that don't have their own LLM defined
        """
        self.llm_router = llm_router
        self.crew_agents_cache = {}  # Cache CrewAI agents to avoid recreating them

    def _create_crew_agent_from_impl(self, agent_name: str, agent_impl: Any) -> CrewAgent:
        """Create a CrewAI agent from an existing agent implementation"""

        # Get LLM from the agent if available, otherwise use the router LLM
        agent_llm = getattr(agent_impl, "llm", self.llm_router)

        # Get configuration if available
        agent_config = getattr(agent_impl, "config", {})
        agent_description = agent_config.get("description", f"A specialized {agent_name} agent")

        # Create the wrapper function to execute the agent implementation
        async def execute_agent_func(context):
            try:
                # Format the input for our agent implementation
                prompt = context.get("prompt", str(context))

                # Create a chat request from the context
                chat_message = ChatMessage(role="user", content=prompt)
                request = ChatRequest(
                    prompt=chat_message,
                    chain_id="crew_collaboration",
                    wallet_address="crew_collaboration",
                    conversation_id="crew_collaboration",
                    # Add any chat history that might be in the context
                    chat_history=context.get("chat_history", []),
                )

                # Process using the appropriate method
                if hasattr(agent_impl, "process_with_crew"):
                    result = await agent_impl.process_with_crew(request)
                elif hasattr(agent_impl, "chat"):
                    result = await agent_impl.chat(request)
                elif hasattr(agent_impl, "process_request"):
                    result = await agent_impl.process_request(request)
                else:
                    return f"Agent {agent_name} does not support any known request processing method"

                # Return the content as a string
                return result.content if hasattr(result, "content") else str(result)

            except Exception as e:
                logger.error(f"Error executing agent {agent_name}: {str(e)}")
                return f"Error from {agent_name} agent: {str(e)}"

        # Create a CrewAI Agent
        return Agent(
            name=agent_name,
            role=agent_config.get("role", f"{agent_name} Expert"),
            goal=agent_config.get("goal", f"Provide expert {agent_name} analysis and solutions"),
            backstory=agent_description,
            verbose=True,
            llm=agent_llm,
            tools=[execute_agent_func],
            allow_delegation=True,  # Enable agent delegation for collaboration
        )

    def _get_crew_agent(self, agent_name: str) -> Optional[CrewAgent]:
        """Get (or create) a CrewAI agent for a given agent name"""

        # Check cache first
        if agent_name in self.crew_agents_cache:
            return self.crew_agents_cache[agent_name]

        # Get the agent implementation from the agent manager
        agent_impl = agent_manager_instance.get_agent(agent_name)

        if not agent_impl:
            logger.warning(f"Agent {agent_name} not found in agent manager")
            return None

        # Create a new CrewAI agent
        crew_agent = self._create_crew_agent_from_impl(agent_name, agent_impl)

        # Cache it for future use
        self.crew_agents_cache[agent_name] = crew_agent

        return crew_agent

    def _create_tasks_for_request(self, request: ChatRequest) -> List[CrewTask]:
        """Create collaborative tasks for the agents based on the request"""

        # Extract the prompt
        prompt = request.prompt.content

        # Format chat history for context
        chat_history_formatted = []
        for msg in request.chat_history:
            chat_history_formatted.append(f"{msg.role.upper()}: {msg.content}")

        chat_history_text = "\n".join(chat_history_formatted)

        # Get available agents
        available_agents = agent_manager_instance.get_available_agents()

        # Create crew agents for each available agent
        crew_agents = {}
        for agent_name in available_agents:
            crew_agent = self._get_crew_agent(agent_name)
            if crew_agent:
                crew_agents[agent_name] = crew_agent

        if not crew_agents:
            logger.error("No agents available to create tasks")
            return []

        # Create task descriptions based on agent specialties
        tasks = []

        # If we have a crypto agent, create a task for it
        if "crypto" in crew_agents:
            tasks.append(
                Task(
                    description=f"""
                Analyze this request from a crypto perspective:
                
                CHAT HISTORY:
                {chat_history_text}
                
                CURRENT REQUEST:
                {prompt}
                
                If this involves cryptocurrency prices, market caps, NFTs, or blockchain data,
                use your specialized tools to provide accurate information.
                """,
                    agent=crew_agents["crypto"],
                    expected_output="A detailed analysis of any crypto-related aspects of the request",
                )
            )

        # If we have an MCP agent, create a task for it
        if "mcp" in crew_agents:
            tasks.append(
                Task(
                    description=f"""
                Analyze this request for external data needs:
                
                CHAT HISTORY:
                {chat_history_text}
                
                CURRENT REQUEST:
                {prompt}
                
                If this requires accessing external data sources or APIs, 
                use your specialized tools to retrieve and process that data.
                """,
                    agent=crew_agents["mcp"],
                    expected_output="Any relevant external data that could help solve the request",
                )
            )

        # Always add a coordination task (using default agent if available, otherwise first agent)
        coordinator_agent = crew_agents.get("default", next(iter(crew_agents.values())))
        tasks.append(
            Task(
                description=f"""
            Coordinate the response to this user request:
            
            CHAT HISTORY:
            {chat_history_text}
            
            CURRENT REQUEST:
            {prompt}
            
            Consider all information gathered by other agents and synthesize a 
            comprehensive and accurate response for the user.
            """,
                agent=coordinator_agent,
                expected_output="A final, coherent response that addresses all aspects of the user's request",
            )
        )

        return tasks

    async def orchestrate(self, chat_request: ChatRequest) -> Tuple[Optional[str], AgentResponse]:
        """
        Main entry point for the CrewAI orchestrator.
        Creates a collaborative crew of agents to solve the request together.

        Args:
            chat_request: The chat request to process

        Returns:
            Tuple of (agent_name, AgentResponse)
        """
        try:
            # Create tasks for the request
            tasks = self._create_tasks_for_request(chat_request)

            if not tasks:
                logger.error("No tasks could be created - no suitable agents available")
                return None, AgentResponse.error(error_message="No suitable agents available to process your request")

            # Get all agents involved in tasks
            agents = list({task.agent for task in tasks})

            # Create a crew with hierarchical process to allow for agent delegation
            crew = Crew(
                agents=agents,
                tasks=tasks,
                verbose=True,
                process=Process.hierarchical,  # Enable hierarchical collaboration
                manager_llm=self.llm_router,  # LLM for the crew manager
                memory=True,  # Enable memory for inter-agent communication
            )

            # Execute the crew
            result = crew.kickoff()

            # Find which agent contributed the final answer
            # (typically the coordinator/default agent)
            contributing_agent = "default"
            if len(tasks) > 0:
                contributing_agent = tasks[-1].agent.name

            # Convert the result to an AgentResponse
            return contributing_agent, AgentResponse.success(
                content=result, metadata={"collaboration": "true", "contributing_agents": [a.name for a in agents]}
            )

        except Exception as e:
            logger.error(f"Error in crew orchestration: {str(e)}")
            return None, AgentResponse.error(error_message=f"Error in multi-agent processing: {str(e)}")

    async def cleanup(self):
        """Clean up resources when the orchestrator is no longer needed"""
        # Clean up any agent resources
        for agent_name in agent_manager_instance.get_available_agents():
            agent = agent_manager_instance.get_agent(agent_name)

            # Check if the agent has a cleanup method
            if hasattr(agent, "cleanup") and callable(agent.cleanup):
                try:
                    await agent.cleanup()
                    logger.info(f"Successfully cleaned up agent {agent_name}")
                except Exception as e:
                    logger.error(f"Error cleaning up agent {agent_name}: {str(e)}")

        # Clear the agent cache
        self.crew_agents_cache.clear()

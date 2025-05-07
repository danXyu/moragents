import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from crewai import Crew, Agent, Task, Process
from crewai.agent import Agent as CrewAgent
from crewai.task import Task as CrewTask
from pydantic import BaseModel, Field

from stores.agent_manager import agent_manager_instance
from models.service.chat_models import AgentResponse, ChatRequest, ResponseType, ChatMessage
from services.orchestrator.system_prompt import get_system_prompt


logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Pydantic model for agent configuration to ensure proper serialization"""

    name: str
    role: str = ""
    goal: str = ""
    backstory: str = ""
    description: str = ""


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
        # Use a dictionary with string keys to prevent unhashable type errors
        self.crew_agents_cache: Dict[str, CrewAgent] = {}

    def _create_crew_agent_from_impl(self, agent_name: str, agent_impl: Any) -> CrewAgent:
        """Create a CrewAI agent from an existing agent implementation"""
        try:
            # Get LLM from the agent if available, otherwise use the router LLM
            agent_llm = getattr(agent_impl, "llm", self.llm_router)

            # Get configuration if available
            agent_config = getattr(agent_impl, "config", {})

            # If agent_config is unhashable (dict), convert key portions to a Pydantic model
            agent_role = (
                agent_config.get("role", f"{agent_name} Expert")
                if isinstance(agent_config, dict)
                else f"{agent_name} Expert"
            )
            agent_goal = (
                agent_config.get("goal", f"Provide expert {agent_name} analysis and solutions")
                if isinstance(agent_config, dict)
                else f"Provide expert {agent_name} analysis and solutions"
            )
            agent_description = (
                agent_config.get("description", f"A specialized {agent_name} agent")
                if isinstance(agent_config, dict)
                else f"A specialized {agent_name} agent"
            )

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

            # Create a CrewAI Agent with only necessary attributes to reduce chance of serialization issues
            return Agent(
                name=agent_name,
                role=agent_role,
                goal=agent_goal,
                backstory=agent_description,
                verbose=True,
                llm=agent_llm,
                tools=[execute_agent_func],
                allow_delegation=True,  # Enable agent delegation for collaboration
            )
        except Exception as e:
            logger.error(f"Error creating CrewAI agent for {agent_name}: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise

    def _get_crew_agent(self, agent_name: Any) -> Optional[CrewAgent]:
        """
        Get (or create) a CrewAI agent for a given agent name.
        Handles potential unhashable agent_name by converting to string.

        Args:
            agent_name: The agent name or identifier (string or dictionary)

        Returns:
            Optional[CrewAgent]: The CrewAI agent or None if not found
        """
        try:
            # Ensure we have a hashable key for the cache
            cache_key = str(agent_name)
            if isinstance(agent_name, dict):
                # If it's a dict, try to extract the name or a unique identifier
                cache_key = str(agent_name.get("name", id(agent_name)))

            # Check if we already have this agent in the cache
            if cache_key in self.crew_agents_cache:
                logger.debug(f"Using cached agent for key {cache_key}")
                return self.crew_agents_cache[cache_key]

            # Get the agent implementation from the manager
            if isinstance(agent_name, dict):
                # If agent_name is a dict, try to extract its name
                name_to_get = agent_name.get("name", str(id(agent_name)))
            else:
                name_to_get = agent_name

            agent_impl = agent_manager_instance.get_agent(name_to_get)

            if not agent_impl:
                logger.warning(f"Agent {name_to_get} not found in agent manager")
                return None

            # Create a new CrewAI agent
            agent_name_str = str(name_to_get)  # Ensure we have a string
            crew_agent = self._create_crew_agent_from_impl(agent_name_str, agent_impl)

            # Cache it using the string key
            self.crew_agents_cache[cache_key] = crew_agent

            return crew_agent

        except Exception as e:
            logger.error(f"Error in _get_crew_agent: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return None

    def _create_tasks_for_request(self, request: ChatRequest) -> List[CrewTask]:
        """Create collaborative tasks for the agents based on the request"""
        try:
            # Extract the prompt
            prompt = request.prompt.content

            # Format chat history for context
            chat_history_formatted = []
            for msg in request.chat_history:
                chat_history_formatted.append(f"{msg.role.upper()}: {msg.content}")

            chat_history_text = "\n".join(chat_history_formatted)

            # Get available agents
            available_agents = agent_manager_instance.get_available_agents()
            logger.info(f"Available agents: {available_agents}")

            # Create crew agents for each available agent
            crew_agents: Dict[str, CrewAgent] = {}
            for agent_name in available_agents:
                try:
                    crew_agent = self._get_crew_agent(agent_name)
                    if crew_agent:
                        # Use string keys to avoid unhashable type errors
                        key = getattr(crew_agent, "name", str(id(crew_agent)))
                        crew_agents[key] = crew_agent
                except Exception as e:
                    logger.error(f"Error creating agent {agent_name}: {str(e)}")
                    # Continue with other agents

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
            coordinator_key = "default"
            if coordinator_key not in crew_agents and crew_agents:
                # Take the first available agent if default is not available
                coordinator_key = next(iter(crew_agents.keys()))

            coordinator_agent = crew_agents[coordinator_key]
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

        except Exception as e:
            logger.error(f"Error creating tasks: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return []

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
            # Using a dictionary with string keys to ensure no unhashable type errors
            unique_agents: Dict[str, CrewAgent] = {}
            for task in tasks:
                try:
                    # Extract a string key that uniquely identifies this agent
                    agent_id = str(id(task.agent))  # Fallback to object id
                    if hasattr(task.agent, "name"):
                        agent_id = task.agent.name

                    # Store in our dictionary of unique agents
                    unique_agents[agent_id] = task.agent
                except Exception as e:
                    logger.error(f"Error extracting agent from task: {str(e)}")
                    # Continue to next task

            # Convert to list for CrewAI
            agents = list(unique_agents.values())

            if not agents:
                logger.error("No valid agents could be extracted from tasks")
                return None, AgentResponse.error(error_message="Failed to extract agents from tasks")

            # Log agent information for debugging
            logger.info(f"Creating crew with {len(agents)} agents and {len(tasks)} tasks")
            for i, agent in enumerate(agents):
                logger.info(f"Agent {i}: {type(agent)} - {getattr(agent, 'name', 'unknown')}")

            # Create a crew with hierarchical process to allow for agent delegation
            try:
                crew = Crew(
                    agents=agents,
                    tasks=tasks,
                    verbose=True,
                    process=Process.hierarchical,  # Enable hierarchical collaboration
                    manager_llm=self.llm_router,  # LLM for the crew manager
                    memory=True,  # Enable memory for inter-agent communication
                )
            except TypeError as te:
                logger.error(f"TypeError when creating Crew: {str(te)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")

                # Special handling for unhashable type errors
                if "unhashable type" in str(te):
                    logger.error(
                        "Detected unhashable type error - attempting to recreate agents with minimal properties"
                    )

                    # Try to create simplified agents
                    simplified_agents = []
                    for agent in agents:
                        try:
                            # Create basic agent with minimal properties
                            new_agent = Agent(
                                name=getattr(agent, "name", f"agent_{id(agent)}"),
                                role=getattr(agent, "role", "Expert"),
                                goal=getattr(agent, "goal", "Solve problems"),
                                backstory=getattr(agent, "backstory", "An expert agent"),
                                verbose=True,
                                llm=self.llm_router,
                            )
                            simplified_agents.append(new_agent)
                        except Exception as inner_e:
                            logger.error(f"Error recreating agent: {str(inner_e)}")

                    # Try to create crew with simplified agents
                    if simplified_agents:
                        logger.info(f"Retrying with {len(simplified_agents)} simplified agents")
                        try:
                            crew = Crew(
                                agents=simplified_agents,
                                tasks=tasks,
                                verbose=True,
                                process=Process.hierarchical,
                                manager_llm=self.llm_router,
                                memory=True,
                            )
                        except Exception as retry_e:
                            logger.error(f"Error in retry attempt: {str(retry_e)}")
                            return None, AgentResponse.error(
                                error_message="Failed to create agent crew after multiple attempts"
                            )
                    else:
                        return None, AgentResponse.error(
                            error_message="Failed to create simplified agents for recovery"
                        )
                else:
                    return None, AgentResponse.error(error_message=f"Error creating agent crew: {str(te)}")
            except Exception as ce:
                logger.error(f"Exception when creating Crew: {str(ce)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                return None, AgentResponse.error(error_message=f"Error creating agent crew: {str(ce)}")

            # Execute the crew
            try:
                result = crew.kickoff()
            except Exception as run_e:
                logger.error(f"Error during crew execution: {str(run_e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                return None, AgentResponse.error(error_message=f"Error during agent execution: {str(run_e)}")

            # Find which agent contributed the final answer
            # (typically the coordinator/default agent)
            contributing_agent = "default"
            if len(tasks) > 0:
                final_agent = tasks[-1].agent
                contributing_agent = getattr(final_agent, "name", str(id(final_agent)))

            # Convert the result to an AgentResponse
            # Safely extract agent names for metadata
            agent_names = []
            for a in agents:
                try:
                    agent_names.append(getattr(a, "name", f"agent_{id(a)}"))
                except:
                    agent_names.append("unnamed_agent")

            return contributing_agent, AgentResponse.success(
                content=result, metadata={"collaboration": "true", "contributing_agents": agent_names}
            )

        except Exception as e:
            logger.error(f"Error in crew orchestration: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return None, AgentResponse.error(error_message=f"Error in multi-agent processing: {str(e)}")

    async def cleanup(self):
        """Clean up resources when the orchestrator is no longer needed"""
        try:
            # Clean up any agent resources
            for agent_name in agent_manager_instance.get_available_agents():
                try:
                    agent = agent_manager_instance.get_agent(agent_name)

                    # Check if the agent has a cleanup method
                    if agent and hasattr(agent, "cleanup") and callable(agent.cleanup):
                        try:
                            await agent.cleanup()
                            logger.info(f"Successfully cleaned up agent {agent_name}")
                        except Exception as e:
                            logger.error(f"Error cleaning up agent {agent_name}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error accessing agent {agent_name} during cleanup: {str(e)}")

            # Clear the agent cache
            self.crew_agents_cache.clear()
            logger.info("Orchestrator cleanup completed successfully")

        except Exception as e:
            logger.error(f"Error during orchestrator cleanup: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")

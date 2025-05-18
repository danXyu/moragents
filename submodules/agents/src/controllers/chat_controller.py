from config import LLM_DELEGATOR, setup_logging
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from langchain.schema import SystemMessage

from models.service.chat_models import AgentResponse, ChatRequest
from models.service.service_models import GenerateConversationTitleRequest
from services.delegator.delegator import run_delegation
from services.orchestrator.run_flow import run_orchestration
from stores.agent_manager import agent_manager_instance

logger = setup_logging()


class ChatController:

    async def handle_chat(self, chat_request: ChatRequest) -> JSONResponse:
        """Handle chat requests and delegate to appropriate agent"""
        logger.info(f"Received chat request for conversation {chat_request.conversation_id}")

        try:
            # Parse command if present
            agent_name, message = agent_manager_instance.parse_command(chat_request.prompt.content)

            if agent_name:
                agent_manager_instance.set_active_agent(agent_name)
                chat_request.prompt.content = message
            else:
                agent_manager_instance.clear_active_agent()

            # If command was parsed, use that agent directly
            if agent_name:
                logger.info(f"Using command agent flow: {agent_name}")
                agent = agent_manager_instance.get_agent(agent_name)
                if not agent:
                    logger.error(f"Agent {agent_name} not found")
                    raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

                agent_response = await agent.chat(chat_request)
                current_agent = agent_name
            # Use orchestrator for multi-agent flow
            elif chat_request.use_research:
                logger.info("Using research flow")
                current_agent, agent_response = await run_orchestration(chat_request)
            # Otherwise use delegator to find appropriate agent
            else:
                logger.info("Using delegator flow")
                current_agent, agent_response = await run_delegation(chat_request)

            # We only critically fail if we don't get an AgentResponse
            if not isinstance(agent_response, AgentResponse):
                logger.error(f"Agent {current_agent} returned invalid response type {type(agent_response)}")
                raise HTTPException(status_code=500, detail="Agent returned invalid response type")

            # Return the response
            return JSONResponse(content={"response": agent_response.model_dump(mode='json'), "current_agent": current_agent})

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error handling chat: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def generate_conversation_title(self, request: GenerateConversationTitleRequest) -> str:
        """Generate a title for a conversation based on chat history"""
        system_prompt = """You are a helpful assistant that generates concise, descriptive titles for conversations.
        Generate a short title (3-6 words) that captures the main topic or theme of the conversation.
        The title should be clear and informative but not too long. DO NOT SURROUND THE TITLE WITH QUOTES, spaces,
        or any other characters. Just return the title as a string."""

        messages = [
            SystemMessage(content=system_prompt),
            *request.messages_for_llm,
        ]

        logger.info(f"Generating title with messages: {messages}")

        try:
            for attempt in range(3):
                try:
                    result = LLM_DELEGATOR.invoke(messages)
                    if not result:
                        continue

                    title = result.content.strip()
                    if not title:
                        continue

                    logger.info(f"Generated title: {title}")
                    return title

                except Exception as e:
                    logger.warning(f"Title generation attempt {attempt+1} failed: {str(e)}")
                    if attempt == 2:
                        raise

            raise Exception("All title generation attempts failed")

        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate title: {str(e)}")

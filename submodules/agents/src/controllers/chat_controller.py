from typing import Optional

from config import LLM_DELEGATOR, setup_logging
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from langchain.schema import SystemMessage
from models.service.chat_models import AgentResponse, ChatRequest
from models.service.service_models import GenerateConversationTitleRequest
from services.delegator.delegator import Delegator
from stores.agent_manager import agent_manager_instance
from services.orchestrator.run_flow import run_flow

logger = setup_logging()


class ChatController:
    def __init__(
        self,
        delegator: Optional[Delegator] = None,
    ):
        self.delegator = delegator

    async def handle_chat(self, chat_request: ChatRequest) -> JSONResponse:
        """Handle chat requests and delegate to appropriate agent"""
        logger.info(f"Received chat request for conversation {chat_request.conversation_id}")

        assert self.delegator is not None
        logger.info(f"Delegator: {self.delegator}")

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
            if chat_request.use_research:
                logger.info("Using research flow")
                # current_agent, agent_response = await self.orchestrator.orchestrate(chat_request)``
                current_agent = "basic_crew"
                agent_response = await run_flow(chat_request)

            # Otherwise use delegator to find appropriate agent
            if self.delegator and not chat_request.use_research:
                logger.info("Using delegator flow")
                current_agent, agent_response = await self.delegator.delegate_chat(chat_request)

            # We only critically fail if we don't get an AgentResponse
            if not isinstance(agent_response, AgentResponse):
                logger.error(f"Agent {current_agent} returned invalid response type {type(agent_response)}")
                raise HTTPException(status_code=500, detail="Agent returned invalid response type")

            response = agent_response.to_chat_message(current_agent).model_dump()
            logger.info(f"Sending response: {response}")
            return JSONResponse(content=response)

        except HTTPException:
            raise
        except TimeoutError:
            logger.error("Chat request timed out")
            raise HTTPException(status_code=504, detail="Request timed out")
        except ValueError as ve:
            logger.error(f"Input formatting error: {str(ve)}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"Error in chat route: {str(e)}", exc_info=True)
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

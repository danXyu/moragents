from config import LLM_DELEGATOR, setup_logging
from controllers.delegation_controller import DelegationController
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from models.service.chat_models import ChatRequest
from models.service.service_models import GenerateConversationTitleRequest
from services.delegator.delegator import Delegator

logger = setup_logging()

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat")
async def chat(chat_request: ChatRequest) -> JSONResponse:
    """Handle chat requests and delegate to appropriate agent"""
    logger.info(f"Received chat request for conversation {chat_request.conversation_id}")

    # Initialize new delegator and controller for each request
    delegator = Delegator(LLM_DELEGATOR)
    controller = DelegationController(delegator)

    try:
        response = await controller.handle_chat(chat_request)
        return response

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


@router.post("/generate-title")
async def generate_conversation_title(
    request: GenerateConversationTitleRequest,
) -> JSONResponse:
    """Generate a title for a conversation based on chat history"""
    logger.info(f"Received title generation request for conversation {request.conversation_id}")

    # Initialize new delegator and controller for each request
    controller = DelegationController()

    try:
        title = await controller.generate_conversation_title(request)
        return JSONResponse(content={"title": title})

    except HTTPException:
        raise
    except TimeoutError:
        logger.error("Title generation request timed out")
        raise HTTPException(status_code=504, detail="Request timed out")
    except ValueError as ve:
        logger.error(f"Input formatting error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in generate title route: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

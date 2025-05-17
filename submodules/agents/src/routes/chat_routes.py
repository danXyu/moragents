from config import setup_logging
from controllers.chat_controller import ChatController
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from models.service.chat_models import ChatRequest
from models.service.service_models import GenerateConversationTitleRequest
from services.delegator.delegator import Delegator
from sse_starlette.sse import EventSourceResponse
from services.orchestrator.progress_listener import event_stream
import uuid
from datetime import datetime

logger = setup_logging()

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat")
async def chat(chat_request: ChatRequest) -> JSONResponse:
    """Handle chat requests and delegate to appropriate agent"""
    logger.info(f"Received chat request for conversation {chat_request.conversation_id}")

    # Initialize new delegator and controller for each request
    delegator = Delegator()
    controller = ChatController(delegator)

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
    controller = ChatController()

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


@router.post("/chat/stream")
async def chat_stream(chat_request: ChatRequest):
    """Handle streaming chat requests with SSE"""
    logger.info(f"Received streaming chat request for conversation {chat_request.conversation_id}")
    
    # Generate a unique request ID for this stream
    request_id = str(uuid.uuid4())
    chat_request.request_id = request_id
    
    # Only support streaming for research/multi-agent flow
    if not chat_request.use_research:
        raise HTTPException(status_code=400, detail="Streaming is only supported for research mode")
    
    # Initialize controller with delegator for streaming
    delegator = Delegator()
    controller = ChatController(delegator)
    
    # Start processing in background
    import asyncio
    
    async def process_stream():
        try:
            # Call the handle_chat method in the background
            await controller.handle_chat(chat_request)
        except Exception as e:
            logger.error(f"Error in stream processing: {e}", exc_info=True)
            # Emit error event
            from services.orchestrator.progress_listener import get_or_create_queue
            queue = get_or_create_queue(request_id)
            await queue.put({
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "message": str(e)
                }
            })
            await queue.put({
                "type": "stream_complete",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "message": "Stream complete with error"
                }
            })
    
    # Start processing asynchronously
    asyncio.create_task(process_stream())
    
    # Return SSE response immediately
    return EventSourceResponse(event_stream(request_id))


@router.get("/chat/stream/{request_id}")
async def get_stream(request_id: str):
    """Get the SSE stream for a specific request ID"""
    logger.info(f"Getting stream for request {request_id}")
    return EventSourceResponse(event_stream(request_id))

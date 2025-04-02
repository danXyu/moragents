import logging
import os

from config import RAG_VECTOR_STORE
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from models.service.chat_models import AgentResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/rag", tags=["rag"])

# Vector store path for persistence
VECTOR_STORE_PATH = os.path.join(os.getcwd(), "data", "vector_store")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for RAG processing"""
    logger.info("Received upload request")
    try:
        # Process the file using the existing RAG_VECTOR_STORE
        result = await RAG_VECTOR_STORE.process_file(file)

        # Save the updated vector store
        os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)
        RAG_VECTOR_STORE.save(VECTOR_STORE_PATH)
        logger.info(f"Vector store saved to {VECTOR_STORE_PATH}")

        response = AgentResponse.success(content=result).to_chat_message("rag").model_dump()
        return JSONResponse(content=response)

    except ValueError as ve:
        # Handle validation errors
        logger.warning(f"Validation error: {str(ve)}")
        response = AgentResponse.error(error_message=str(ve)).to_chat_message("rag").model_dump()
        return JSONResponse(content=response)
    except Exception as e:
        # Handle other errors
        logger.error(f"Failed to upload file: {str(e)}")
        response = (
            AgentResponse.error(error_message=f"Failed to upload file: {str(e)}").to_chat_message("rag").model_dump()
        )
        return JSONResponse(content=response)


@router.delete("/documents")
async def delete_documents():
    """Clear all documents from the vector store"""
    try:
        # Reinitialize the vector store with existing embeddings
        RAG_VECTOR_STORE.vector_store = None
        RAG_VECTOR_STORE.retriever = None

        # Remove existing vector store file if it exists
        if os.path.exists(VECTOR_STORE_PATH):
            import shutil

            shutil.rmtree(VECTOR_STORE_PATH, ignore_errors=True)
            logger.info(f"Removed vector store at {VECTOR_STORE_PATH}")

        response = (
            AgentResponse.success(content="All documents have been removed from the vector store")
            .to_chat_message("rag")
            .model_dump()
        )
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error clearing vector store: {str(e)}")
        response = (
            AgentResponse.error(error_message=f"Error clearing vector store: {str(e)}")
            .to_chat_message("rag")
            .model_dump()
        )
        return JSONResponse(content=response)

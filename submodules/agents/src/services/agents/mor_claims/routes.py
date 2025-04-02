import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from stores import agent_manager_instance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/claim", tags=["claim"])


@router.post("/claim")
async def claim(request: Request) -> JSONResponse:
    """Process a claim request"""
    logger.info("Received claim request")
    try:
        claim_agent = agent_manager_instance.get_agent("claim")
        if not claim_agent:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Claim agent not found"},
            )

        response = await claim_agent.claim(request)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Claim processed successfully",
                "response": response,
            },
        )
    except Exception as e:
        logger.error(f"Failed to process claim: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to process claim: {str(e)}",
            },
        )

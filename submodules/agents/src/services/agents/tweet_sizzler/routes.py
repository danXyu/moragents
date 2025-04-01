import logging
import warnings

# Suppress Tweepy warnings before it is imported. Until maintainers fix the issue.
warnings.filterwarnings(
    "ignore",
    message="invalid escape sequence.*",
    category=SyntaxWarning,
    module="tweepy",
)

import tweepy
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from stores import agent_manager_instance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tweet", tags=["tweet"])


@router.post("/regenerate")
async def regenerate_tweet():
    """Regenerate a tweet"""
    logger.info("Received regenerate tweet request")
    try:
        tweet_agent = agent_manager_instance.get_agent("tweet sizzler")
        if not tweet_agent:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Tweet sizzler agent not found"},
            )

        response = tweet_agent.generate_tweet()
        return response
    except Exception as e:
        logger.error(f"Failed to regenerate tweet: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to regenerate tweet: {str(e)}",
            },
        )


class TweetRequest(BaseModel):
    """Request body for posting a tweet"""

    post_content: str
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str


@router.post("/post")
async def post_tweet(request: TweetRequest):
    """Post a tweet"""
    logger.info("Received post tweet request")
    try:
        client = tweepy.Client(
            consumer_key=request.api_key,
            consumer_secret=request.api_secret,
            access_token=request.access_token,
            access_token_secret=request.access_token_secret,
        )

        response = client.create_tweet(text=request.post_content)
        logger.info(f"Tweet posted successfully: {response}")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "tweet": response.data["text"],
                "tweet_id": response.data["id"],
            },
        )

    except Exception as e:
        logger.error(f"Failed to post tweet: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Failed to post tweet: {str(e)}"},
        )

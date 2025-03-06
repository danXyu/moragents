import logging
from typing import Dict
from langchain.schema import HumanMessage
from services.agents.tweet_sizzler.config import Config
from config import LLM_AGENT

logger = logging.getLogger(__name__)


async def generate_tweet(content: str) -> str:
    """
    Generate a tweet based on the provided content.

    Args:
        content (str): The content to generate a tweet about

    Returns:
        Dict[str, str]: Dictionary containing the generated tweet content
    """
    try:
        result = LLM_AGENT.invoke(
            [
                Config.system_message,
                HumanMessage(content=f"Generate a tweet for: {content}"),
            ]
        )

        tweet = result.content.strip()
        tweet = " ".join(tweet.split())  # Normalize whitespace

        # Remove any dictionary-like formatting
        if tweet.startswith("{") and tweet.endswith("}"):
            tweet = tweet.strip("{}").split(":", 1)[-1].strip().strip('"')

        logger.info(f"Tweet generated successfully: {tweet}")
        return tweet

    except Exception as e:
        logger.error(f"Error generating tweet: {str(e)}")
        return str(e)

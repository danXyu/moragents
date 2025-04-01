from langchain.schema import SystemMessage
from models.service.agent_config import AgentConfig


class Config:
    """Configuration for Tweet Sizzler Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.tweet_sizzler.agent",
        class_name="TweetSizzlerAgent",
        description="Creates engaging social media content",
        delegator_description="Creates engaging cryptocurrency-related social media content, generates tweet drafts, "
        "analyzes tweet performance metrics, and suggests hashtags or posting strategies. Use when users "
        "want to create or optimize social media content related to crypto.",
        human_readable_name="Tweet Generator",
        command="tweet",
        upload_required=False,
    )

    # *************
    # SYSTEM MESSAGE
    # *************

    system_message = SystemMessage(
        content=(
            "You are a witty and engaging tweet generator. Your task is to create spicy, "
            "attention-grabbing tweets based on the user's prompt. It is CRUCIAL that you "
            "keep the tweets strictly under 280 characters - this is a hard limit. Make the "
            "tweets as engaging as possible while adhering to this character limit. Do not "
            "surround your tweet with quotes or any other formatting. Do not preface it with "
            "any text like 'here is your tweet'. Simply generate and output the tweet, ensuring "
            "it is less than 280 characters long. Use newlines sparingly. Do not surrounded with "
            "quotes or braces. Do not use any other formatting."
        )
    )

    # *************
    # TOOLS CONFIG
    # *************

    tools = [
        {
            "name": "generate_tweet",
            "description": "Generate an engaging tweet based on provided content",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to base the tweet on",
                    }
                },
                "required": ["content"],
            },
        }
    ]

    # *************
    # TWITTER CONFIG
    # *************

    TWITTER_API_VERSION = "2"
    TWEET_MAX_LENGTH = 280

    # LLM configuration
    LLM_MAX_TOKENS = 280
    LLM_TEMPERATURE = 0.7

    # Error messages
    ERROR_NO_TWEET_CONTENT = "No tweet content provided"
    ERROR_TWITTER_CLIENT_NOT_INITIALIZED = (
        "Twitter client not initialized. Please set X API credentials first."
    )
    ERROR_MISSING_API_CREDENTIALS = "Missing required X API credentials"
    ERROR_INVALID_ACTION = "Invalid action"
    ERROR_MISSING_PARAMETERS = "Missing required parameters"

"""
Example demonstrating how to use the BasicOrchestrator with ChatController.

This script shows how to initialize and use the BasicOrchestrator
to handle chat requests in a multi-agent environment.
"""

import asyncio
import logging
from typing import Optional

from config import LLM_DELEGATOR
from models.service.chat_models import ChatRequest, ChatMessage
from services.orchestrator.basic_orchestrator import BasicOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """
    Main function demonstrating BasicOrchestrator usage.
    """
    # Initialize the BasicOrchestrator with the LLM delegator
    orchestrator = BasicOrchestrator(llm_router=LLM_DELEGATOR)

    # Create a sample chat request
    chat_request = ChatRequest(
        prompt=ChatMessage(role="user", content="What is the current price of Bitcoin?"),
        chain_id="example_chain",
        wallet_address="example_wallet",
        conversation_id="example_conversation",
        chat_history=[],
        use_multiagent=True,  # Enable multi-agent processing
    )

    # Process the request with the orchestrator
    logger.info("Processing request with BasicOrchestrator...")
    agent_name, response = await orchestrator.orchestrate(chat_request)

    # Log the result
    if agent_name:
        logger.info(f"Response from agent: {agent_name}")
        logger.info(f"Content: {response.content}")
        logger.info(f"Metadata: {response.metadata}")
    else:
        logger.error(f"Error: {response.error_message}")

    # Cleanup
    await orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

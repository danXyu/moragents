# BasicOrchestrator

A CrewAI-powered multi-agent orchestrator for handling chat requests across specialized agents.

## Overview

The `BasicOrchestrator` creates a collaborative crew of agents including:

1. **Crypto Data Agent** - Provides cryptocurrency market data, NFT floor prices, and DeFi protocol information
2. **Search Agent** - Searches the web for up-to-date information using Brave Search
3. **Scraper Agent** - Extracts content from websites using Selenium
4. **Research Agent** - Coordinates research efforts and synthesizes information

These agents work together in a hierarchical process to handle complex queries that may require multiple specialized skills.

## Requirements

To use the `BasicOrchestrator`, you'll need to install:

```bash
pip install 'crewai[tools]'
pip install selenium webdriver-manager
```

The system also requires:

- Chrome browser installed (for Selenium)
- Brave Search API key (for BraveSearchTool)

## Usage

### Basic Integration

```python
from services.orchestrator.basic_orchestrator import BasicOrchestrator
from config import LLM_DELEGATOR
from models.service.chat_models import ChatRequest, ChatMessage

# Initialize the orchestrator
orchestrator = BasicOrchestrator(llm_router=LLM_DELEGATOR)

# Create a chat request
chat_request = ChatRequest(
    prompt=ChatMessage(role="user", content="What is the current price of Bitcoin?"),
    chain_id="example_chain",
    wallet_address="example_wallet",
    conversation_id="example_conversation",
    chat_history=[],
    use_multiagent=True  # Enable multi-agent processing
)

# Process the request
agent_name, response = await orchestrator.orchestrate(chat_request)

# Get the result
if agent_name:
    print(f"Response: {response.content}")
else:
    print(f"Error: {response.error_message}")

# Clean up when done
await orchestrator.cleanup()
```

### Integration with ChatController

```python
from fastapi import FastAPI
from services.orchestrator.basic_orchestrator import BasicOrchestrator
from controllers.chat_controller import ChatController
from config import LLM_DELEGATOR

# Initialize FastAPI app
app = FastAPI()

# Initialize the orchestrator
orchestrator = BasicOrchestrator(llm_router=LLM_DELEGATOR)

# Initialize the chat controller with the orchestrator
chat_controller = ChatController(orchestrator=orchestrator)

# Define routes
@app.post("/chat")
async def chat(request: ChatRequest):
    return await chat_controller.handle_chat(request)

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await orchestrator.cleanup()
```

## Architecture

The `BasicOrchestrator` follows these steps:

1. Initializes specialized agents and tools
2. Creates tasks for each agent based on the chat request
3. Sets up a CrewAI crew with a hierarchical process
4. Executes the crew to obtain a collaborative result
5. Returns the result with metadata about contributing agents

## Extending

To add new agent types:

1. Create a new agent creation method (e.g., `_create_custom_agent()`)
2. Add the new agent to the `_setup_agents()` method
3. Include the agent in the crew creation in the `orchestrate()` method

## Troubleshooting

- **Import Errors**: Ensure all required packages are installed
- **Agent Creation Failures**: Check that the agent manager is properly initialized
- **CrewAI Errors**: Verify that the LLM router is properly configured
- **Selenium Errors**: Make sure Chrome is installed and webdriver-manager is set up correctly

# Agent Development Guide

This guide walks you through the process of developing new agents for the MySuperAgent platform.

## Agent Architecture

Agents in MySuperAgent follow a modular architecture:

```
your_agent_name/
├── __init__.py
├── agent.py
├── config.py
└── tools/
    └── tools.py
```

Each agent consists of:

- **agent.py**: Main agent class that extends AgentCore
- **config.py**: Configuration including tool definitions
- **tools/tools.py**: Implementation of agent-specific tools

## Creating a New Agent

### 1. Use the Creation Script

```bash
./create_new_agent.sh
```

When prompted, enter your agent name (must start with a letter and can only contain letters, numbers, underscores, and hyphens).

### 2. Configure Agent in Main Config

Add your agent to the main config file in `src/config.py`:

```python
from services.agents.your_agent_name.config import Config as YourAgentConfig

class Config:
    # ... existing config ...

    AGENT_CONFIGS = {
        # ... existing agents ...
        "your_agent_name": YourAgentConfig,
    }
```

### 3. Implement Agent Logic

In `your_agent_name/agent.py`:

```python
class YourAgentNameAgent(AgentCore):
    """Agent for handling specific operations related to your agent's purpose."""

    def __init__(self, config: Dict[str, Any], llm: Any, embeddings: Any):
        super().__init__(config, llm, embeddings)
        self.tools_provided = [
            # Add your tool functions here
        ]
        self.tool_bound_llm = self.llm.bind_tools(self.tools_provided)

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        try:
            messages = [
                SystemMessage(content="Your custom system prompt here"),
                HumanMessage(content=request.prompt.content),
            ]

            result = self.tool_bound_llm.invoke(messages)
            return await self._handle_llm_response(result)
        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.error(error_message=str(e))

    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        """Execute the appropriate tool based on function name."""
        tool_map = {
            # Map your tool names to their implementation functions
            "your_tool_name": self._your_tool_implementation,
        }

        if func_name not in tool_map:
            return AgentResponse.error(error_message=f"Unknown tool: {func_name}")

        try:
            result = await tool_map[func_name](**args)
            return AgentResponse.success(content=result)
        except Exception as e:
            return AgentResponse.error(error_message=str(e))
```

### 4. Implement Tools

In `your_agent_name/tools/tools.py`:

```python
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def your_tool_implementation(arg1: str, arg2: int) -> str:
    """
    Implementation of your custom tool.

    Args:
        arg1: Description of first argument
        arg2: Description of second argument

    Returns:
        str: Result of the tool operation
    """
    try:
        # Your tool implementation here
        result = f"Processed {arg1} with value {arg2}"
        return result
    except Exception as e:
        logger.error(f"Error in tool implementation: {str(e)}", exc_info=True)
        raise
```

### 5. Configure Tools

In `your_agent_name/config.py`:

```python
class Config:
    tools = [
        {
            "name": "your_tool_name",
            "description": "Description of what your tool does",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {
                        "type": "string",
                        "description": "Description of first argument"
                    },
                    "arg2": {
                        "type": "integer",
                        "description": "Description of second argument"
                    }
                },
                "required": ["arg1", "arg2"]
            }
        }
    ]
```

## Best Practices

### Error Handling

- Use the `@handle_exceptions` decorator for common exceptions
- Return appropriate `AgentResponse` types:
  - `AgentResponse.success(content="Success message")`
  - `AgentResponse.error(error_message="Error description")`
  - `AgentResponse.needs_info(message="Additional information needed")`

### Logging

Always use the logger for debugging and monitoring:

```python
self.logger.info("Processing request")
self.logger.error("Error occurred", exc_info=True)
```

### Input Validation

Validate inputs early to prevent errors down the pipeline:

```python
if not some_required_value:
    return AgentResponse.needs_info(message="Please provide required value")
```

### Modularity

- Keep tool implementations focused on a single responsibility
- Separate complex logic into helper functions
- Use type hints consistently for better code maintainability

## Testing Your Agent

Create tests in the `tests/agents/your_agent_name/` directory:

```python
import pytest
from services.agents.your_agent_name.agent import YourAgentNameAgent
from models.service.chat_models import ChatRequest

@pytest.mark.asyncio
async def test_agent_basic_functionality():
    # Setup test agent
    agent = YourAgentNameAgent(mock_config, mock_llm, mock_embeddings)

    # Create request
    request = ChatRequest(prompt="Test prompt")

    # Process request
    response = await agent.chat(request)

    # Assert on response
    assert response.error_message is None
    assert response.content is not None
```

Test different aspects:

- Basic functionality
- Tool implementations
- Error handling
- Edge cases

## Examples

See existing agents in the repository for real-world examples:

- DCA Agent
- Base Agent
- Tweet Sizzler

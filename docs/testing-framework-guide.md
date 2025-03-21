# Testing Framework

This document covers testing practices for MySuperAgent platform and agent development.

## Overview

MySuperAgent uses a comprehensive testing framework to ensure quality and reliability:

1. **Unit Tests**: Individual functions and components
2. **Integration Tests**: Interactions between components
3. **End-to-End Tests**: Complete user flows
4. **Agent-Specific Tests**: Validation of agent functionality

## Testing Tools

- **pytest**: Primary testing framework
- **pytest-asyncio**: For testing async functions
- **pytest-mock**: For mocking dependencies
- **pytest-cov**: For code coverage reports

## Directory Structure

```
tests/
├── conftest.py               # Shared fixtures
├── unit/
│   ├── agents/
│   │   └── your_agent_name/  # Tests for specific agent
│   ├── services/
│   ├── models/
│   └── tools/
├── integration/
│   ├── agents/
│   ├── services/
│   └── api/
└── e2e/
    └── workflows/
```

## Setting Up Tests

### Prerequisites

Install test dependencies:

```bash
poetry install --with test
```

### Writing Tests for Agents

Create a file structure in `tests/unit/agents/your_agent_name/` that mirrors your agent's structure.

#### Basic Agent Test

```python
import pytest
from services.agents.your_agent_name.agent import YourAgentNameAgent
from models.service.chat_models import ChatRequest, AgentResponse

@pytest.fixture
def mock_llm():
    # Mock the LLM service
    mock = MagicMock()
    mock.invoke.return_value = {"content": "Mocked response"}
    mock.bind_tools.return_value = mock
    return mock

@pytest.fixture
def mock_embeddings():
    # Mock the embeddings service
    return MagicMock()

@pytest.fixture
def agent_config():
    # Return a test configuration
    return {
        "tools": [
            {
                "name": "test_tool",
                "description": "Test tool for unit tests",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_param": {
                            "type": "string",
                            "description": "Test parameter"
                        }
                    },
                    "required": ["test_param"]
                }
            }
        ]
    }

@pytest.fixture
def agent(mock_llm, mock_embeddings, agent_config):
    return YourAgentNameAgent(agent_config, mock_llm, mock_embeddings)

@pytest.mark.asyncio
async def test_agent_initialization(agent):
    """Test that agent initializes correctly."""
    assert agent is not None
    assert len(agent.tools_provided) > 0
    assert agent.tool_bound_llm is not None

@pytest.mark.asyncio
async def test_process_request(agent, mock_llm):
    """Test that agent processes requests correctly."""
    # Arrange
    request = ChatRequest(prompt="Test request")

    # Act
    response = await agent.chat(request)

    # Assert
    assert isinstance(response, AgentResponse)
    assert mock_llm.invoke.called
    assert response.content is not None
    assert response.error_message is None
```

#### Testing Tool Execution

```python
@pytest.mark.asyncio
async def test_tool_execution(agent, mocker):
    """Test tool execution function."""
    # Arrange
    mocker.patch.object(
        agent,
        '_your_tool_implementation',
        return_value="Tool executed successfully"
    )

    # Act
    response = await agent._execute_tool("your_tool_name", {"arg1": "test", "arg2": 123})

    # Assert
    assert response.content == "Tool executed successfully"
    assert response.error_message is None
    agent._your_tool_implementation.assert_called_once_with(arg1="test", arg2=123)
```

### Testing Tools

Test each tool in isolation:

```python
from services.agents.your_agent_name.tools.tools import your_tool_implementation

@pytest.mark.asyncio
async def test_your_tool_implementation():
    """Test the actual tool implementation."""
    # Act
    result = await your_tool_implementation(arg1="test", arg2=123)

    # Assert
    assert "Processed test with value 123" in result
```

## Mocking External Services

For tools that interact with external services, use mocking:

```python
@pytest.mark.asyncio
async def test_external_api_tool(mocker):
    """Test a tool that calls an external API."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": "test_result"}
    mock_response.status_code = 200

    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Act
    from services.agents.your_agent_name.tools.tools import api_tool
    result = await api_tool(query="test")

    # Assert
    assert "test_result" in result
    mock_session.get.assert_called_once()
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests for a Specific Agent

```bash
pytest tests/unit/agents/your_agent_name/
```

### Run with Coverage

```bash
pytest --cov=services.agents.your_agent_name
```

Generate HTML coverage report:

```bash
pytest --cov=services.agents.your_agent_name --cov-report=html
```

## Integration Tests

Integration tests verify that your agent works with the platform:

```python
@pytest.mark.asyncio
async def test_agent_registration(client):
    """Test that agent is properly registered in the platform."""
    # Arrange
    from services.agent_registry import AgentRegistry

    # Act
    response = await client.get("/api/agents")
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert any(agent["id"] == "your_agent_name" for agent in data["agents"])

@pytest.mark.asyncio
async def test_agent_chat_endpoint(client):
    """Test that agent responds through the chat API."""
    # Arrange
    request_data = {
        "prompt": "Test request for your agent",
        "agent_id": "your_agent_name"
    }

    # Act
    response = await client.post("/api/chat", json=request_data)
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert "content" in data
    assert data["agent_id"] == "your_agent_name"
```

## Continuous Integration

Tests run automatically in CI pipelines on:

- Pull request creation
- Merge to main branch

The CI pipeline:

1. Sets up the testing environment
2. Installs dependencies
3. Runs linters and style checks
4. Executes unit tests
5. Runs integration tests
6. Generates coverage reports

## Best Practices

1. **Keep Tests Focused**: Each test should verify a single behavior
2. **Use Descriptive Names**: Test names should describe what they're testing
3. **Maintain Test Independence**: No test should depend on another
4. **Use Fixtures**: Share setup code through pytest fixtures
5. **Mock External Dependencies**: Don't rely on external services in unit tests
6. **Test Error Handling**: Verify that your code handles errors gracefully
7. **Maintain High Coverage**: Aim for >85% test coverage
8. **Write Both Positive and Negative Tests**: Test both successes and failures

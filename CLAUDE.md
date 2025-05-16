# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MySuperAgent is a platform for building, deploying, and leveraging AI agents. It consists of:
- **Python Backend**: Agent orchestration system using FastAPI, LangChain, and CrewAI
- **React Frontend**: Next.js-based web interface with Web3 capabilities
- **Multi-Agent Framework**: Extensible architecture supporting various specialized agents

## Architecture

### Backend Architecture
- **Agent System** (`submodules/agents/src/services/agents/`): Individual agents extending base_agent/agent.py
- **Orchestrator** (`submodules/agents/src/services/orchestrator/`): CrewAI-based multi-agent orchestration
- **Delegator** (`submodules/agents/src/services/delegator/`): Routes requests to appropriate agents
- **Controllers** (`submodules/agents/src/controllers/`): FastAPI endpoints for chat, user, and agent management
- **Database**: PostgreSQL with Alembic migrations for user data
- **Vector Store**: ChromaDB for RAG capabilities

### Frontend Architecture
- **Components** (`submodules/frontend/components/`): React components for UI
- **Contexts** (`submodules/frontend/contexts/`): State management with React Context
- **Services** (`submodules/frontend/services/`): API clients and utilities

## Common Development Commands

### Backend Development (Agents)
```bash
cd submodules/agents

# Install dependencies
poetry install

# Run the server locally
poetry run uvicorn src.app:app --host 0.0.0.0 --port 8888 --reload

# Run tests
poetry run pytest

# Run specific test
poetry run pytest tests/services/agents/crypto_data/benchmark/test_crypto_data_agent.py

# Linting and formatting
poetry run black src/
poetry run isort src/
poetry run pylint src/
poetry run mypy src/

# Database migrations
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "Description"

# Create new agent
./src/services/agents/create_new_agent.sh
```

### Frontend Development
```bash
cd submodules/frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

### Docker Development
```bash
# Run full stack with Docker Compose
docker compose -p mysuperagent -f build/docker-compose.yml up

# Run individual services
docker compose -p mysuperagent -f build/docker-compose.yml up agents
docker compose -p mysuperagent -f build/docker-compose.yml up frontend
```

### Testing
```bash
# Run all tests
cd submodules/agents
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Run benchmark tests
poetry run pytest tests/services/agents/*/benchmarks/

# Run unit tests
poetry run pytest tests/services/agents/*/unit/
```

## Agent Development

To create a new agent:

1. Use the creation script:
   ```bash
   cd submodules/agents/src/services/agents
   ./create_new_agent.sh
   ```

2. Add agent to main config (`src/config.py`):
   ```python
   from services.agents.your_agent.config import Config as YourAgentConfig
   
   AGENT_CONFIGS = {
       "your_agent": YourAgentConfig,
   }
   ```

3. Implement agent logic in `your_agent/agent.py` extending `AgentCore`
4. Define tools in `your_agent/tools.py`
5. Configure tools in `your_agent/config.py`
6. Add tests in `tests/services/agents/your_agent/`

### Agent Response Types
- `AgentResponse.success(content="...")`
- `AgentResponse.error(error_message="...")`
- `AgentResponse.needs_info(message="...")`

## Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `TogetherApiKey`: Together AI API key
- `CerebrasApiKey`: Cerebras API key
- `CodexApiKey`: Codex API key
- `ElfaApiKey`: Elfa API key

### Frontend
- `NEXT_PUBLIC_API_URL`: Backend API URL

## MCP Agent Creation

For Model Context Protocol (MCP) agents:
1. Create config in `src/services/agents/mcp_<name>/config.py`
2. Follow standard MCP integration patterns
3. Ensure proper server installation and configuration

## Deployment

### Staging
```bash
# Jenkins deployment to staging
# Select ENVIRONMENT: staging, COMPONENT: all
```

### Production
```bash
# Jenkins deployment to prod
# Select ENVIRONMENT: prod, COMPONENT: all
```

## Key Files and Patterns

### Agent Implementation Pattern
```python
class YourAgent(AgentCore):
    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        # Process request logic
        
    async def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> AgentResponse:
        # Tool execution logic
```

### Error Handling
- Use `@handle_exceptions` decorator for common error patterns
- Log errors appropriately with `self.logger`
- Return proper `AgentResponse` types

### Testing Pattern
```python
@pytest.mark.asyncio
async def test_agent_functionality():
    agent = YourAgent(config, llm, embeddings)
    response = await agent.chat(request)
    assert response.error_message is None
```
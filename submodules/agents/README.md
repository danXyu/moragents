# MySuperAgent:agents

## Overview

MySuperAgent:agents is the server that powers the MySuperAgent.io app. It's a FastAPI-based AI chat application featuring intelligent responses from various language models and embeddings. The system includes file uploading and a delegator system to manage multiple specialized agents. The application can run locally and supports containerization with Docker.

## Pre-requisites

- [Download Ollama](https://ollama.com/) for your operating system
- After installation, pull these two required models:

```sh
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

## Getting Started

### Building from Source

1. Clone the repository:

```sh
git clone https://github.com/yourusername/mysuperagent.git
cd mysuperagent
```

2. Install Poetry (if not already installed):

```sh
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:

```sh
poetry install
```

4. Run the application:

```sh
cd src
poetry run uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### Using Docker Compose

1. Ensure you're in the root project folder:

```sh
# Make sure you're in the main project directory, not submodules
```

2. Build images and launch containers:

   For Intel/AMD/x86_64:

   ```sh
   docker-compose up
   ```

   For Apple Silicon (M1, M2, etc.):

   ```sh
   docker compose -f build/docker-compose-apple.yml up
   ```

3. Open in the browser: `http://localhost:3333/`

The Docker build will download the model. The first time an agent is called, the model will be loaded into memory and shared between all agents.

## API Endpoints

The application provides several key API endpoints:

### Chat API

- **POST /api/v1/chat**: Handles chat requests and delegates to appropriate agent

  - Accepts a `ChatRequest` object
  - Returns the AI-generated response

- **POST /api/v1/generate-title**: Generates a title for a conversation based on chat history
  - Accepts a `GenerateConversationTitleRequest` object
  - Returns a JSON response with the generated title

### Agent Management API

- **GET /agents/available**: Gets the list of currently available agents

  - Returns selected and available agents

- **POST /agents/selected**: Sets which agents should be selected

  - Accepts a JSON object with an "agents" array
  - Returns success status and the selected agents

- **GET /agents/commands**: Gets the list of available agent commands
  - Returns commands, descriptions, and human-readable names for each agent

## Creating a New Agent

To create a new agent, follow the instructions in the README.md located in the `src/services/agents` directory.

## Code Quality & Linting

We use several tools to maintain code quality:

### Python

1. **black** - Code formatting
2. **isort** - Import sorting
3. **flake8** - Style guide enforcement

### Frontend

1. **eslint** - JavaScript/TypeScript linting

### Running Linters

Linters will automatically run on staged files when you commit changes. You can also run them manually:

```bash
# In root directory
pip install -r requirements.txt
pre-commit install

# Run all pre-commit hooks on staged files
pre-commit run

# Run on specific files
pre-commit run --files path/to/file.py

# Run all hooks on all files
pre-commit run --all-files
```

![morpheus ecosystem](static/morpheus-ecosystem@3x_green.png)

# MySuperAgent

## A Platform for Building, Deploying, and Leveraging AI Agents

A developer-focused platform that enables building, testing, and deploying AI agents. Powered by Python and React, with seamless integration of LLMs and Web3 capabilities.

**Note:** MySuperAgent serves as both a development sandbox and production platform for AI agent builders. The platform enables rapid prototyping and deployment of agents that can be automatically invoked based on user intent. For detailed documentation on specific agents, see the agent READMEs in the `/agents` directory.

![UI](static/demo.gif)

---

### Available Agents & Features

#### Generate Images (Imagen) 💫

- Generate AI images using Stable Diffusion XL
- Example: "Generate an image of Donald Trump"
- Example: "Create a cyberpunk style portrait of Elon Musk"

#### Document Analysis 📄

- Upload and analyze documents with natural language querying
- Example: "Summarize the uploaded document"
- Example: "What are the key points in this uploaded document?"

#### Crypto Market Data 📈

- Real-time price, market cap and TVL data
- Example: "What's the price of ETH?"
- Example: "What's the FDV of USDC?"

#### Token Swaps 🔄

- Swap tokens across multiple chains
- Example: "Swap 0.2 ETH for USDC"
- Example: "Exchange my BTC for ETH"

#### Tweet Generator 🔥

- AI-powered viral tweet generation
- Example: "Create a viral tweet about Web3"
- Example: "Create a spicy crypto market tweet about Gary Gensler"

#### Base Transactions ⚡

- Send and swap tokens on Base
- Example: "Send USDC on Base"
- Example: "Swap USDC for ETH on Base"

#### MOR Claims Manager 🎁

- Manage and claim MOR token rewards
- Example: "Claim my MOR rewards"
- Example: "Help me claim my pending MOR tokens"

#### MOR Rewards Tracking 🏆

- Track and analyze MOR rewards
- Example: "Show my MOR rewards balance"
- Example: "Calculate my pending MOR rewards"

#### Crypto News Analysis 📰

- Get latest crypto market news and analysis
- Example: "Analyze recent crypto market news for ETH"
- Example: "What's the latest news impact on BTC?"

#### DexScreener 📊

- Monitor DEX activity and token metrics
- Example: "Scan Dexscreener for the most active tokens on solana"
- Example: "Show me DEX activity for ETH as reported by Dexscreener"

#### Elfa Social Search 🔍

- Search social media for crypto mentions
- Example: "Search for mentions of MOR on social media"
- Example: "What are the top trending tokens on social media?"

#### Solana Token Safety 🛡️

- Check token safety and rugpull risks
- Example: "Check token safety for SAMO"
- Example: "Show me the most viewed tokens on rugcheck"

#### Codex Agent 🗄️

- Advanced token analytics and insights
- Example: "What are the top trending tokens on Ethereum?"
- Example: "Who are the top holders of $TRUMP on Solana?"

---

## Getting Started

### Using the Platform

Visit [https://mysuperagent.io](https://mysuperagent.io) to access the hosted platform.

#### Requirements

- Modern web browser (Chrome, Firefox, Safari)
- Web3 wallet for blockchain interactions
- API keys for specific agent integrations (Coinbase, Twitter, etc)

### Local Development

To run MySuperAgent locally, follow these comprehensive setup instructions:

#### Prerequisites

1. Install Ollama:
   ```bash
   # Install Ollama following instructions at https://ollama.ai
   ollama pull 3.2:3b
   ollama serve
   ```

#### Running with Docker

1. Clone the repository:

   ```bash
   git clone https://github.com/mysuperagent/mysuperagent.git
   cd mysuperagent
   ```

2. Start the Docker environment:

   ```bash
   docker compose -p mysuperagent -f build/docker-compose.yml up
   ```

3. Access the application:
   - Frontend: http://localhost:3333
   - Server API: http://localhost:8888

#### Running Services Independently

1. Clone the repository:

   ```bash
   git clone https://github.com/mysuperagent/mysuperagent.git
   cd mysuperagent
   ```

2. Start PostgreSQL:

   ```bash
   docker run -d \
     -p 5678:5678 \
     -e POSTGRES_USER=neo \
     -e POSTGRES_PASSWORD=trinity \
     -e POSTGRES_DB=morpheus_db \
     postgres:16-bullseye -p 5678
   ```

3. Start the Frontend:

   ```bash
   cd submodules/frontend
   docker build -t frontend .
   docker run -d -p 3333:80 frontend
   ```

4. Start the Agents API:
   ```bash
   cd submodules/agents
   docker build -t agents -f build/Dockerfile .
   docker run -d \
     -p 8888:5000 \
     -e DATABASE_URL=postgresql://neo:trinity@localhost:5678/morpheus_db \
     agents
   ```

#### Simulating Production Environment

To test features that require external API integrations, you'll need to export the following environment variables:

```
export TogetherApiKey="mock-key"
export CerebrasApiKey="mock-key"
export CodexApiKey="mock-key"
export ElfaApiKey="mock-key"
```

### Developer Documentation

For developers looking to build and deploy their own agents:

1. [Agent Development Guide](docs/agent-development-guide.md)
2. [API Documentation](docs/available-apis-guide.md)
3. [Testing Framework](docs/testing-framework-guide.md)
4. [Deployment Guide](docs/deployment-guide.md)

# Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new agents and contributing to the platform.

Your agents will be automatically invoked based on user intent through our advanced routing system.

![morpheus ecosystem](images/morpheus-ecosystem@3x_green.png)

# MySuperAgent

## A Web-Based Platform for Building and Deploying AI Agents

A developer-focused platform that enables building, testing, and deploying AI agents. Powered by Python and React, with seamless integration of LLMs and Web3 capabilities.

**Note:** MySuperAgent serves as both a development sandbox and production platform for AI agent builders. The platform enables rapid prototyping and deployment of agents that can be automatically invoked based on user intent. For detailed documentation on specific agents, see the agent READMEs in the `/agents` directory.

![UI 1](images/mysuperagent-UI.png)

![UI 2](images/gasless-usdc-base-agent.png)

![UI 3](images/dca-strategy-agent.png)

![UI 4](images/image-generator.png)

![UI 5](images/tweet_sizzler.png)

![UI 6](images/real-time-info.png)

![UI 7](images/mor_rewards.png)

![UI 8](images/price-fetcher-realtime-news.png)

![UI 9](images/mysuperagent_chatpdf.png)

---

### Available Agents & Features

#### Generate Images with Stable Diffusion 🏞️

- "Generate an image of a cryptographically secure doggo"
- Powered by Stable Diffusion XL

#### Web3 Transaction Agents

##### Send Gasless USDC with Coinbase 🚚

- "Send USDC on Base"
  _- Note: Requires Coinbase API integration. See [setup instructions](submodules/agents/src/agents/base_agent/README.md)_

##### Dollar Cost Averaging (DCA) with Coinbase

- "DCA Strategy on Base"
- Automated trading strategies with comprehensive safety checks
- [Full Documentation](submodules/agents/src/agents/dca_agent/README.md)

#### Content Generation

##### AI-Powered Tweet Generator 🌶

- "Write a based tweet about Crypto and AI"
- Direct X/Twitter integration
- [Integration Guide](submodules/agents/src/agents/tweet_sizzler/README.md)

#### Market Intelligence

##### Real-time Company Analysis 🕸️

- "Real-time info about Company XYZ"

##### Crypto Market News

- "Latest news for USDC"

##### MOR Token Analytics 🏆

- "How many MOR rewards do I have?"

##### CoinGecko Price Integration 📈

- Real-time price, market cap, and TVL data
- "What's the price of ETH?"
- "What's the market cap of BTC?"

#### Document Analysis

##### PDF Analysis Engine 📄

- Upload and analyze documents
- Natural language querying
- "Can you give me a summary?"
- "What's the main point of the document?"

#### Token Research

##### Token Analytics Platform 🍿

- Chain-specific token activity monitoring
- "What are the most active tokens on Solana?"

---

## Getting Started

Visit [https://mysuperagent.io](https://mysuperagent.io) to access the platform.

### Requirements

- Modern web browser (Chrome, Firefox, Safari)
- Web3 wallet for blockchain interactions
- API keys for specific agent integrations (Coinbase, Twitter, etc)

### Developer Documentation

For developers looking to build and deploy their own agents:

1. [Agent Development Guide](docs/agent-development.md)
2. [API Documentation](docs/api-docs.md)
3. [Testing Framework](docs/testing.md)
4. [Deployment Guide](docs/deployment.md)

# Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new agents and contributing to the platform.

Your agents will be automatically invoked based on user intent through our advanced routing system.

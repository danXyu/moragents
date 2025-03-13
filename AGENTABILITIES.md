# MySuperAgent

Welcome to the world of agents! If you're interested in building and using agents, this document will guide you through the principles and
current projects underway.

### Principles:

1. **Agents Need Guardrails When Executing Decisions**: Agents should not be given all private key information or be allowed to enforce their own policy non-deterministically.
   This is due to the limitations of current LLMs in understanding complex transactions and the risk of [gaslighting](https://arxiv.org/abs/2311.04235).

### Current Projects:

1. **Architecture** (lachsbagel):

   1. Core Architecture
   2. HideNSeek: Model verification and fingerprinting algorithm
      1. Paper: [Hide and Seek: Fingerprinting Large Language Models with Evolutionary Learning](https://www.arxiv.org/abs/2408.02871)
   3. Parameter size estimation research

2. **Available Agents**:

   A. Data & Analysis

   - Crypto Market Data Agent: Real-time price and market data from CoinGecko
   - DexScreener Agent: DEX activity monitoring and token analytics
   - Codex Agent: On-chain analytics and token trends
   - Document Analysis Agent: PDF and document QA capabilities
   - Rugcheck Agent: Solana token safety analysis

   B. Social & News

   - Tweet Sizzler Agent: AI-powered tweet generation
   - Elfa Social Search: Social media monitoring for crypto
   - Crypto News Agent: Real-time crypto news analysis

   C. Trading & Transactions

   - Token Swap Agent: Cross-chain token swapping
   - Base Chain Agent: USDC and token transactions on Base

   D. Image Generation

   - Image Generation Agent: AI image creation and editing

   E. Morpheus Platform

   - MOR Rewards Agent: Track and manage MOR token rewards
   - Delegating Agent: Persona management and task coordination

### Decentralized Inference:

#### Non-Local Installation Agents for Permission-less Compute

Pending Lumerin's work. Eventually Agent Builders will be able to permission-lessly upload Agent and Model artifacts to a decentralized registry.

### How to Contribute:

- If you are working on an agent which can provide value through open models and relies on processing public data, please reach out to lachsbagel on Discord (link below)
  - Otherwise, you are more than welcome to publish your agent to the registry when it goes live pending Lumerin's work and any other necessary pieces which come up to better ensure security and verifiability of models in non-local execution environments.
- If you are working on security and/or verifiability of models and the runtime, please reach out to LachsBagel on the Morpheus Discord.
  - Currently looking at [Hyperbolic.xyz](https://hyperbolic.xyz) and [6079](https://docs.6079.ai/technology/6079-proof-of-inference-protocol). See more ecosystem members [here](https://mor.org/ecosystem).
  - LachsBagel is also working on a new algorithm, named [HideNSeek](https://github.com/MorpheusAIs/HideNSeek), which uses a Transformer specific heuristic for model verification
  - [6079](https://6079.ai/) will help with implementing the plumbing for [HideNSeek](https://github.com/MorpheusAIs/HideNSeek)

### Contact

Join the [Morpheus Discord](https://discord.com/invite/Dc26EFb6JK)

_Last Updated: January 16, 2025_

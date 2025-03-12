# API Documentation

This document outlines the REST API endpoints available in the MySuperAgent platform.

## Base URL

All API endpoints are available under:

```
https://api.mysuperagent.io
```

## Authentication

Authentication is required for all API endpoints. Use one of the following methods:

1. **API Key Authentication**:

   - Include the API key in the request header:

   ```
   X-API-Key: your_api_key_here
   ```

2. **Bearer Token Authentication**:
   - Include a bearer token in the Authorization header:
   ```
   Authorization: Bearer your_token_here
   ```

## Endpoints

### Agent Interaction

#### Chat with Agent

```
POST /api/chat
```

Request an agent to process a chat message.

**Request Body**:

```json
{
  "prompt": "Your request here",
  "agent_id": "optional_specific_agent_id",
  "conversation_id": "optional_ongoing_conversation_id",
  "context": {
    "optional_context_parameter1": "value1",
    "optional_context_parameter2": "value2"
  }
}
```

**Response**:

```json
{
  "id": "response_id",
  "content": "Agent response message",
  "tool_calls": [
    {
      "tool": "tool_name",
      "arguments": {
        "arg1": "value1"
      },
      "result": "Tool execution result"
    }
  ],
  "conversation_id": "conversation_id",
  "agent_id": "agent_that_processed_request",
  "error_message": null,
  "needs_info": false,
  "info_needed": null
}
```

#### Get Available Agents

```
GET /api/agents
```

Retrieve a list of all available agents.

**Response**:

```json
{
  "agents": [
    {
      "id": "base_agent",
      "name": "Base USDC Agent",
      "description": "Send USDC on Base blockchain",
      "capabilities": ["send_usdc", "check_balance"]
    },
    {
      "id": "dca_agent",
      "name": "DCA Strategy Agent",
      "description": "Dollar cost averaging cryptocurrency strategy",
      "capabilities": ["create_strategy", "get_strategies", "execute_strategy"]
    }
  ]
}
```

### Document Analysis

#### Upload Document

```
POST /api/documents/upload
```

Upload a document for analysis.

**Request Body**:

- Form data with `file` parameter
- Optional `metadata` parameter (JSON string)

**Response**:

```json
{
  "document_id": "doc_123456",
  "filename": "example.pdf",
  "size": 1245678,
  "page_count": 23,
  "status": "processing"
}
```

#### Query Document

```
POST /api/documents/{document_id}/query
```

Ask questions about a previously uploaded document.

**Request Body**:

```json
{
  "query": "What is the main topic of the document?",
  "include_citations": true
}
```

**Response**:

```json
{
  "answer": "The main topic of the document is artificial intelligence.",
  "citations": [
    {
      "page": 1,
      "text": "This paper explores the latest developments in artificial intelligence."
    },
    {
      "page": 3,
      "text": "Artificial intelligence has seen rapid growth in recent years."
    }
  ]
}
```

### Web3 Interactions

#### Get Token Balances

```
GET /api/wallet/{wallet_address}/balances
```

Retrieve token balances for a specific wallet address.

**Response**:

```json
{
  "eth_balance": "1.234",
  "tokens": [
    {
      "symbol": "USDC",
      "balance": "100.00",
      "chain": "Base"
    },
    {
      "symbol": "USDT",
      "balance": "50.00",
      "chain": "Ethereum"
    }
  ]
}
```

#### Submit Transaction

```
POST /api/transactions/submit
```

Submit a blockchain transaction.

**Request Body**:

```json
{
  "chain": "Base",
  "transaction_data": {
    "to": "0x1234...",
    "value": "10",
    "token": "USDC",
    "data": "0x..."
  },
  "authorization": {
    "type": "signature",
    "value": "0x..."
  }
}
```

**Response**:

```json
{
  "transaction_id": "tx_789012",
  "hash": "0xabcd...",
  "status": "pending",
  "estimated_confirmation_time": "30 seconds"
}
```

## Error Handling

All API endpoints follow consistent error handling patterns.

**Error Response Format**:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human readable error message",
    "details": {
      "additional_information": "More details about the error"
    }
  }
}
```

**Common Error Codes**:

- `400`: Bad Request - Missing or invalid parameters
- `401`: Unauthorized - Invalid or missing authentication
- `403`: Forbidden - Valid authentication but insufficient permissions
- `404`: Not Found - Resource not found
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server-side issue

## Rate Limits

API endpoints are subject to rate limits:

- 60 requests per minute per API key
- Higher rate limits available for premium tiers

Headers indicating rate limits are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1609459200
```

## Webhooks

Configure webhooks to receive real-time updates on specific events.

**Event Types**:

- `agent.response_complete`
- `document.processing_complete`
- `transaction.status_change`

**Webhook Payload Example**:

```json
{
  "event_type": "transaction.status_change",
  "timestamp": "2023-03-15T14:30:45Z",
  "data": {
    "transaction_id": "tx_789012",
    "new_status": "confirmed",
    "hash": "0xabcd..."
  }
}
```

## SDK Support

Official SDKs are available for:

- Python
- JavaScript/TypeScript
- Go

Visit [https://github.com/mysuperagent/sdks](https://github.com/mysuperagent/sdks) for SDK documentation and examples.

# Exposing an MCP Server with Supergateway and Ngrok

This guide walks you through exposing a local MCP server via Supergateway and Ngrok to create a publicly accessible endpoint.

## Prerequisites

- Node.js installed
- Basic command line knowledge

## Step 1: Start Your MCP Server with Supergateway

Supergateway converts stdio-based MCP servers to HTTP/SSE servers.

```bash
npx -y supergateway \
  --stdio "npx -y @modelcontextprotocol/simple-server" \
  --port 8000 \
  --cors
```

This command:

- Runs a simple MCP server over stdio
- Exposes it on port 8000
- Enables CORS for cross-origin requests

## Step 2: Set Up Ngrok

Ngrok creates a secure tunnel to your local machine.

1. Install Ngrok (if not already installed):

```bash
npm install -g ngrok
```

2. In a new terminal window, create a tunnel to your Supergateway:

```bash
ngrok http 8000
```

3. Ngrok will display a URL like: `https://abc123.ngrok.io`

## Step 3: Use the Ngrok URL

When configuring services like MySuperAgent to use your MCP:

1. Use the Ngrok URL **plus** `/sse` path:

   ```
   https://abc123.ngrok.io/sse
   ```

2. The `/sse` path is critical as this is where Supergateway exposes the event stream.

## Complete Example

```bash
# Terminal 1: Start Supergateway with simple MCP server
npx -y supergateway \
  --stdio "npx -y @modelcontextprotocol/simple-server" \
  --port 8000 \
  --cors

# Terminal 2: Start Ngrok
ngrok http 8000
```

Then in MySuperAgent:

1. Go to Tools > Add New Agent
2. Under MCP URL, enter the Ngrok URL + `/sse` (e.g., `https://abc123.ngrok.io/sse`)
3. Fill in agent details and save

## Important Notes

- Your computer must remain on and both terminals must stay open for the MCP server to remain accessible
- If you restart either process, you'll get a new Ngrok URL and will need to update it
- For production use, consider hosting this setup on a cloud server

## Advanced Options

```bash
# Add custom headers (useful for authentication)
npx -y supergateway \
  --stdio "npx -y @modelcontextprotocol/simple-server" \
  --port 8000 \
  --cors \
  --header "Authorization: Bearer your-token"

# Custom SSE path
npx -y supergateway \
  --stdio "npx -y @modelcontextprotocol/simple-server" \
  --port 8000 \
  --cors \
  --ssePath "/custom-sse-path"
```

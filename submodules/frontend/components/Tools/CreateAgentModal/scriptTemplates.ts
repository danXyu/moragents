/**
 * Template for the shell script that will start the MCP server and create a tunnel
 */
export const SCRIPT_TEMPLATE = `#!/bin/bash

# Script to start MCP server, expose via supergateway, and create ngrok tunnel
# Generated on {{DATE}}

echo "🚀 Starting MCP server and creating tunnel..."

# Check if required tools are installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed. Please install it first."
    exit 1
fi

if ! command -v npx &> /dev/null; then
    echo "❌ npx is not installed. Please install Node.js first."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo "📞 Cleaning up processes..."
    [[ -n $SUPERGATEWAY_PID ]] && kill $SUPERGATEWAY_PID
    exit 0
}

# Setup cleanup on script exit
trap cleanup EXIT INT TERM

# Set environment variables
{{ENV_VARS}}

# Generate a random port for supergateway to avoid collisions
GATEWAY_PORT=$(( 8000 + RANDOM % 1000 ))

# Start the MCP server via supergateway in the background
echo "🔧 Starting MCP server via supergateway: {{COMMAND}} {{ARGS}}"
npx -y supergateway --stdio "{{COMMAND}} {{ARGS}}" --port $GATEWAY_PORT &
SUPERGATEWAY_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to initialize (5 seconds)..."
sleep 5

# Get the ngrok URL using the ngrok API
echo "🔗 Creating ngrok tunnel..."
echo "✅ Your MCP server will be accessible via the ngrok URL shown below"
echo "📋 Copy the https:// URL and paste it in the MCP Server URL field"
echo "💡 Press Ctrl+C to stop the server and tunnel when you're done"
echo

# Start ngrok in the foreground
ngrok http $GATEWAY_PORT

# The script will not reach here unless ngrok exits unexpectedly
echo "❌ ngrok has exited. The MCP server may still be running in the background."
echo "Run 'ps aux | grep supergateway' to find and kill the process if needed."

# Keep the script running until supergateway exits
wait $SUPERGATEWAY_PID`;

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

# Function to cleanup on exit
cleanup() {
    echo "📞 Cleaning up processes..."
    [[ -n $SERVER_PID ]] && kill $SERVER_PID
    [[ -n $NGROK_PID ]] && kill $NGROK_PID
    exit 0
}

# Setup cleanup on script exit
trap cleanup EXIT INT TERM

# Set environment variables
{{ENV_VARS}}

# Start the MCP server in the background
echo "🔧 Starting MCP server: {{COMMAND}} {{ARGS}}"
{{COMMAND}} {{ARGS}} &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to initialize (5 seconds)..."
sleep 5

# Start ngrok tunnel
echo "🔗 Creating ngrok tunnel..."
ngrok http 3000 --log=stdout > ngrok.log &
NGROK_PID=$!

# Wait for ngrok to initialize
echo "⏳ Waiting for ngrok to initialize (5 seconds)..."
sleep 5

# Extract the ngrok URL
NGROK_URL=$(grep -o 'https://[0-9a-z\\-]*\\.ngrok\\.io' ngrok.log | head -1)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL. Check ngrok.log for details."
    exit 1
fi

echo "✅ Success! Your MCP server is running and accessible at:"
echo $NGROK_URL
echo
echo "📋 Copy this URL and paste it in the MCP Server URL field"
echo
echo "💡 Press Ctrl+C to stop the server and tunnel when you're done"

# Keep the script running
wait $SERVER_PID`;

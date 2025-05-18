#!/bin/bash

# Navigate to the application directory
cd /home/ec2-user/mysuperagent

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    # Install docker-compose
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
fi

# Start the application with docker-compose if available
if [ -f "docker-compose.yml" ]; then
    echo "Starting application with docker-compose..."
    docker-compose up -d
else
    # Start individual containers if no docker-compose
    echo "Starting application containers individually..."
    
    # Set up environment variables
    ACCOUNT_ID="816069170416"
    AWS_REGION="us-west-1"
    ECR_URL="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    AGENT_REPO="mysuperagent-agents"
    
    # Start backend
    docker run -d --restart always --name mysuperagent-backend -p 8888:5000 $ECR_URL/$AGENT_REPO:latest
fi

# Output container status
echo "Application started. Container status:"
docker ps
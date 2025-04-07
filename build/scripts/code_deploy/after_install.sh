#!/bin/bash

# Set up environment variables
ACCOUNT_ID="816069170416"
AWS_REGION="us-west-1"
ECR_URL="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
AGENT_REPO="mysuperagent-agents"
FRONTEND_REPO="mysuperagent-frontend"

# Pull the latest images
echo "Pulling latest Docker images..."
docker pull $ECR_URL/$AGENT_REPO:latest
docker pull $ECR_URL/$FRONTEND_REPO:latest

# Create docker-compose.yml if building on deploy
cat > /home/ec2-user/mysuperagent/docker-compose.yml << EOL
version: '3'

services:
  backend:
    image: $ECR_URL/$AGENT_REPO:latest
    restart: always
    ports:
      - "8888:5000"
    environment:
      - NODE_ENV=production

  frontend:
    image: $ECR_URL/$FRONTEND_REPO:latest
    restart: always
    ports:
      - "3333:80"
    depends_on:
      - backend

EOL

# Setup environment variables if needed
if [ -f "/home/ec2-user/mysuperagent/.env" ]; then
    cp /home/ec2-user/mysuperagent/.env /home/ec2-user/mysuperagent/.env.backup
fi

# If there's a .env file in the repository, use it
if [ -f "/home/ec2-user/mysuperagent/.env.template" ]; then
    cp /home/ec2-user/mysuperagent/.env.template /home/ec2-user/mysuperagent/.env
fi

# Ensure permissions are set correctly
chown -R ec2-user:ec2-user /home/ec2-user/mysuperagent
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

# Create docker-compose.yml with proper network configuration
cat > /home/ec2-user/mysuperagent/docker-compose.yml << EOL
version: '3'
services:
  backend:
    container_name: backend
    image: $ECR_URL/$AGENT_REPO:latest
    restart: always
    ports:
      - "8888:5000"
    environment:
      - ENV=staging
      - AWS_DEFAULT_REGION=us-west-1
      - AWS_REGION=us-west-1
    dns:
      - 8.8.8.8
      - 8.8.4.4
    tty: true
    stdin_open: true
  
  frontend:
    container_name: frontend
    image: $ECR_URL/$FRONTEND_REPO:latest
    restart: always
    ports:
      - "3333:80"
    environment:
      - NODE_ENV=production
      - APP_ENV=staging
      - AWS_DEFAULT_REGION=us-west-1
      - AWS_REGION=us-west-1
    dns:
      - 8.8.8.8
      - 8.8.4.4
    tty: true
    stdin_open: true

networks:
  default:
    external:
      name: mysuperagent-network
EOL

# Setup environment variables
cat > /home/ec2-user/mysuperagent/.env << EOL
ENV=staging
AWS_DEFAULT_REGION=us-west-1
NODE_ENV=production
APP_ENV=staging
AWS_DEFAULT_REGION=us-west-1
EOL

# Configure Docker network if it doesn't exist
if ! docker network inspect mysuperagent-network &>/dev/null; then
  echo "Creating Docker network..."
  docker network create --driver bridge --subnet 172.28.0.0/16 --gateway 172.28.0.1 --opt "com.docker.network.bridge.name"="docker1" mysuperagent-network
fi

# Ensure permissions are set correctly
chown -R ec2-user:ec2-user /home/ec2-user/mysuperagent
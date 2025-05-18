#!/bin/bash

# Navigate to the application directory
cd /home/ec2-user/mysuperagent

# Stop the application gracefully with docker-compose if available
if [ -f "docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
    echo "Stopping application with docker-compose..."
    docker-compose down --remove-orphans
else
    # Stop containers individually if no docker-compose
    echo "Stopping application containers individually..."
    
    # Stop backend
    if docker ps -q --filter "name=mysuperagent-backend" | grep -q .; then
        docker stop mysuperagent-backend
        docker rm mysuperagent-backend
    fi
    
    # Stop any other containers using the same images
    BACKEND_IMAGE_ID=$(docker images -q "*/*mysuperagent-agents:latest")
    
    if [ ! -z "$BACKEND_IMAGE_ID" ]; then
        BACKEND_CONTAINERS=$(docker ps -q --filter ancestor="$BACKEND_IMAGE_ID")
        if [ ! -z "$BACKEND_CONTAINERS" ]; then
            docker stop $BACKEND_CONTAINERS
            docker rm $BACKEND_CONTAINERS
        fi
    fi
fi

# Check if any containers are still running
if docker ps -q | grep -q .; then
    echo "Some containers are still running:"
    docker ps
else
    echo "All containers stopped successfully."
fi
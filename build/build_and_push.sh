#!/bin/bash

# Set AWS Region
AWS_REGION="us-west-1"

# AWS ECR Repository URL (Replace with your AWS account ID)
AWS_ACCOUNT_ID="586794444026"
ECR_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Define image names and their corresponding directories
IMAGE_NAMES=("agents" "mysuperagent-frontend")
IMAGE_DIRS=("../agents" "../frontend")

# Authenticate with AWS ECR
echo "Logging into AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

# Loop through images to build, tag, and push
for ((i=0; i<${#IMAGE_NAMES[@]}; i++)); do
    IMAGE_NAME="${IMAGE_NAMES[$i]}"
    IMAGE_DIR="${IMAGE_DIRS[$i]}"
    
    echo "Building $IMAGE_NAME in directory $IMAGE_DIR..."
    
    # Navigate to the project directory
    cd "$IMAGE_DIR" || { echo "Failed to navigate to $IMAGE_DIR"; exit 1; }

    # Build the Docker image
    if [ "$IMAGE_NAME" == "agents" ]; then
        docker build -t "$IMAGE_NAME" -f build/Dockerfile .
    else
        docker build -t "$IMAGE_NAME" .
    fi
    
    # Navigate back to the root directory
    cd - > /dev/null

    # Tag the image
    echo "Tagging $IMAGE_NAME..."
    docker tag "$IMAGE_NAME:latest" "$ECR_URL/$IMAGE_NAME:latest"

    # Push the image
    echo "Pushing $IMAGE_NAME to ECR..."
    docker push "$ECR_URL/$IMAGE_NAME:latest"

    echo "$IMAGE_NAME pushed successfully!"
done

echo "All images have been built and pushed successfully!"

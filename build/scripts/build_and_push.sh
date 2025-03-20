#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the root directory (parent of build/)
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Set AWS Region
AWS_REGION="us-west-1"

# AWS ECR Repository URL (Updated with new AWS account ID)
AWS_ACCOUNT_ID="816069170416"
ECR_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Define image names and their corresponding directories
IMAGE_NAMES=("mysuperagent-agents" "mysuperagent-frontend")
IMAGE_DIRS=("$ROOT_DIR/submodules/agents" "$ROOT_DIR/submodules/frontend")

# Authenticate with AWS ECR
echo "Logging into AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

# Create repositories if they don't exist
for IMAGE_NAME in "${IMAGE_NAMES[@]}"; do
    echo "Checking if repository $IMAGE_NAME exists..."
    if ! aws ecr describe-repositories --repository-names "$IMAGE_NAME" --region $AWS_REGION &> /dev/null; then
        echo "Creating repository $IMAGE_NAME..."
        aws ecr create-repository --repository-name "$IMAGE_NAME" --region $AWS_REGION
    else
        echo "Repository $IMAGE_NAME already exists"
    fi
done

# Loop through images to build, tag, and push
for ((i=0; i<${#IMAGE_NAMES[@]}; i++)); do
    IMAGE_NAME="${IMAGE_NAMES[$i]}"
    IMAGE_DIR="${IMAGE_DIRS[$i]}"
    
    echo "Building $IMAGE_NAME in directory $IMAGE_DIR..."
    
    # Navigate to the project directory
    cd "$IMAGE_DIR" || { echo "Failed to navigate to $IMAGE_DIR"; exit 1; }

    # Build the Docker image
    if [ "$IMAGE_NAME" == "mysuperagent-agents" ]; then
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
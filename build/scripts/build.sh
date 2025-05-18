#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the root directory (parent of build/)
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Set AWS Region
AWS_REGION="us-west-1"

# AWS ECR Repository URL
AWS_ACCOUNT_ID="816069170416"
ECR_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Define image name and directory
IMAGE_NAME="mysuperagent-agents"
IMAGE_DIR="$ROOT_DIR/../submodules/agents"

# Function to handle errors
handle_error() {
    echo "ERROR: $1"
    exit 1
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo "Options:"
    echo "  --help      Display this help message"
    exit 0
}

# Parse command line arguments
if [ $# -gt 0 ]; then
    case "$1" in
        --help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
fi

# Function to refresh AWS ECR authentication
refresh_aws_auth() {
    echo "Refreshing AWS ECR authentication..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL || handle_error "Failed to authenticate with AWS ECR"
}

# Initial authentication with AWS ECR
echo "Logging into AWS ECR..."
refresh_aws_auth

# Function to build and push the image
build_and_push_image() {    
    echo "Building $IMAGE_NAME in directory $IMAGE_DIR..."
    
    # Check if repository exists, create if it doesn't
    echo "Checking if repository $IMAGE_NAME exists..."
    if ! aws ecr describe-repositories --repository-names "$IMAGE_NAME" --region $AWS_REGION &> /dev/null; then
        echo "Creating repository $IMAGE_NAME..."
        aws ecr create-repository --repository-name "$IMAGE_NAME" --region $AWS_REGION || handle_error "Failed to create repository $IMAGE_NAME"
    else
        echo "Repository $IMAGE_NAME already exists"
    fi
    
    # Navigate to the project directory
    cd "$IMAGE_DIR" || handle_error "Failed to navigate to $IMAGE_DIR"

    # Build the Docker image
    docker build -t "$IMAGE_NAME" -f build/Dockerfile . || handle_error "Failed to build $IMAGE_NAME"
    
    # Navigate back to the root directory
    cd - > /dev/null

    # Tag the image
    echo "Tagging $IMAGE_NAME..."
    docker tag "$IMAGE_NAME:latest" "$ECR_URL/$IMAGE_NAME:latest" || handle_error "Failed to tag $IMAGE_NAME"

    # Push the image with improved retry logic
    echo "Pushing $IMAGE_NAME to ECR..."
    
    # Set retry parameters
    MAX_RETRIES=5
    RETRY_COUNT=0
    PUSH_SUCCESS=false
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$PUSH_SUCCESS" = false ]; do
        if [ $RETRY_COUNT -gt 0 ]; then
            echo "Retry attempt $RETRY_COUNT for pushing $IMAGE_NAME..."
            # Refresh AWS credentials before retry
            refresh_aws_auth
            # Longer delay before retry - increases with each attempt
            sleep $((5 * RETRY_COUNT))
        fi
        
        if docker push "$ECR_URL/$IMAGE_NAME:latest"; then
            PUSH_SUCCESS=true
            echo "$IMAGE_NAME pushed successfully!"
        else
            RETRY_COUNT=$((RETRY_COUNT + 1))
            
            if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
                handle_error "Failed to push $IMAGE_NAME after $MAX_RETRIES attempts. Check network connection to ECR."
            else
                echo "Push attempt failed. Will retry ($RETRY_COUNT/$MAX_RETRIES)..."
            fi
        fi
    done
}

# Build and push the image
echo "Starting build and push process..."
build_and_push_image

echo "Image has been built and pushed successfully!"
#!/bin/bash

# Set up environment variables
ACCOUNT_ID="816069170416"
AWS_REGION="us-west-1"
ECR_URL="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
AGENT_REPO="mysuperagent-agents"
FRONTEND_REPO="mysuperagent-frontend"

# Install CodeDeploy agent if not already installed
if [ ! -d "/opt/codedeploy-agent" ]; then
    yum update -y
    yum install -y ruby wget
    cd /home/ec2-user
    wget https://aws-codedeploy-$AWS_REGION.s3.$AWS_REGION.amazonaws.com/latest/install
    chmod +x ./install
    ./install auto
    systemctl enable codedeploy-agent
    systemctl start codedeploy-agent
fi

# Create application directory if it doesn't exist
if [ ! -d "/home/ec2-user/mysuperagent" ]; then
    mkdir -p /home/ec2-user/mysuperagent
fi

# Clean up the deployment directory
rm -rf /home/ec2-user/mysuperagent/*

# Make sure Docker is running
systemctl start docker
systemctl enable docker

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL
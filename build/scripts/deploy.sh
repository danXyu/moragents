#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
AWS_REGION="us-west-1"
ACCOUNT_ID="816069170416"
VERSION=$(date +%Y%m%d%H%M%S)

# Default to staging if no environment specified
ENVIRONMENT="staging"

# Function to show usage
usage() {
    echo "Usage: $0 [--staging|--prod]"
    echo "  --staging   Deploy to staging environment (default)"
    echo "  --prod      Deploy to production environment"
    echo "  --help      Show this help message"
    exit 1
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --staging) ENVIRONMENT="staging" ;;
        --prod) ENVIRONMENT="prod" ;;
        --help) usage ;;
        *) echo "Unknown parameter: $1"; usage ;;
    esac
    shift
done

# Set environment-specific variables
if [ "$ENVIRONMENT" == "staging" ]; then
    S3_BUCKET="mysuperagent-staging-deploy-${ACCOUNT_ID}"
    APPLICATION_NAME="MySuperAgentApp-Staging"
    DEPLOYMENT_GROUP="MySuperAgentDeploymentGroup-Staging"
else
    S3_BUCKET="mysuperagent-deploy-${ACCOUNT_ID}"
    APPLICATION_NAME="MySuperAgentApp"
    DEPLOYMENT_GROUP="MySuperAgentDeploymentGroup"
fi

DEPLOYMENT_CONFIG="CodeDeployDefault.AllAtOnce"

echo "Starting deployment process for MySuperAgent (Environment: $ENVIRONMENT, Version: $VERSION)"

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo "Working in temporary directory: $TEMP_DIR"

# Create the AppSpec file with environment variables
cat > $TEMP_DIR/appspec.yml << EOF
version: 0.0
os: linux
files:
  - source: /scripts
    destination: /tmp/deployment
hooks:
  ApplicationStop:
    - location: scripts/stop_application.sh
      timeout: 300
      runas: root
  BeforeInstall:
    - location: scripts/before_install.sh
      timeout: 300
      runas: root
  AfterInstall:
    - location: scripts/after_install.sh
      timeout: 600
      runas: root
  ApplicationStart:
    - location: scripts/start_application.sh
      timeout: 300
      runas: root
EOF

# Create scripts directory and copy deployment scripts
mkdir -p $TEMP_DIR/scripts

# Copy deployment scripts from code_deploy directory
DEPLOY_SCRIPTS_DIR="$SCRIPT_DIR/code_deploy"
echo "Copying deployment scripts from $DEPLOY_SCRIPTS_DIR..."

for script in stop_application.sh before_install.sh after_install.sh start_application.sh; do
    if [ ! -f "$DEPLOY_SCRIPTS_DIR/$script" ]; then
        echo "Error: Required script $script not found in $DEPLOY_SCRIPTS_DIR"
        exit 1
    fi
    
    # Copy script and inject environment variable after shebang
    awk -v env="$ENVIRONMENT" 'NR==1{print; print "export DEPLOY_ENV=\047" env "\047"} NR!=1{print}' "$DEPLOY_SCRIPTS_DIR/$script" > "$TEMP_DIR/scripts/$script"
    chmod +x "$TEMP_DIR/scripts/$script"
done

echo "Deployment scripts copied and configured successfully."

# Create the deployment bundle
echo "Creating deployment bundle..."
BUNDLE_FILE="/tmp/mysuperagent-${ENVIRONMENT}-deployment-${VERSION}.zip"
(cd $TEMP_DIR && zip -r $BUNDLE_FILE .)

# Upload bundle to S3
echo "Uploading bundle to S3..."
aws s3 cp $BUNDLE_FILE s3://$S3_BUCKET/

# Create the deployment
echo "Creating deployment..."
DEPLOYMENT_ID=$(aws deploy create-deployment \
    --application-name $APPLICATION_NAME \
    --deployment-group-name $DEPLOYMENT_GROUP \
    --deployment-config-name $DEPLOYMENT_CONFIG \
    --s3-location bucket=$S3_BUCKET,key=$(basename $BUNDLE_FILE),bundleType=zip \
    --query 'deploymentId' \
    --output text)

echo "Deployment created with ID: $DEPLOYMENT_ID"
echo "Tracking deployment status..."

# Track the deployment status
STATUS="InProgress"
while [ "$STATUS" == "InProgress" ] || [ "$STATUS" == "Created" ] || [ "$STATUS" == "Queued" ] || [ "$STATUS" == "Ready" ]; do
    echo "Deployment status: $STATUS"
    sleep 10
    STATUS=$(aws deploy get-deployment \
        --deployment-id $DEPLOYMENT_ID \
        --query 'deploymentInfo.status' \
        --output text)
done

if [ "$STATUS" == "Succeeded" ]; then
    echo "Deployment to $ENVIRONMENT succeeded!"
else
    echo "Deployment to $ENVIRONMENT failed with status: $STATUS"
    aws deploy get-deployment --deployment-id $DEPLOYMENT_ID
    exit 1
fi

# Clean up
rm -rf $TEMP_DIR
rm -f $BUNDLE_FILE

echo "Deployment process completed for $ENVIRONMENT environment"
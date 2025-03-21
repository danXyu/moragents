#!/bin/bash
set -e

# Configuration
AWS_REGION="us-west-1"
ACCOUNT_ID="816069170416"
S3_BUCKET="mysuperagent-deploy-${ACCOUNT_ID}"
APPLICATION_NAME="MySuperAgentApp"
DEPLOYMENT_GROUP="MySuperAgentDeploymentGroup"
DEPLOYMENT_CONFIG="CodeDeployDefault.AllAtOnce"
VERSION=$(date +%Y%m%d%H%M%S)

echo "Starting deployment process for MySuperAgent (version: $VERSION)"

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo "Working in temporary directory: $TEMP_DIR"

# Create the AppSpec file
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

# Create scripts directory and copy your existing scripts
mkdir -p $TEMP_DIR/scripts

# Copy your existing deployment scripts (assuming they're in the current directory)
echo "Copying existing deployment scripts..."
cp before_install.sh $TEMP_DIR/scripts/
cp after_install.sh $TEMP_DIR/scripts/
cp start_application.sh $TEMP_DIR/scripts/
cp stop_application.sh $TEMP_DIR/scripts/

# Make sure scripts are executable
chmod +x $TEMP_DIR/scripts/*.sh

# Create the deployment bundle
echo "Creating deployment bundle..."
BUNDLE_FILE="/tmp/mysuperagent-deployment-${VERSION}.zip"
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
    echo "Deployment succeeded!"
else
    echo "Deployment failed with status: $STATUS"
    exit 1
fi

# Clean up
rm -rf $TEMP_DIR
rm -f $BUNDLE_FILE

echo "Deployment process completed"
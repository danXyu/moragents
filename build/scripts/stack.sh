#!/bin/bash

# Default region
REGION="us-west-1"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Function to display usage information
function show_usage {
    echo "Usage: $0 [prod|staging|monitoring] [--delete]"
    echo ""
    echo "Options:"
    echo "  prod        Manage the production stack (MySuperAgent-Infrastructure)"
    echo "  staging     Manage the staging stack (MySuperAgent-Infrastructure-Staging)"
    echo "  monitoring  Manage the monitoring stack (MySuperAgent-Monitoring)"
    echo "  jenkins     Manage the Jenkins stack (MySuperAgent-Jenkins)"
    echo "  --delete    Delete the specified stack instead of creating/updating it"
    echo ""
    exit 1
}

# Check if an argument was provided
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    show_usage
fi

# Check for delete flag
DELETE_FLAG=false
if [ $# -eq 2 ] && [ "$2" == "--delete" ]; then
    DELETE_FLAG=true
elif [ $# -eq 2 ]; then
    echo "Error: Unrecognized second argument '$2'"
    show_usage
fi

# Set variables based on the argument
case "$1" in
    prod)
        STACK_NAME="MySuperAgent-Infrastructure"
        TEMPLATE_FILE="${SCRIPT_DIR}/../mysuperagent-stack-prod.yaml"
        echo "Selected: Production stack"
        echo "Using template file: $TEMPLATE_FILE"
        ;;
    staging)
        STACK_NAME="MySuperAgent-Infrastructure-Staging"
        TEMPLATE_FILE="${SCRIPT_DIR}/../mysuperagent-stack-staging.yaml"
        echo "Selected: Staging stack"
        echo "Using template file: $TEMPLATE_FILE"
        ;;
    monitoring)
        STACK_NAME="MySuperAgent-Monitoring"
        TEMPLATE_FILE="${SCRIPT_DIR}/../mysuperagent-cloudwatch.yaml"
        echo "Selected: Monitoring stack"
        echo "Using template file: $TEMPLATE_FILE"
        ;;
    jenkins)
        STACK_NAME="MySuperAgent-Jenkins"
        TEMPLATE_FILE="${SCRIPT_DIR}/../mysuperagent-jenkins.yaml"
        echo "Selected: Jenkins stack"
        echo "Using template file: $TEMPLATE_FILE"
        ;;
    *)
        echo "Error: Invalid stack type '$1'"
        show_usage
        ;;
esac

# Check if template file exists (only if not deleting)
if [ "$DELETE_FLAG" = false ] && [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file $TEMPLATE_FILE not found."
    echo "Please ensure the CloudFormation template exists at this location."
    exit 1
fi

# Handle deletion if requested
if [ "$DELETE_FLAG" = true ]; then
    echo "WARNING: You are about to DELETE the $STACK_NAME stack!"
    read -p "Are you sure you want to proceed with deletion? (yes/no): " CONFIRM_DELETE
    
    if [[ $CONFIRM_DELETE != "yes" ]]; then
        echo "Deletion canceled."
        exit 0
    fi
    
    echo "Deleting stack $STACK_NAME..."
    aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
    
    echo "Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION
    
    # Check if deletion was successful
    if [ $? -eq 0 ]; then
        echo "Stack $STACK_NAME successfully deleted."
        exit 0
    else
        echo "Error deleting stack $STACK_NAME. Check AWS console for details."
        exit 1
    fi
fi

# Check if the stack exists
STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION 2>&1 || echo "NOT_EXISTS")

# Validate the template
echo "Validating CloudFormation template..."
VALIDATION=$(aws cloudformation validate-template --template-body file://$TEMPLATE_FILE --region $REGION 2>&1)
if [ $? -ne 0 ]; then
    echo "Template validation failed:"
    echo "$VALIDATION"
    exit 1
fi
echo "Template validation successful!"

# If stack doesn't exist, create it
if [[ $STACK_EXISTS == *"does not exist"* ]] || [[ $STACK_EXISTS == *"NOT_EXISTS"* ]]; then
    echo "Stack $STACK_NAME does not exist. Creating new stack..."
    
    # Create the stack
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region $REGION
    
    # Wait for stack creation to complete
    echo "Waiting for stack creation to complete... This may take several minutes."
    aws cloudformation wait stack-create-complete \
        --stack-name $STACK_NAME \
        --region $REGION
    
    # Check if stack creation was successful
    STACK_STATUS=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].StackStatus' \
        --output text)
    
    if [ "$STACK_STATUS" = "CREATE_COMPLETE" ]; then
        echo "Stack creation completed successfully!"
        
        # Display outputs
        echo "Stack outputs:"
        aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --region $REGION \
            --query 'Stacks[0].Outputs' \
            --output table
        
        exit 0
    else
        echo "Stack creation failed with status: $STACK_STATUS"
        
        # Get the failure reason
        FAILURE_REASON=$(aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --region $REGION \
            --query 'Stacks[0].StackStatusReason' \
            --output text)
        
        echo "Failure reason: $FAILURE_REASON"
        exit 1
    fi
else
    # Stack exists, proceed with update via change set
    echo "Stack $STACK_NAME exists. Proceeding with update..."
    
    # Create a change set to see the upcoming changes
    CHANGE_SET_NAME="${STACK_NAME}-ChangeSet-$(date +%Y%m%d%H%M%S)"
    echo "Creating change set '$CHANGE_SET_NAME'..."
    aws cloudformation create-change-set \
        --stack-name $STACK_NAME \
        --change-set-name $CHANGE_SET_NAME \
        --template-body file://$TEMPLATE_FILE \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region $REGION
    
    # Wait for change set creation to complete
    echo "Waiting for change set creation to complete..."
    aws cloudformation wait change-set-create-complete \
        --stack-name $STACK_NAME \
        --change-set-name $CHANGE_SET_NAME \
        --region $REGION
    
    # Check if change set was created successfully
    CHANGE_SET_STATUS=$(aws cloudformation describe-change-set \
        --stack-name $STACK_NAME \
        --change-set-name $CHANGE_SET_NAME \
        --region $REGION \
        --query 'Status' \
        --output text 2>/dev/null)
    
    if [ "$CHANGE_SET_STATUS" = "FAILED" ]; then
        # Get the status reason
        STATUS_REASON=$(aws cloudformation describe-change-set \
            --stack-name $STACK_NAME \
            --change-set-name $CHANGE_SET_NAME \
            --region $REGION \
            --query 'StatusReason' \
            --output text)
        
        if [[ "$STATUS_REASON" == *"didn't contain changes"* ]]; then
            echo "No changes detected in the stack."
            
            # Clean up the change set
            aws cloudformation delete-change-set \
                --stack-name $STACK_NAME \
                --change-set-name $CHANGE_SET_NAME \
                --region $REGION
            
            exit 0
        else
            echo "Change set creation failed: $STATUS_REASON"
            exit 1
        fi
    fi
    
    # Display the changes
    echo "Changes to be applied:"
    aws cloudformation describe-change-set \
        --stack-name $STACK_NAME \
        --change-set-name $CHANGE_SET_NAME \
        --region $REGION
    
    # Execute the change set without confirmation
    echo "Executing change set..."
    aws cloudformation execute-change-set \
        --stack-name $STACK_NAME \
        --change-set-name $CHANGE_SET_NAME \
        --region $REGION
    
    # Wait for stack update to complete
    echo "Updating stack... This may take several minutes."
    aws cloudformation wait stack-update-complete \
        --stack-name $STACK_NAME \
        --region $REGION
    
    # Check if stack update was successful
    STACK_STATUS=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].StackStatus' \
        --output text)
    
    if [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
        echo "Stack update completed successfully!"
        
        # Display outputs
        echo "Stack outputs:"
        aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --region $REGION \
            --query 'Stacks[0].Outputs' \
            --output table
        
        exit 0
    else
        echo "Stack update failed with status: $STACK_STATUS"
        
        # Get the failure reason
        FAILURE_REASON=$(aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --region $REGION \
            --query 'Stacks[0].StackStatusReason' \
            --output text)
        
        echo "Failure reason: $FAILURE_REASON"
        exit 1
    fi
fi
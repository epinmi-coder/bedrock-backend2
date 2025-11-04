#!/bin/bash
# Deployment script for Bedrock Backend

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DEPLOYMENT_ENVIRONMENT="${1:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${DEPLOYMENT_ENVIRONMENT}-bedrock-backend"

echo -e "${BLUE}=========================================="
echo "Bedrock Backend Deployment Script"
echo "=========================================="
echo "Environment: $DEPLOYMENT_ENVIRONMENT"
echo "AWS Region: $AWS_REGION"
echo "Stack Name: $STACK_NAME"
echo "==========================================${NC}"

# Check AWS credentials
echo ""
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials valid${NC}"

# Check if required secrets are set
echo ""
echo "Checking required environment variables..."
REQUIRED_VARS=("DATABASE_URL" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "EC2_KEY_PAIR_NAME")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}✗ Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please set these variables and try again."
    exit 1
fi
echo -e "${GREEN}✓ All required variables are set${NC}"

# Validate CloudFormation template
echo ""
echo "Validating CloudFormation template..."
if aws cloudformation validate-template \
    --template-body file://cloudformation/infrastructure.yaml \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Template is valid${NC}"
else
    echo -e "${RED}✗ Template validation failed${NC}"
    exit 1
fi

# Check if stack exists
echo ""
echo "Checking if stack exists..."
if aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    STACK_EXISTS=true
    echo -e "${YELLOW}Stack exists - will update${NC}"
else
    STACK_EXISTS=false
    echo -e "${YELLOW}Stack does not exist - will create${NC}"
fi

# Deploy stack
echo ""
echo "Deploying CloudFormation stack..."
if [ "$STACK_EXISTS" = true ]; then
    COMMAND="update-stack"
    WAIT_COMMAND="stack-update-complete"
else
    COMMAND="create-stack"
    WAIT_COMMAND="stack-create-complete"
fi

aws cloudformation "$COMMAND" \
    --stack-name "$STACK_NAME" \
    --template-body file://cloudformation/infrastructure.yaml \
    --parameters \
        ParameterKey=Environment,ParameterValue="$DEPLOYMENT_ENVIRONMENT" \
        ParameterKey=InstanceType,ParameterValue=t3.small \
        ParameterKey=KeyPairName,ParameterValue="$EC2_KEY_PAIR_NAME" \
        ParameterKey=DatabaseURL,ParameterValue="$DATABASE_URL" \
        ParameterKey=AWSAccessKeyId,ParameterValue="$AWS_ACCESS_KEY_ID" \
        ParameterKey=AWSSecretAccessKey,ParameterValue="$AWS_SECRET_ACCESS_KEY" \
        ParameterKey=AllowedOrigins,ParameterValue="${ALLOWED_ORIGINS:-[\"https://da57vzl0vgd9l.cloudfront.net\"]}" \
        ParameterKey=MinSize,ParameterValue="${MIN_SIZE:-1}" \
        ParameterKey=MaxSize,ParameterValue="${MAX_SIZE:-4}" \
        ParameterKey=DesiredCapacity,ParameterValue="${DESIRED_CAPACITY:-2}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION" \
    --tags \
        Key=Environment,Value="$DEPLOYMENT_ENVIRONMENT" \
        Key=Project,Value=bedrock-backend \
        Key=ManagedBy,Value=Script || echo "No changes detected"

# Wait for stack operation to complete
echo ""
echo "Waiting for stack operation to complete..."
aws cloudformation wait "$WAIT_COMMAND" \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" 2>/dev/null || echo "Stack operation completed"

# Get stack outputs
echo ""
echo -e "${GREEN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[].[OutputKey,OutputValue]' \
    --output table

# Get Load Balancer URL
ALB_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text)

echo ""
echo -e "${BLUE}=========================================="
echo "Application URLs:"
echo "==========================================${NC}"
echo "🌐 Load Balancer: $ALB_URL"
echo "🏥 Health Check: $ALB_URL/health"
echo "📚 API Docs: $ALB_URL/api/v1/docs"
echo ""
echo -e "${YELLOW}Note: It may take a few minutes for the application to be fully available${NC}"

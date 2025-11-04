#!/bin/bash
# Rollback deployment script

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

DEPLOYMENT_ENVIRONMENT="${1:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${DEPLOYMENT_ENVIRONMENT}-bedrock-backend"

echo -e "${BLUE}=========================================="
echo "Bedrock Backend Rollback Script"
echo "=========================================="
echo "Environment: $DEPLOYMENT_ENVIRONMENT"
echo "Stack Name: $STACK_NAME"
echo "==========================================${NC}"

# Get deployment bucket
DEPLOYMENT_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DeploymentBucketName`].OutputValue' \
    --output text)

if [ -z "$DEPLOYMENT_BUCKET" ]; then
    echo -e "${RED}✗ Could not find deployment bucket${NC}"
    exit 1
fi

echo "Deployment Bucket: $DEPLOYMENT_BUCKET"

# List available releases
echo ""
echo "Available releases:"
aws s3 ls s3://$DEPLOYMENT_BUCKET/releases/ --region "$AWS_REGION" | tail -10

# Get previous release (second to last)
PREVIOUS_RELEASE=$(aws s3 ls s3://$DEPLOYMENT_BUCKET/releases/ --region "$AWS_REGION" | tail -2 | head -1 | awk '{print $2}' | sed 's/\///')

if [ -z "$PREVIOUS_RELEASE" ]; then
    echo -e "${RED}✗ No previous release found${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Rolling back to: $PREVIOUS_RELEASE${NC}"
read -p "Continue? (y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi

# Copy previous release to latest
echo ""
echo "Copying previous release to latest..."
aws s3 cp s3://$DEPLOYMENT_BUCKET/releases/$PREVIOUS_RELEASE/app.tar.gz \
    s3://$DEPLOYMENT_BUCKET/latest/app.tar.gz \
    --region "$AWS_REGION"

# Get ASG name
ASG_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`AutoScalingGroupName`].OutputValue' \
    --output text)

# Get instance IDs
INSTANCE_IDS=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names "$ASG_NAME" \
    --region "$AWS_REGION" \
    --query 'AutoScalingGroups[0].Instances[?HealthStatus==`Healthy`].InstanceId' \
    --output text)

echo ""
echo "Deploying to instances..."
for INSTANCE_ID in $INSTANCE_IDS; do
    echo "Deploying to: $INSTANCE_ID"
    
    aws ssm send-command \
        --instance-ids "$INSTANCE_ID" \
        --document-name "AWS-RunShellScript" \
        --parameters 'commands=[
            "cd /opt/bedrock-backend",
            "sudo -u bedrock bash -c \"aws s3 cp s3://'$DEPLOYMENT_BUCKET'/latest/app.tar.gz /tmp/app.tar.gz --region '$AWS_REGION'\"",
            "sudo -u bedrock bash -c \"tar -xzf /tmp/app.tar.gz -C /opt/bedrock-backend --overwrite\"",
            "sudo -u bedrock bash -c \"source venv/bin/activate && pip install -r requirements.txt\"",
            "sudo supervisorctl restart bedrock-backend"
        ]' \
        --region "$AWS_REGION" \
        --output text
done

echo ""
echo -e "${GREEN}=========================================="
echo "✓ Rollback initiated"
echo "==========================================${NC}"
echo ""
echo "Waiting for instances to stabilize..."
sleep 30

# Health check
echo "Running health check..."
bash scripts/health-check.sh

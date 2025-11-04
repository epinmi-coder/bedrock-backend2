#!/bin/bash
# Cleanup script - removes old deployment artifacts

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
DEPLOYMENT_ENVIRONMENT="${1:-production}"
STACK_NAME="${DEPLOYMENT_ENVIRONMENT}-bedrock-backend"
DAYS_TO_KEEP="${2:-30}"

echo "=========================================="
echo "Cleanup Script"
echo "=========================================="
echo "Environment: $DEPLOYMENT_ENVIRONMENT"
echo "Days to keep: $DAYS_TO_KEEP"
echo "=========================================="

# Get deployment bucket
DEPLOYMENT_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DeploymentBucketName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -z "$DEPLOYMENT_BUCKET" ]; then
    echo "✗ Could not find deployment bucket"
    exit 1
fi

echo "Deployment Bucket: $DEPLOYMENT_BUCKET"
echo ""

# Calculate cutoff date
CUTOFF_DATE=$(date -d "$DAYS_TO_KEEP days ago" +%Y%m%d 2>/dev/null || date -v-${DAYS_TO_KEEP}d +%Y%m%d)

echo "Removing releases older than $CUTOFF_DATE..."

# List and delete old releases
aws s3 ls s3://$DEPLOYMENT_BUCKET/releases/ --region "$AWS_REGION" | while read -r line; do
    RELEASE_DATE=$(echo "$line" | awk '{print $2}' | cut -d'-' -f1)
    RELEASE_PATH=$(echo "$line" | awk '{print $2}')
    
    if [ "$RELEASE_DATE" -lt "$CUTOFF_DATE" ]; then
        echo "Deleting: $RELEASE_PATH"
        aws s3 rm s3://$DEPLOYMENT_BUCKET/releases/$RELEASE_PATH --recursive --region "$AWS_REGION"
    fi
done

echo ""
echo "✓ Cleanup completed"

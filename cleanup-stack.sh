#!/bin/bash
# Cleanup failed CloudFormation stack
# Run this if deployment times out or fails

STACK_NAME="bedrock-backend-stack"
REGION="us-east-2"

echo "🔍 Checking stack status..."
STACK_STATUS=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query "Stacks[0].StackStatus" \
  --output text 2>/dev/null)

if [ -z "$STACK_STATUS" ]; then
  echo "✅ No stack found - ready for fresh deployment"
  exit 0
fi

echo "📊 Current stack status: $STACK_STATUS"

if [[ "$STACK_STATUS" == *"IN_PROGRESS"* ]]; then
  echo "⚠️ Stack operation is still in progress. Wait for it to complete before deleting."
  echo ""
  echo "🔍 Recent events:"
  aws cloudformation describe-stack-events \
    --stack-name $STACK_NAME \
    --region $REGION \
    --max-items 10 \
    --query "StackEvents[*].[Timestamp,LogicalResourceId,ResourceStatus]" \
    --output table
  exit 1
fi

if [[ "$STACK_STATUS" == "ROLLBACK_COMPLETE" ]] || [[ "$STACK_STATUS" == "CREATE_FAILED" ]] || [[ "$STACK_STATUS" == *"ROLLBACK"* ]]; then
  echo "🗑️ Deleting failed stack..."
  aws cloudformation delete-stack \
    --stack-name $STACK_NAME \
    --region $REGION
  
  echo "⏳ Waiting for stack deletion..."
  aws cloudformation wait stack-delete-complete \
    --stack-name $STACK_NAME \
    --region $REGION
  
  echo "✅ Stack deleted successfully. Ready for fresh deployment."
else
  echo "📋 Stack is in status: $STACK_STATUS"
  echo "💡 Only delete if status is ROLLBACK_COMPLETE or CREATE_FAILED"
fi

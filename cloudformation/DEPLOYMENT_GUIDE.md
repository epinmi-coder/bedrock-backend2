# Bedrock Backend Deployment Guide

## Overview

This guide covers deploying the Bedrock Backend application to AWS EC2 using CloudFormation, Docker, with full Celery support for email processing.

## Architecture

```
Internet → ALB (Port 80/443) → EC2 Instance (Auto Scaling Group)
                                   ├─ FastAPI Container (Port 8000)
                                   ├─ Celery Worker Container
                                   └─ Redis Container (Celery Broker)

                                 (Docker Network: bedrock-network)
```

## Prerequisites

### 1. AWS Account Setup

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- EC2 Key Pair created in your target region

### 2. ECR Repository

Create an ECR repository for the Docker image:

```bash
aws ecr create-repository \
  --repository-name bedrock-backend \
  --region us-east-2
```

### 3. RDS PostgreSQL Database

Set up a PostgreSQL database (RDS recommended):

- PostgreSQL 14+ with psycopg3 support
- Note the connection string format: `postgresql+psycopg://user:password@host:5432/database?sslmode=require`

### 4. Email Configuration (SMTP)

For Gmail:

1. Enable 2-Factor Authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character app password (no spaces)

For other providers:

- Use appropriate SMTP server and port
- Ensure credentials are ready

## Step-by-Step Deployment

### Step 1: Build and Push Docker Image

```bash
# Navigate to backend directory
cd bedrock-backend

# Configure AWS credentials
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-2

# Login to ECR
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com

# Build Docker image
docker build -t bedrock-backend:latest .

# Tag for ECR
docker tag bedrock-backend:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/bedrock-backend:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/bedrock-backend:latest
```

### Step 2: Prepare Parameters File

Copy and customize the parameters file:

```bash
cp cloudformation/parameters.example.json cloudformation/parameters.json
```

Edit `parameters.json` with your actual values:

```json
[
  {
    "ParameterKey": "Environment",
    "ParameterValue": "production"
  },
  {
    "ParameterKey": "InstanceType",
    "ParameterValue": "t3.small"
  },
  {
    "ParameterKey": "KeyPairName",
    "ParameterValue": "your-key-pair-name"
  },
  {
    "ParameterKey": "DockerImage",
    "ParameterValue": "123456789012.dkr.ecr.us-east-2.amazonaws.com/bedrock-backend:latest"
  },
  {
    "ParameterKey": "DatabaseURL",
    "ParameterValue": "postgresql+psycopg://user:password@rds-endpoint:5432/dbname?sslmode=require"
  },
  {
    "ParameterKey": "AWSAccessKeyId",
    "ParameterValue": "YOUR_AWS_ACCESS_KEY"
  },
  {
    "ParameterKey": "AWSSecretAccessKey",
    "ParameterValue": "YOUR_AWS_SECRET_KEY"
  },
  {
    "ParameterKey": "JWTSecret",
    "ParameterValue": "generate-with-python-secrets"
  },
  {
    "ParameterKey": "FrontendDomain",
    "ParameterValue": "yourdomain.com"
  },
  {
    "ParameterKey": "MailServer",
    "ParameterValue": "smtp.gmail.com"
  },
  {
    "ParameterKey": "MailPort",
    "ParameterValue": "587"
  },
  {
    "ParameterKey": "MailUsername",
    "ParameterValue": "your-email@gmail.com"
  },
  {
    "ParameterKey": "MailPassword",
    "ParameterValue": "your-16-char-app-password"
  },
  {
    "ParameterKey": "MailFrom",
    "ParameterValue": "noreply@yourdomain.com"
  },
  {
    "ParameterKey": "MailFromName",
    "ParameterValue": "Security Platform"
  },
  {
    "ParameterKey": "Domain",
    "ParameterValue": "api.yourdomain.com"
  },
  {
    "ParameterKey": "VpcId",
    "ParameterValue": "vpc-xxxxx"
  },
  {
    "ParameterKey": "SubnetIds",
    "ParameterValue": "subnet-xxxxx,subnet-yyyyy"
  }
]
```

**Important Notes:**

- `VpcId`: Use your default VPC or existing VPC ID
- `SubnetIds`: Must be in **at least 2 different availability zones** for ALB
- `DatabaseURL`: Use `postgresql+psycopg://` (not `postgresql+psycopg_async://`) for the connection string
- `InstanceType`: Use `t3.small` or larger to handle 3 containers

### Step 3: Generate JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Get VPC and Subnet Information

```bash
# Get default VPC ID
aws ec2 describe-vpcs --filters "Name=is-default,Values=true" \
  --query "Vpcs[0].VpcId" --output text

# Get subnet IDs in different AZs
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=YOUR_VPC_ID" \
  --query "Subnets[*].[SubnetId,AvailabilityZone]" \
  --output table
```

Select at least 2 subnets from different availability zones.

### Step 5: Deploy CloudFormation Stack

```bash
# Validate template
aws cloudformation validate-template \
  --template-body file://cloudformation/bedrock-docker-ec2.yaml

# Create stack
aws cloudformation create-stack \
  --stack-name bedrock-backend-stack \
  --template-body file://cloudformation/bedrock-docker-ec2.yaml \
  --parameters file://cloudformation/parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-2

# Monitor stack creation
aws cloudformation wait stack-create-complete \
  --stack-name bedrock-backend-stack \
  --region us-east-2

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name bedrock-backend-stack \
  --query "Stacks[0].Outputs" \
  --output table
```

### Step 6: Verify Deployment

```bash
# Get ALB DNS
ALB_DNS=$(aws cloudformation describe-stacks \
  --stack-name bedrock-backend-stack \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
  --output text)

# Test health endpoint
curl http://${ALB_DNS}/health

# Expected response:
# {"status":"healthy","timestamp":"2025-11-06T..."}
```

### Step 7: Verify Containers on EC2

```bash
# Get instance ID
INSTANCE_ID=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names production-bedrock-asg \
  --query "AutoScalingGroups[0].Instances[0].InstanceId" \
  --output text)

# Connect via SSM
aws ssm start-session --target $INSTANCE_ID

# Once connected, check containers
docker ps

# Expected output:
# bedrock-backend        (FastAPI)
# bedrock-celery-worker  (Celery)
# redis                  (Redis)

# Check Celery worker logs
docker logs bedrock-celery-worker

# Check FastAPI logs
docker logs bedrock-backend

# Check Redis logs
docker logs redis
```

## GitHub Actions CI/CD Setup

### Required GitHub Secrets

Add these secrets to your GitHub repository:

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### Deployment Workflow

The deployment workflow (`.github/workflows/deploy-backend.yml`) automatically:

1. Builds Docker image on push to `main` branch
2. Runs smoke tests
3. Pushes to ECR
4. Deploys to EC2 instances via SSM
5. Verifies health checks

To trigger manual deployment:

```bash
# Via GitHub Actions UI: Actions → Deploy Bedrock Backend → Run workflow
```

## Monitoring and Maintenance

### CloudWatch Logs

```bash
# View application logs
aws logs tail /aws/ec2/bedrock-backend --follow

# View specific container logs
aws logs tail /aws/ec2/bedrock-backend --log-stream-name-prefix fastapi --follow
aws logs tail /aws/ec2/bedrock-backend --log-stream-name-prefix celery --follow
aws logs tail /aws/ec2/bedrock-backend --log-stream-name-prefix redis --follow
```

### CloudWatch Alarms

The stack creates these alarms:

- **High CPU**: Alerts when CPU > 80%
- **Unhealthy Hosts**: Alerts when target group has unhealthy instances
- **High Memory**: Alerts when memory usage > 85%

### Update Environment Variables

To update environment variables after deployment:

```bash
# SSH into EC2 instance
aws ssm start-session --target $INSTANCE_ID

# Edit .env file
sudo nano /opt/bedrock-backend/.env

# Restart containers
cd /opt/bedrock-backend
sudo docker stop bedrock-celery-worker bedrock-backend
sudo docker rm bedrock-celery-worker bedrock-backend

# Restart using latest .env
sudo docker run -d \
  --name bedrock-backend \
  --restart unless-stopped \
  --network bedrock-network \
  -p 8000:8000 \
  --env-file .env \
  YOUR_IMAGE_URI

sudo docker run -d \
  --name bedrock-celery-worker \
  --restart unless-stopped \
  --network bedrock-network \
  --env-file .env \
  YOUR_IMAGE_URI \
  celery -A src.celery_tasks.c_app worker --loglevel=info
```

## Troubleshooting

### Issue: Containers not starting

```bash
# Check Docker logs
docker logs bedrock-backend
docker logs bedrock-celery-worker
docker logs redis

# Check user-data script execution
cat /var/log/user-data.log
```

### Issue: Email not sending

```bash
# Check Celery worker logs
docker logs bedrock-celery-worker

# Test SMTP connection
docker exec -it bedrock-celery-worker python -c "
from src.mail import mail
print('SMTP Config:', mail.config)
"

# Verify Redis connection
docker exec -it redis redis-cli ping
# Should return: PONG
```

### Issue: Database connection errors

```bash
# Verify database URL format
docker exec -it bedrock-backend env | grep DATABASE_URL

# Test database connection
docker exec -it bedrock-backend python -c "
import asyncio
from src.db.main import engine
async def test():
    async with engine.connect() as conn:
        print('Database connected!')
asyncio.run(test())
"
```

### Issue: Health check failing

```bash
# Check if FastAPI is running
curl http://localhost:8000/health

# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn YOUR_TARGET_GROUP_ARN
```

## Security Best Practices

1. **Restrict SSH Access**: Update the EC2 Security Group to limit SSH to your IP only
2. **Enable SSL/TLS**: Add an SSL certificate to ALB for HTTPS
3. **Use AWS Secrets Manager**: Store sensitive credentials in Secrets Manager instead of parameters
4. **Enable CloudTrail**: Enable CloudTrail for audit logging
5. **Regular Updates**: Keep Docker images and system packages updated

## Cost Optimization

- **Instance Type**: Start with t3.small, scale up if needed
- **Auto Scaling**: Configured to scale based on CPU (70% threshold)
- **Log Retention**: Set to 7 days (adjust in CloudFormation if needed)
- **Reserved Instances**: Consider Reserved Instances for production workloads

## Cleanup

To delete all resources:

```bash
aws cloudformation delete-stack \
  --stack-name bedrock-backend-stack \
  --region us-east-2

aws cloudformation wait stack-delete-complete \
  --stack-name bedrock-backend-stack \
  --region us-east-2
```

## Support

For issues or questions:

1. Check CloudWatch logs: `/aws/ec2/bedrock-backend`
2. Review container logs: `docker logs <container-name>`
3. Verify CloudFormation events in AWS Console

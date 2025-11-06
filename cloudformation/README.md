# 📦 Deployment Files Summary

This directory contains AWS CloudFormation templates for deploying the Bedrock Backend.

## Active Template

### bedrock-docker-ec2.yaml

**Production-ready Docker deployment on EC2 with ALB**

**Features:**

- Docker containerized application
- Auto Scaling Group (1-3 instances)
- Application Load Balancer (HTTP/HTTPS)
- Health checks and monitoring
- CloudWatch logs and metrics
- Rolling deployments via SSM
- Port mapping: ALB(80) → EC2(8000) → Docker(8000)
- CORS: Accepts all origins over HTTP/HTTPS

**Use this template for:**

- Production deployments
- Staging environments
- Any Docker-based deployment

## Deployment Instructions

See the complete guide: [AWS_DEPLOYMENT_GUIDE.md](../AWS_DEPLOYMENT_GUIDE.md)

Quick deploy command:

```powershell
aws cloudformation create-stack `
  --stack-name bedrock-backend-stack `
  --template-body file://bedrock-docker-ec2.yaml `
  --parameters file://parameters.json `
  --capabilities CAPABILITY_NAMED_IAM
```

## Parameters Required

Create `parameters.json` with:

- Environment (production/staging)
- InstanceType (t3.small recommended)
- KeyPairName (for SSH)
- DockerImage (ECR URI)
- DatabaseURL
- AWS credentials
- JWTSecret
- VpcId and SubnetIds

## Related Files

- `Dockerfile` - Multi-stage Docker build
- `.dockerignore` - Build context exclusions
- `.github/workflows/deploy-backend.yml` - CI/CD pipeline

---

_Last Updated: November 5, 2025_

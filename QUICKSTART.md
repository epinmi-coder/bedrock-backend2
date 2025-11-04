# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

- AWS Account
- GitHub repository
- PostgreSQL database

### Step 1: Configure GitHub Secrets

Add these secrets to your GitHub repository:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
DATABASE_URL
EC2_KEY_PAIR_NAME
```

### Step 2: Deploy Infrastructure

**Option A: Via GitHub Actions**

1. Go to Actions → Production CI/CD Pipeline
2. Click "Run workflow"
3. Select environment: `production`
4. Select action: `deploy`
5. Click "Run workflow"

**Option B: Via Script**

```bash
export AWS_REGION=us-east-1
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export EC2_KEY_PAIR_NAME="your-keypair"

bash scripts/deploy.sh production
```

### Step 3: Verify Deployment

Wait 5-10 minutes for deployment to complete, then:

```bash
# Get your ALB URL from CloudFormation outputs
ALB_URL="http://your-alb-url.amazonaws.com"

# Test health endpoint
curl $ALB_URL/health

# View API docs
open $ALB_URL/api/v1/docs
```

### Step 4: Monitor

- **Logs**: CloudWatch Logs → `/aws/ec2/bedrock-backend/production`
- **Metrics**: CloudWatch Metrics → `BedrockBackend/production`
- **Alarms**: CloudWatch Alarms

## 🔧 Local Development

```bash
# Clone repository
git clone <your-repo>
cd bedrock-backend

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://bedrock:bedrock_dev_password@localhost:5432/bedrock_db
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
EOF

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f api

# Access API
curl http://localhost:8000/health
open http://localhost:8000/api/v1/docs
```

## 📚 Next Steps

- Read the full [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions
- Review [ARCHITECTURE.md](./ARCHITECTURE.md) for system design
- Check [README.md](./README.md) for API documentation

## 🆘 Need Help?

Common issues and solutions:

**Deployment fails?**

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name production-bedrock-backend \
  --region us-east-1
```

**Health checks fail?**

```bash
# Check application logs
aws logs tail /aws/ec2/bedrock-backend/production \
  --follow \
  --region us-east-1
```

**Can't connect to database?**

- Verify DATABASE_URL is correct
- Check database security group allows EC2 instances
- Test connection: `psql "$DATABASE_URL"`

For more help, see the [Troubleshooting](./DEPLOYMENT.md#troubleshooting) section.

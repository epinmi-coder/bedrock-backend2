# Local Frontend to AWS Backend Setup Guide

This guide explains how to configure your local frontend (running on localhost:5173) to connect to your backend deployed in AWS EC2.

## Architecture Overview

```
┌─────────────────────┐          ┌──────────────────────────┐
│  Your Computer      │          │     AWS Cloud            │
│                     │          │                          │
│  ┌───────────────┐  │  HTTP    │  ┌────────────────────┐  │
│  │  Frontend     │──┼─────────►│  │  Application       │  │
│  │  localhost:   │  │  Request │  │  Load Balancer     │  │
│  │  5173         │◄─┼──────────│  │  (ALB)             │  │
│  └───────────────┘  │  Response│  └────────────────────┘  │
│                     │          │          │               │
└─────────────────────┘          │          ▼               │
                                 │  ┌────────────────────┐  │
                                 │  │  EC2 Instance      │  │
                                 │  │  with Docker       │  │
                                 │  │  ┌──────────────┐  │  │
                                 │  │  │ FastAPI:8000 │  │  │
                                 │  │  │ Celery       │  │  │
                                 │  │  │ Redis        │  │  │
                                 │  │  └──────────────┘  │  │
                                 │  └────────────────────┘  │
                                 └──────────────────────────┘
```

## Key Configuration Changes Made

### 1. **CORS Configuration** ✅

**Location:** `cloudformation/bedrock-docker-ec2.yaml`

```yaml
ALLOWED_ORIGINS='["*"]'
```

**What it does:** Allows your localhost frontend to make requests to the AWS backend without CORS blocking.

**Why it works:** The `*` wildcard allows any origin (including `http://localhost:5173`) to access the API.

### 2. **TrustedHostMiddleware Fix** ✅

**Location:** `src/middleware.py`

```python
allowed_hosts = ["*"]
```

**What it does:** Accepts requests with any Host header, including the ALB DNS name.

**Why it's needed:** When your frontend makes a request to `http://production-bedrock-alb-123.us-east-2.elb.amazonaws.com`, the Host header contains the ALB DNS. The previous configuration only allowed `localhost` and `127.0.0.1`, which would reject ALB requests.

### 3. **ALB Security Group** ✅

**Location:** `cloudformation/bedrock-docker-ec2.yaml`

The ALB Security Group already allows:

- **Port 80 (HTTP)** from anywhere (`0.0.0.0/0`)
- **Port 443 (HTTPS)** from anywhere (for future SSL setup)

This means your local machine can reach the ALB.

## Deployment Steps

### Step 1: Prepare CloudFormation Parameters

Create `cloudformation/parameters.json` from the example:

```bash
cd cloudformation
cp parameters.example.json parameters.json
```

Edit `parameters.json` and fill in your values:

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
    "ParameterValue": "your-ec2-keypair-name"
  },
  {
    "ParameterKey": "DockerImage",
    "ParameterValue": "123456789012.dkr.ecr.us-east-2.amazonaws.com/bedrock-backend:latest"
  },
  {
    "ParameterKey": "DatabaseURL",
    "ParameterValue": "postgresql+psycopg://user:pass@your-neon-host.neon.tech:5432/bedrock?sslmode=require"
  },
  {
    "ParameterKey": "JWTSecret",
    "ParameterValue": "your-super-secret-jwt-key-here"
  },
  {
    "ParameterKey": "AWSAccessKeyId",
    "ParameterValue": "AKIAIOSFODNN7EXAMPLE"
  },
  {
    "ParameterKey": "AWSSecretAccessKey",
    "ParameterValue": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  },
  {
    "ParameterKey": "FrontendDomain",
    "ParameterValue": "localhost:5173"
  },
  {
    "ParameterKey": "Domain",
    "ParameterValue": "production-bedrock-alb-123.us-east-2.elb.amazonaws.com"
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
    "ParameterValue": "your-app-password"
  },
  {
    "ParameterKey": "MailFrom",
    "ParameterValue": "your-email@gmail.com"
  },
  {
    "ParameterKey": "MailFromName",
    "ParameterValue": "Security Platform"
  },
  {
    "ParameterKey": "VpcId",
    "ParameterValue": "vpc-0123456789abcdef0"
  },
  {
    "ParameterKey": "SubnetIds",
    "ParameterValue": "subnet-abc123,subnet-def456"
  }
]
```

**Important Notes:**

- Use your **default VPC** or an existing VPC
- Select **at least 2 subnets in different Availability Zones**
- The `Domain` parameter will be updated after deployment with the actual ALB DNS

### Step 2: Create ECR Repository

```bash
aws ecr create-repository --repository-name bedrock-backend --region us-east-2
```

### Step 3: Deploy via GitHub Actions (Recommended)

1. **Set GitHub Secrets:**

Go to your repository → Settings → Secrets and variables → Actions → New repository secret

Add:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DATABASE_URL`
- `JWT_SECRET`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`

2. **Push to main branch:**

```bash
git add .
git commit -m "Deploy backend to AWS"
git push origin main
```

GitHub Actions will automatically:

- Build Docker image
- Push to ECR
- Deploy CloudFormation stack (on first run)
- Update EC2 instances with new image

### Step 4: Manual Deployment (Alternative)

If you prefer manual deployment:

```bash
# Build and push Docker image
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-2.amazonaws.com

docker build -t bedrock-backend .
docker tag bedrock-backend:latest 123456789012.dkr.ecr.us-east-2.amazonaws.com/bedrock-backend:latest
docker push 123456789012.dkr.ecr.us-east-2.amazonaws.com/bedrock-backend:latest

# Deploy CloudFormation stack
aws cloudformation create-stack \
  --stack-name bedrock-backend-stack \
  --template-body file://cloudformation/bedrock-docker-ec2.yaml \
  --parameters file://cloudformation/parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-2
```

### Step 5: Get ALB DNS Name

After stack creation completes (takes ~5-10 minutes):

```bash
aws cloudformation describe-stacks \
  --stack-name bedrock-backend-stack \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
  --output text \
  --region us-east-2
```

Output example:

```
production-bedrock-alb-1234567890.us-east-2.elb.amazonaws.com
```

### Step 6: Update Frontend Configuration

In your frontend code, update the API base URL:

**Before (local development):**

```javascript
const API_BASE_URL = "http://localhost:8000";
```

**After (AWS backend):**

```javascript
const API_BASE_URL =
  "http://production-bedrock-alb-1234567890.us-east-2.elb.amazonaws.com";
```

Or use environment variables:

```javascript
// .env.local
VITE_API_URL=http://production-bedrock-alb-1234567890.us-east-2.elb.amazonaws.com
```

```javascript
// In your code
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

### Step 7: Test Connection

1. **Test health endpoint:**

```bash
curl http://your-alb-dns.us-east-2.elb.amazonaws.com/health
```

Expected response:

```json
{
  "status": "ok",
  "timestamp": "2025-11-06T12:00:00.000Z"
}
```

2. **Test from frontend:**

Open your browser console and try:

```javascript
fetch("http://your-alb-dns.us-east-2.elb.amazonaws.com/api/v1/health")
  .then((r) => r.json())
  .then(console.log);
```

## Troubleshooting

### Issue: "No 'Access-Control-Allow-Origin' header"

**Cause:** CORS not configured properly

**Solution:** Verify the environment variable in EC2:

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@ec2-instance

# Check environment
docker exec bedrock-backend env | grep ALLOWED_ORIGINS

# Should show: ALLOWED_ORIGINS='["*"]'
```

If incorrect, update `/opt/bedrock-backend/.env` and restart:

```bash
docker restart bedrock-backend
```

### Issue: "Could not connect to server"

**Cause:** Security group or ALB listener issue

**Solution:**

1. Check ALB is running:

```bash
aws elbv2 describe-load-balancers --names production-bedrock-alb --region us-east-2
```

2. Check target health:

```bash
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-2:123456789012:targetgroup/production-bedrock-tg/abc123 \
  --region us-east-2
```

3. Verify EC2 instance is registered and healthy

### Issue: "TrustedHost validation failed"

**Cause:** TrustedHostMiddleware rejecting ALB DNS

**Solution:** Already fixed! The middleware now allows all hosts (`["*"]`). If you still see this, rebuild and redeploy the Docker image.

### Issue: Health check failing

**Check logs:**

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@ec2-instance-ip

# View FastAPI logs
docker logs bedrock-backend

# View Celery logs
docker logs bedrock-celery-worker

# View Redis logs
docker logs redis

# Check container status
docker ps -a
```

## Security Considerations

### Current Setup (Development)

- ✅ CORS allows all origins (`["*"]`)
- ✅ TrustedHost allows all hosts (`["*"]`)
- ✅ ALB accepts HTTP on port 80 from anywhere
- ❌ No SSL/HTTPS (yet)
- ❌ SSH open to 0.0.0.0/0 (should restrict to your IP)

### Production Recommendations

1. **Enable HTTPS with SSL Certificate:**

   - Request certificate from AWS Certificate Manager (ACM)
   - Update CloudFormation to use HTTPS listener
   - Redirect HTTP to HTTPS

2. **Restrict CORS Origins:**

   ```yaml
   ALLOWED_ORIGINS='["https://yourdomain.com", "https://www.yourdomain.com"]'
   ```

3. **Restrict SSH Access:**
   Update CloudFormation security group:

   ```yaml
   - IpProtocol: tcp
     FromPort: 22
     ToPort: 22
     CidrIp: YOUR_IP_ADDRESS/32
     Description: Allow SSH from my IP only
   ```

4. **Use Custom Domain:**

   - Register domain in Route 53
   - Create A record pointing to ALB
   - Update frontend to use domain instead of ALB DNS

5. **Add WAF (Web Application Firewall):**
   - Protect against common web exploits
   - Rate limiting

## Cost Estimation

**Monthly AWS Costs (approximate):**

- EC2 t3.small: ~$15/month (1 instance)
- ALB: ~$16/month + data transfer
- CloudWatch Logs: ~$0.50/month (1GB)
- Data Transfer: ~$5-10/month (depends on usage)

**Total: ~$37-42/month** for basic setup

**Scaling:** With 3 instances (MaxSize=3), costs increase to ~$60-70/month

## Next Steps

1. ✅ Deploy backend to AWS
2. ✅ Update frontend API URL to point to ALB DNS
3. ✅ Test authentication flow (register, login, verify email)
4. ✅ Test chat functionality
5. ⏳ Set up custom domain (optional)
6. ⏳ Enable HTTPS with SSL certificate (recommended)
7. ⏳ Configure monitoring and alerts

## Support

If you encounter issues:

1. Check CloudWatch Logs: `/aws/ec2/bedrock-backend`
2. SSH to EC2 and check Docker logs
3. Verify all environment variables are set correctly
4. Test health endpoint: `curl http://alb-dns/health`

---

**Last Updated:** November 6, 2025
**Configuration Status:** Ready for deployment with localhost frontend support

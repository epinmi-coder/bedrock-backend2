# Bedrock Backend API

**AI-Powered Chat Backend with AWS Bedrock Integration**

# Bedrock Backend API

A high-performance FastAPI backend service that integrates with AWS Bedrock to provide AI-powered security analysis capabilities.

## 🚀 Quick Links

- **[AWS Deployment Guide](AWS_DEPLOYMENT_GUIDE.md)** - Complete guide for deploying to AWS with Docker, CloudFormation, and GitHub Actions
- **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Step-by-step checklist for deployment
- **[Architecture Documentation](ARCHITECTURE.md)** - System architecture and design decisions Features full CRUD functionality for chat history management, PostgreSQL database integration, and ChatGPT-style conversation experience.

---

## 🎯 Key Features

### 1. **AWS Bedrock Integration**

- **Model**: Anthropic Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`)
- Real-time AI response generation
- Configurable temperature and token limits
- Automatic retry and error handling

### 2. **Full CRUD Functionality**

- ✅ **Create**: Store new chat messages and responses
- ✅ **Read**: Retrieve chat history by user, chat session, or message ID
- ✅ **Update**: Modify existing conversations (if needed)
- ✅ **Delete**: Remove specific messages or entire chat sessions

### 3. **Chat History Management**

- Hierarchical ID structure:
  - `chat_id`: Groups messages in a conversation
  - `message_uid`: Unique identifier for each message
  - `response_session_id`: Links user input to AI response
- Load complete chat history on frontend initialization
- Efficient pagination and filtering

### 4. **Database Architecture**

- **PostgreSQL** with async support (SQLModel + psycopg)
- **Alembic** migrations for schema management
- **JSONB** storage for flexible metadata
- Indexed columns for fast queries

### 5. **Performance Optimization**

- Async/await throughout the application
- Database connection pooling
- Caching strategy for frequently accessed data
- Rate limiting per user

### 6. **Public Access (Current)**

- **No authentication required** (open for testing)
- Anonymous user support
- CORS configured for frontend access

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (React + Vite)                        │
│  - ChatGPT-style UI                             │
│  - Load chat history on init                    │
│  - Real-time message streaming                  │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/REST API
                   ▼
┌─────────────────────────────────────────────────┐
│  FastAPI Backend                                │
│  ├─ /api/v1/chats (POST)    - Send messages    │
│  ├─ /api/v1/history (GET)   - Get chat history │
│  ├─ /api/v1/conversations   - CRUD operations  │
│  └─ /health                  - Health check     │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴───────────┐
        ▼                      ▼
┌──────────────────┐  ┌─────────────────────┐
│  AWS Bedrock     │  │  PostgreSQL DB      │
│  - Claude 3      │  │  - Chats table      │
│  - AI responses  │  │  - Users table      │
└──────────────────┘  └─────────────────────┘
```

---

## 🗄️ Database Schema

### **Chats Table**

```sql
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    chat_id UUID NOT NULL,
    user_input TEXT NOT NULL,
    bedrock_response TEXT,
    chat_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_chats_chat_id ON chats(chat_id);
CREATE INDEX idx_chats_created_at ON chats(created_at);
```

### **Metadata Structure**

```json
{
  "question": "Original user query",
  "bedrock_processed": true,
  "chat_id": "uuid",
  "message_uid": "uuid",
  "response_session_id": "uuid",
  "user_id": "anonymous",
  "timestamp": "2025-11-04T00:00:00Z"
}
```

---

## 🚀 API Endpoints

### **Health Check**

```http
GET /health
GET /api/v1/health
```

### **Chat Endpoints**

```http
POST /api/v1/chats
Content-Type: application/json

{
  "message": "What are the top security vulnerabilities?",
  "chat_id": "optional-uuid",
  "message_uid": "optional-uuid"
}
```

**Response**:

```json
{
  "response": "AI-generated response text...",
  "chat_id": "abc123",
  "message_uid": "def456",
  "response_session_id": "ghi789",
  "metadata": {
    "question": "What are the top security vulnerabilities?",
    "bedrock_processed": true,
    "timestamp": "2025-11-04T10:30:00Z"
  },
  "status": "success"
}
```

### **History Endpoints**

```http
# Get chat history by chat_id
GET /api/v1/my-history?chat_id=abc123&message_id=def456

# Get all conversations
GET /api/v1/conversations?limit=50&offset=0

# Get specific chat conversations
GET /api/v1/conversations/{chat_id}
```

---

## 🛠️ Technology Stack

| Component          | Technology                    | Version        |
| ------------------ | ----------------------------- | -------------- |
| **Framework**      | FastAPI                       | 0.119.1        |
| **Language**       | Python                        | 3.11+          |
| **Database**       | PostgreSQL                    | 15+            |
| **ORM**            | SQLModel + SQLAlchemy         | 2.x            |
| **Migrations**     | Alembic                       | 1.17.1         |
| **AI Service**     | AWS Bedrock                   | Claude 3 Haiku |
| **Async Driver**   | psycopg3 (async)              | 3.x            |
| **Authentication** | Optional (currently disabled) | -              |

---

## 📦 Installation & Setup

### **🚀 Quick Start - Choose Your Deployment**

#### Option 1: AWS Production Deployment (Docker + CloudFormation)

**Recommended for production environments**

✅ **Complete automated deployment to AWS**  
✅ **Docker containerized for consistency**  
✅ **Auto-scaling with load balancer**  
✅ **CI/CD with GitHub Actions**

👉 **[Follow AWS Deployment Guide](AWS_DEPLOYMENT_GUIDE.md)**  
👉 **[Use Deployment Checklist](DEPLOYMENT_CHECKLIST.md)**

Quick deploy command:

```powershell
# After configuring parameters.json
.\deploy.ps1
```

---

#### Option 2: Local Development Setup

**For development and testing**

### **Prerequisites**

```bash
- Python 3.11+
- PostgreSQL 15+
- AWS Account with Bedrock access
- AWS Access Keys with Bedrock permissions
```

### **1. Clone Repository**

```bash
git clone <repository-url>
cd bedrock-backend
```

### **2. Create Virtual Environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Configure Environment Variables**

Create `.env` file:

```env
# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:5173", "https://your-cloudfront-url.com"]

# AWS Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_MAX_TOKENS=4000
BEDROCK_TEMPERATURE=0.1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1

# Database
DATABASE_URL=postgresql+psycopg_async://user:password@host:port/dbname

# Optional: Authentication (currently disabled)
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# Optional: Redis (for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### **5. Run Database Migrations**

```bash
# Initialize Alembic (if not already done)
alembic upgrade head
```

### **6. Start Development Server**

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using FastAPI CLI
fastapi dev main.py
```

**Server will be available at**: `http://localhost:8000`  
**API Documentation**: `http://localhost:8000/docs`

---

## 🔧 Configuration

### **AWS Bedrock Setup**

1. **Enable Bedrock in AWS Console**

   - Go to AWS Bedrock console
   - Enable model access for Claude 3 Haiku
   - Region: `us-east-1` (or your preferred region)

2. **Create IAM User with Permissions**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```

3. **Generate Access Keys**
   - IAM → Users → Security credentials
   - Create access key
   - Copy `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

### **Database Setup**

**PostgreSQL (Local)**:

```bash
# Install PostgreSQL
# Create database
createdb security_agents_db

# Create user
psql -c "CREATE USER dbuser WITH PASSWORD 'your-password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE security_agents_db TO dbuser;"
```

**PostgreSQL (Cloud - Neon, RDS, etc.)**:

- Use provided connection string
- Ensure SSL is enabled for production
- Configure connection pooling

---

## 🔄 Database Migrations

### **Create New Migration**

```bash
alembic revision --autogenerate -m "Add new feature"
```

### **Apply Migrations**

```bash
alembic upgrade head
```

### **Rollback Migration**

```bash
alembic downgrade -1
```

### **View Migration History**

```bash
alembic history
```

---

## 📈 Rate Limiting

Current implementation:

- **10 requests per minute** per user
- **60-second window**
- Anonymous users: No limit (or separate limit)

Configurable in `chats/service.py`:

```python
self.rate_limit = 10
self.rate_limit_window = 60
```

---

## 🧪 Testing

### **Manual Testing**

```bash
# Health check
curl http://localhost:8000/health

# Send chat message
curl -X POST http://localhost:8000/api/v1/chats \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are SQL injection attacks?",
    "chat_id": "test-chat-123"
  }'

# Get chat history
curl "http://localhost:8000/api/v1/my-history?chat_id=test-chat-123"
```

### **Automated Testing**

```bash
# Run tests (if implemented)
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

---

## 🚢 Deployment Options

### **Option 1: AWS Lambda (Serverless)**

- Deploy with AWS SAM or Serverless Framework
- Use API Gateway for HTTP endpoints
- Integrate with RDS for database
- Cost-effective for variable traffic

### **Option 2: EC2 Instance**

- Deploy on Ubuntu/Amazon Linux
- Use systemd for process management
- Nginx as reverse proxy
- Suitable for consistent traffic

### **Option 3: ECS/Fargate (Containerized)**

- Package as Docker container
- Deploy to ECS Fargate
- Auto-scaling capabilities
- Production-grade setup

### **Option 4: Elastic Beanstalk**

- Simple deployment process
- Automatic scaling
- Managed environment
- Good for quick deployment

---

## 🔐 Security Considerations

### **Current State (Public Access)**

- ⚠️ **No authentication** - Open for testing
- ⚠️ **No authorization** - All endpoints accessible
- ⚠️ **Rate limiting** - Basic protection

### **Production Recommendations**

1. **Enable Authentication**

   - JWT-based authentication
   - Okta/Auth0 integration
   - API key authentication

2. **Add Authorization**

   - Role-based access control (RBAC)
   - User-specific chat history
   - Admin-only endpoints

3. **Secure Secrets**

   - Use AWS Secrets Manager
   - Environment-based configuration
   - Rotate credentials regularly

4. **API Security**

   - HTTPS only (TLS 1.2+)
   - CORS whitelist
   - Request size limits
   - Input validation

5. **Database Security**
   - SSL connections
   - Encrypted at rest
   - Regular backups
   - Access control

---

## 🐛 Troubleshooting

### **Common Issues**

**1. Bedrock Connection Error**

```
❌ Failed to initialize Bedrock client
```

**Solution**: Check AWS credentials, region, and Bedrock model access

**2. Database Connection Error**

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Verify DATABASE_URL, check PostgreSQL is running

**3. CORS Error in Frontend**

```
Access to fetch blocked by CORS policy
```

**Solution**: Add frontend URL to ALLOWED_ORIGINS in .env

**4. Rate Limit Exceeded**

```
429 Too Many Requests
```

**Solution**: Wait 60 seconds or adjust rate limits

---

## 📝 Environment Variables Reference

| Variable                | Description                       | Required | Default        |
| ----------------------- | --------------------------------- | -------- | -------------- |
| `ALLOWED_ORIGINS`       | CORS allowed origins (JSON array) | Yes      | -              |
| `DATABASE_URL`          | PostgreSQL connection string      | Yes      | -              |
| `BEDROCK_MODEL_ID`      | AWS Bedrock model identifier      | Yes      | claude-3-haiku |
| `BEDROCK_MAX_TOKENS`    | Max response tokens               | No       | 4000           |
| `BEDROCK_TEMPERATURE`   | AI temperature (0-1)              | No       | 0.1            |
| `AWS_ACCESS_KEY_ID`     | AWS access key                    | Yes      | -              |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key                    | Yes      | -              |
| `AWS_DEFAULT_REGION`    | AWS region                        | Yes      | us-east-1      |
| `JWT_SECRET`            | JWT signing secret                | No       | -              |
| `REDIS_HOST`            | Redis host for caching            | No       | localhost      |

---

## 📊 Monitoring & Logging

### **Logs**

- Location: `logs/` directory
- Format: Structured JSON logs
- Rotation: Daily rotation with 7-day retention

### **Metrics to Monitor**

- Request latency (target: < 2s)
- Bedrock API calls (cost optimization)
- Database query performance
- Error rates
- Rate limit hits

---

## 🎯 Future Enhancements

### **Planned Features**

- [ ] Add authentication (JWT/Okta)
- [ ] Implement Redis caching
- [ ] Add WebSocket support for streaming responses
- [ ] Implement message editing/deletion
- [ ] Add conversation sharing
- [ ] Export chat history (PDF/JSON)
- [ ] Multi-model support (Claude, GPT-4, etc.)
- [ ] Vector database integration for RAG
- [ ] Conversation summarization
- [ ] Cost tracking per user

---

## 📄 License

Proprietary - Internal Use Only

---

## 👥 Support

For issues, questions, or contributions:

- Create an issue in the repository
- Contact the development team
- Check documentation in `/docs`

---

**Built with ❤️ using FastAPI, AWS Bedrock, and PostgreSQL**

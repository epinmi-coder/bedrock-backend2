"""
AWS Bedrock service integration module
Handles AI model interactions using AWS Bedrock
"""
import json
import logging
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError
from src.config import Config as settings

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockAgent:
    """AWS Bedrock service client for AI model interactions"""
    
    def __init__(self):
        """Initialize Bedrock service with configuration from settings"""
        self.model_id = settings.BEDROCK_MODEL_ID
        self.max_tokens = settings.BEDROCK_MAX_TOKENS
        self.temperature = settings.BEDROCK_TEMPERATURE
        self.aws_region = settings.AWS_REGION
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Bedrock client"""
        if self._client is None:
            try:
                self._client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=self.aws_region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                logger.info(f"✅ Bedrock client initialized for region: {self.aws_region}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Bedrock client: {str(e)}")
                raise
        return self._client
    
    def process_request(self, user_query: str) -> Dict[str, Any]:
        """Process user query with AWS Bedrock and return response"""
        try:
            logger.info(f"🔄 Processing query with Bedrock model: {self.model_id}")
            logger.debug(f"Query: {user_query[:100]}...")
            
            # Prepare the request payload for Anthropic Claude model
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": user_query
                    }
                ]
            }
            
            # Call Bedrock
            response = self.client.invoke_model(
                body=json.dumps(body),
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response.get('body').read())
            
            # Extract the AI response text
            if 'content' in response_body and len(response_body['content']) > 0:
                bedrock_response = response_body['content'][0]['text']
                
                logger.info("✅ Bedrock processing successful")
                logger.debug(f"Response length: {len(bedrock_response)} characters")
                
                return {
                    "success": True,
                    "question": user_query,
                    "response": bedrock_response,
                    "model_id": self.model_id,
                    "tokens_used": response_body.get('usage', {}).get('output_tokens', 0)
                }
            else:
                logger.error("❌ Invalid response format from Bedrock")
                return {
                    "success": False,
                    "error": "Invalid response format from Bedrock",
                    "question": user_query,
                    "response": "I'm sorry, I couldn't process your request due to an invalid response format."
                }
                
        except ClientError as e:
            error_msg = f"AWS Bedrock ClientError: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "question": user_query,
                "response": "I'm sorry, I encountered an AWS service error while processing your request."
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "question": user_query,
                "response": "I'm sorry, I encountered an unexpected error while processing your request."
            }
    
    def health_check(self) -> Dict[str, Any]:
        
        try:
            # Try to list foundation models as a health check
            bedrock_client = boto3.client(
                'bedrock', 
                region_name=self.aws_region,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            response = bedrock_client.list_foundation_models()
            
            # Check if our model is available
            available_models = [model['modelId'] for model in response.get('modelSummaries', [])]
            model_available = self.model_id in available_models
            
            return {
                "status": "healthy" if model_available else "warning",
                "model_available": model_available,
                "model_id": self.model_id,
                "region": self.aws_region,
                "available_models_count": len(available_models)
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "model_id": self.model_id,
                "region": self.aws_region
            }

# Create a singleton instance
bedrock_agent = BedrockAgent()
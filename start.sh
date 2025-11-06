#!/bin/bash
# Startup script for Bedrock Backend
# Supports running FastAPI server or Celery worker based on SERVICE_TYPE environment variable

set -e

SERVICE_TYPE=${SERVICE_TYPE:-"api"}

echo "=========================================="
echo "Starting Bedrock Backend Service"
echo "Service Type: $SERVICE_TYPE"
echo "Timestamp: $(date)"
echo "=========================================="

case "$SERVICE_TYPE" in
  api)
    echo "Starting FastAPI server with Uvicorn..."
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    ;;
  
  celery)
    echo "Starting Celery worker..."
    exec celery -A src.celery_tasks.c_app worker --loglevel=info --concurrency=2
    ;;
  
  celery-beat)
    echo "Starting Celery beat scheduler..."
    exec celery -A src.celery_tasks.c_app beat --loglevel=info
    ;;
  
  *)
    echo "Error: Unknown SERVICE_TYPE '$SERVICE_TYPE'"
    echo "Valid options: api, celery, celery-beat"
    exit 1
    ;;
esac

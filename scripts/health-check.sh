#!/bin/bash
# Health check script for Bedrock Backend API

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
MAX_RETRIES="${MAX_RETRIES:-5}"
RETRY_DELAY="${RETRY_DELAY:-5}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Bedrock Backend Health Check"
echo "=========================================="
echo "API URL: $API_URL"
echo "Max Retries: $MAX_RETRIES"
echo "=========================================="

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local description=$3
    
    echo -n "Checking $description... "
    
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint" || echo "000")
    
    if [ "$http_code" == "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code, expected $expected_status)"
        return 1
    fi
}

# Function to check with retries
check_with_retry() {
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        echo ""
        echo "Attempt $attempt of $MAX_RETRIES..."
        
        if check_endpoint "/health" "200" "Health endpoint" && \
           check_endpoint "/api/v1/health" "200" "API health endpoint" && \
           check_endpoint "/" "200" "Root endpoint"; then
            echo ""
            echo -e "${GREEN}=========================================="
            echo "✓ All health checks passed!"
            echo "==========================================${NC}"
            return 0
        fi
        
        if [ $attempt -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}Retrying in $RETRY_DELAY seconds...${NC}"
            sleep $RETRY_DELAY
        fi
        
        attempt=$((attempt + 1))
    done
    
    echo ""
    echo -e "${RED}=========================================="
    echo "✗ Health checks failed after $MAX_RETRIES attempts"
    echo "==========================================${NC}"
    return 1
}

# Run health checks
check_with_retry

exit $?

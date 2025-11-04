#!/bin/bash
# Database migration script

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Database Migration Script"
echo "=========================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL environment variable is not set${NC}"
    exit 1
fi

echo -e "${GREEN}Database URL configured${NC}"

# Check database connection
echo "Checking database connection..."
python -c "
import os
import sys
from sqlalchemy import create_engine

try:
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to connect to database${NC}"
    exit 1
fi

# Run migrations
echo ""
echo "Running Alembic migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "✓ Migrations completed successfully"
    echo "==========================================${NC}"
else
    echo -e "${RED}=========================================="
    echo "✗ Migrations failed"
    echo "==========================================${NC}"
    exit 1
fi

# Show current revision
echo ""
echo "Current database revision:"
alembic current

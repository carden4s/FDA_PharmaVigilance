#!/bin/bash

# FDA PharmaVigilance - Complete Setup Script

set -e  # Exit on error

echo "================================"
echo "FDA PharmaVigilance Setup"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -n "Checking Python version... "
if ! command -v python3.11 &> /dev/null; then
    echo -e "${YELLOW}Python 3.11 not found, trying python3${NC}"
    PYTHON=python3
else
    PYTHON=python3.11
fi
$PYTHON --version
echo -e "${GREEN}✓${NC}"
echo ""

# Create .env file
echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}Created .env file. Please edit with your credentials:${NC}"
    echo "  - SNOWFLAKE_ACCOUNT"
    echo "  - SNOWFLAKE_USER"
    echo "  - SNOWFLAKE_PASSWORD"
    echo "  - FDA_API_KEY"
    echo ""
    read -p "Press Enter after updating .env..."
fi
echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Setup Ingestion Layer
echo "Setting up Ingestion Layer..."
cd ingestion
$PYTHON -m pip install -r requirements.txt
mkdir -p logs data/sample data/mappings
cd ..
echo -e "${GREEN}✓ Ingestion layer ready${NC}"
echo ""

# Setup dbt
echo "Setting up dbt..."
cd dbt
$PYTHON -m pip install -r requirements.txt
mkdir -p ~/.dbt
# Note: profiles.yml uses env vars, so copy it to ~/.dbt if needed
cd ..
echo -e "${GREEN}✓ dbt ready${NC}"
echo ""

# Setup Streamlit
echo "Setting up Streamlit..."
cd streamlit
$PYTHON -m pip install -r requirements.txt
# Create secrets file from example
if [ ! -f .streamlit/secrets.toml ]; then
    cp .streamlit/secrets.toml.example .streamlit/secrets.toml
    echo -e "${YELLOW}Created .streamlit/secrets.toml. Please edit with your Snowflake credentials${NC}"
fi
cd ..
echo -e "${GREEN}✓ Streamlit ready${NC}"
echo ""

# Test connections
echo "Testing connections..."
cd ingestion
$PYTHON -c "
from src.fda_client import FDAClient
from src.config import get_config

config = get_config()
client = FDAClient(api_key=config.FDA_API_KEY)
if client.test_connection():
    print('✓ FDA API connection successful')
else:
    print('✗ FDA API connection failed')
"
cd ..
echo ""

echo "================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Run ingestion:"
echo "   cd ingestion"
echo "   python src/main.py"
echo ""
echo "2. Run dbt transformations:"
echo "   cd dbt"
echo "   dbt run"
echo ""
echo "3. Run Streamlit dashboard:"
echo "   cd streamlit"
echo "   streamlit run app.py"
echo ""
echo "Or use Docker:"
echo "   docker-compose up"
echo ""

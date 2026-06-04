#!/bin/bash

# FDA PharmaVigilance - Local Development Setup

echo "================================"
echo "FDA PharmaVigilance Development Setup"
echo "================================"
echo ""

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

echo "Virtual environment activated"
echo ""

# Install all dependencies
echo "Installing dependencies..."
pip install --upgrade pip

# Ingestion
echo "Installing ingestion dependencies..."
pip install -r ingestion/requirements-dev.txt

# dbt
echo "Installing dbt dependencies..."
pip install -r dbt/requirements.txt

# Streamlit
echo "Installing streamlit dependencies..."
pip install -r streamlit/requirements.txt

echo ""
echo "================================"
echo "Development Setup Complete!"
echo "================================"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "Run tests:"
echo "  pytest ingestion/tests/"
echo ""
echo "Format code:"
echo "  black ingestion/src streamlit/"
echo ""

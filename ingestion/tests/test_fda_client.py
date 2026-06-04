"""Tests for FDA API client"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fda_client import FDAClient


@pytest.fixture
def fda_client():
    """Create FDA client for testing"""
    return FDAClient(api_key="test_key", base_url="http://test.local")


def test_initialization(fda_client):
    """Test FDA client initialization"""
    assert fda_client.api_key == "test_key"
    assert fda_client.timeout == 30
    assert fda_client.max_retries == 5


@patch('fda_client.requests.get')
def test_test_connection_success(mock_get, fda_client):
    """Test successful connection"""
    mock_response = Mock()
    mock_response.json.return_value = {"results": []}
    mock_get.return_value = mock_response
    
    result = fda_client.test_connection()
    assert result is True


@patch('fda_client.requests.get')
def test_test_connection_failure(mock_get, fda_client):
    """Test failed connection"""
    mock_get.side_effect = Exception("Connection failed")
    
    result = fda_client.test_connection()
    assert result is False


@patch('fda_client.requests.get')
def test_fetch_adverse_events(mock_get, fda_client):
    """Test fetching adverse events"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {"safetyreportid": "123", "drug": []}
        ]
    }
    mock_get.return_value = mock_response
    
    result = fda_client.fetch_adverse_events("aspirin")
    assert result is not None
    assert "results" in result

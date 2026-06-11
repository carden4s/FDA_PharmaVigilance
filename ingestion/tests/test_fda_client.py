"""Tests for FDA API client"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fda_client import FDAClient


@pytest.fixture
def fda_client():
    return FDAClient(api_key="test_key", base_url="http://test.local")


def test_initialization(fda_client):
    assert fda_client.api_key == "test_key"
    assert fda_client.timeout == 30
    assert fda_client.max_retries == 5


@patch('fda_client.requests.get')
def test_test_connection_success(mock_get, fda_client):
    mock_response = Mock()
    mock_response.json.return_value = {"results": []}
    mock_get.return_value = mock_response
    assert fda_client.test_connection() is True


@patch('fda_client.requests.get')
def test_test_connection_failure(mock_get, fda_client):
    mock_get.side_effect = Exception("Connection failed")
    assert fda_client.test_connection() is False


def test_build_search_no_window(fda_client):
    s = fda_client._build_search("aspirin", None, None)
    assert 'medicinalproduct.exact:"ASPIRIN"' in s
    assert "receivedate" not in s


def test_build_search_with_window(fda_client):
    s = fda_client._build_search("aspirin", "20240101", "20240131")
    assert "receivedate:[20240101 TO 20240131]" in s


@patch('fda_client.requests.get')
def test_fetch_adverse_events(mock_get, fda_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [{"safetyreportid": "123", "drug": []}]}
    mock_get.return_value = mock_response

    result = fda_client.fetch_adverse_events("aspirin")
    assert result is not None
    assert "results" in result
    assert len(result["results"]) == 1


@patch('fda_client.requests.get')
def test_fetch_paginates(mock_get, fda_client):
    """Should page through multiple responses until the last short page."""
    fda_client.PAGE_SIZE = 2
    page1 = Mock(); page1.status_code = 200
    page1.json.return_value = {"results": [{"safetyreportid": "1"}, {"safetyreportid": "2"}],
                               "meta": {"results": {"total": 3}}}
    page2 = Mock(); page2.status_code = 200
    page2.json.return_value = {"results": [{"safetyreportid": "3"}],
                               "meta": {"results": {"total": 3}}}
    mock_get.side_effect = [page1, page2]

    result = fda_client.fetch_adverse_events("aspirin")
    assert len(result["results"]) == 3


@patch('fda_client.requests.get')
def test_fetch_404_returns_empty(mock_get, fda_client):
    """openFDA returns 404 for zero matches -> treat as empty, not error."""
    resp = Mock(); resp.status_code = 404
    mock_get.return_value = resp
    result = fda_client.fetch_adverse_events("nonexistent_drug")
    assert result["results"] == []
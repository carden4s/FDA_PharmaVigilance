"""Tests for data processor"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_processor import DataProcessor


@pytest.fixture
def sample_event():
    """Sample FDA adverse event"""
    return {
        "safetyreportid": "12345",
        "reporttype": "EXP",
        "serious": 1,
        "seriousnessdeath": 1,
        "patient": {
            "patientonsetage": 65,
            "patientsex": 1,
            "patientweight": 75.5,
            "reaction": [
                {"reactionmeddrapt": "Myocardial infarction", "reactionoutcome": 1},
                {"reactionmeddrapt": "Chest pain", "reactionoutcome": 3}
            ]
        },
        "drug": [
            {"medicinalproduct": "ASPIRIN"},
            {"medicinalproduct": "IBUPROFEN"}
        ],
        "eventdate": "2026-01-15",
        "reportdate": "2026-01-20"
    }


def test_flatten_event_basic(sample_event):
    """Test flattening a single event"""
    result = DataProcessor.flatten_event(sample_event)
    
    # Should create 4 rows (2 drugs x 2 reactions)
    assert len(result) == 4
    
    # Check first row
    assert result[0]["safetyreportid"] == "12345"
    assert result[0]["drug_name"] == "ASPIRIN"
    assert result[0]["reaction_name"] == "Myocardial infarction"


def test_flatten_event_no_reactions(sample_event):
    """Test flattening event without reactions"""
    sample_event["patient"]["reaction"] = []
    result = DataProcessor.flatten_event(sample_event)
    
    # Should create one row per drug
    assert len(result) == 2


def test_flatten_response_empty():
    """Test flattening empty response"""
    result = DataProcessor.flatten_response({})
    assert result == []


def test_flatten_response_with_results():
    """Test flattening response with results"""
    response = {
        "results": [
            {
                "safetyreportid": "1",
                "patient": {"reaction": []},
                "drug": [{"medicinalproduct": "ASPIRIN"}]
            },
            {
                "safetyreportid": "2",
                "patient": {"reaction": []},
                "drug": [{"medicinalproduct": "IBUPROFEN"}]
            }
        ]
    }
    
    result = DataProcessor.flatten_response(response)
    assert len(result) == 2


def test_add_metadata():
    """Test adding metadata to record"""
    record = {"safetyreportid": "123"}
    result = DataProcessor.add_metadata(record, "Aspirin", "batch-001")
    
    assert result["source_drug"] == "Aspirin"
    assert result["ingestion_batch_id"] == "batch-001"
    assert "loaded_at" in result

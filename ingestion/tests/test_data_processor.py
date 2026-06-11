"""Tests for data processor"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_processor import DataProcessor, _to_int, _to_float


@pytest.fixture
def sample_event():
    """Sample FDA adverse event (drug at root — sample/legacy format)."""
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
        "eventdate": "20260115",
        "reportdate": "20260120"
    }


@pytest.fixture
def nested_drug_event():
    """Real openFDA shape — drug nested under patient."""
    return {
        "safetyreportid": "999",
        "serious": "2",                       # string, like the live API
        "patient": {
            "patientonsetage": "45",          # string age
            "patientsex": "0",                # 0 = Unknown
            "drug": [{"medicinalproduct": "ASPIRIN"}],
            "reaction": [{"reactionmeddrapt": "Nausea", "reactionoutcome": "2"}]
        }
    }


def test_flatten_event_basic(sample_event):
    result = DataProcessor.flatten_event(sample_event)
    assert len(result) == 4                   # 2 drugs x 2 reactions
    assert result[0]["safetyreportid"] == "12345"
    assert result[0]["drug_name"] == "ASPIRIN"
    assert result[0]["reaction_name"] == "Myocardial infarction"


def test_flatten_event_no_reactions(sample_event):
    sample_event["patient"]["reaction"] = []
    result = DataProcessor.flatten_event(sample_event)
    assert len(result) == 2                    # one row per drug


def test_flatten_drug_nested_under_patient(nested_drug_event):
    """openFDA nests drug under patient — must still produce a row."""
    result = DataProcessor.flatten_event(nested_drug_event)
    assert len(result) == 1
    assert result[0]["drug_name"] == "ASPIRIN"
    assert result[0]["reaction_name"] == "Nausea"


def test_flatten_type_coercion(nested_drug_event):
    """String numeric fields should be coerced to int; sex=0 preserved."""
    row = DataProcessor.flatten_event(nested_drug_event)[0]
    assert row["serious"] == 2
    assert row["patient_onsetage"] == 45
    assert row["patient_sex"] == 0
    assert row["reaction_outcome"] == 2


def test_flatten_response_empty():
    assert DataProcessor.flatten_response({}) == []


def test_flatten_response_with_results():
    response = {
        "results": [
            {"safetyreportid": "1", "patient": {"reaction": [], "drug": [{"medicinalproduct": "ASPIRIN"}]}},
            {"safetyreportid": "2", "patient": {"reaction": [], "drug": [{"medicinalproduct": "IBUPROFEN"}]}}
        ]
    }
    result = DataProcessor.flatten_response(response)
    assert len(result) == 2


def test_add_metadata():
    record = {"safetyreportid": "123"}
    result = DataProcessor.add_metadata(record, "Aspirin", "batch-001")
    assert result["source_drug"] == "Aspirin"
    assert result["ingestion_batch_id"] == "batch-001"
    assert "loaded_at" in result


@pytest.mark.parametrize("value,expected", [
    ("65", 65), (65, 65), (None, None), ("", None), ("abc", None), ("0", 0),
])
def test_to_int(value, expected):
    assert _to_int(value) == expected


@pytest.mark.parametrize("value,expected", [
    ("75.5", 75.5), (75.5, 75.5), (None, None), ("", None), ("bad", None),
])
def test_to_float(value, expected):
    assert _to_float(value) == expected
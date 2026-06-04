"""Tests for data validator"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from validator import Validator


@pytest.fixture
def valid_record():
    """Valid test record"""
    return {
        "safetyreportid": "12345",
        "patient_onsetage": 45,
        "patient_sex": 1,
        "drug_name": "ASPIRIN",
        "serious": 1
    }


def test_validate_valid_record(valid_record):
    """Test validating valid record"""
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_missing_required_field(valid_record):
    """Test validating record with missing required field"""
    del valid_record["safetyreportid"]
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is False
    assert len(errors) > 0


def test_validate_invalid_age_range(valid_record):
    """Test validating record with invalid age"""
    valid_record["patient_onsetage"] = 200
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is False


def test_validate_invalid_sex(valid_record):
    """Test validating record with invalid sex"""
    valid_record["patient_sex"] = 9
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is False


def test_validate_records_batch(valid_record):
    """Test validating batch of records"""
    records = [valid_record, valid_record.copy()]
    results = Validator.validate_records(records)
    
    assert len(results["passed"]) == 2
    assert len(results["failed"]) == 0


def test_generate_report():
    """Test generating validation report"""
    results = {"passed": [1, 2, 3], "failed": []}
    report = Validator.generate_report(results)
    
    assert "3" in report
    assert "100.0" in report

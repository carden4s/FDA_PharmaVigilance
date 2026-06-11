"""Tests for data validator"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from validator import Validator


@pytest.fixture
def valid_record():
    return {
        "safetyreportid": "12345",
        "patient_onsetage": 45,
        "patient_sex": 1,
        "drug_name": "ASPIRIN",
        "serious": 1
    }


def test_validate_valid_record(valid_record):
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_missing_required_field(valid_record):
    del valid_record["safetyreportid"]
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is False
    assert len(errors) > 0


def test_validate_invalid_age_range(valid_record):
    valid_record["patient_onsetage"] = 200
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is False


def test_validate_invalid_sex(valid_record):
    valid_record["patient_sex"] = 9
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is False


@pytest.mark.parametrize("serious_value", [1, 2, None])
def test_validate_serious_allowed(valid_record, serious_value):
    """openFDA serious is 1 (serious) or 2 (non-serious)."""
    valid_record["serious"] = serious_value
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is True


@pytest.mark.parametrize("sex_value", [0, 1, 2, None])
def test_validate_sex_allowed(valid_record, sex_value):
    """0 = Unknown is a valid openFDA sex code."""
    valid_record["patient_sex"] = sex_value
    is_valid, errors = Validator.validate_record(valid_record)
    assert is_valid is True


def test_validate_records_batch(valid_record):
    records = [valid_record, valid_record.copy()]
    results = Validator.validate_records(records)
    assert len(results["passed"]) == 2
    assert len(results["failed"]) == 0


def test_generate_report():
    results = {"passed": [1, 2, 3], "failed": []}
    report = Validator.generate_report(results)
    assert "3" in report
    assert "100.0" in report
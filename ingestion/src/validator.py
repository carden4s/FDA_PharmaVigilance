"""Data validation for FDA adverse events"""

from typing import List, Dict, Any, Tuple
from logger import logger


class Validator:
    """Validate FDA adverse event records"""

    VALIDATION_RULES = {
        "safetyreportid": {"required": True, "type": str},
        "patient_onsetage": {"type": int, "range": [0, 150]},
        "patient_sex": {"allowed": [1, 2, "U", None]},
        "drug_name": {"required": False, "type": str},
        "reaction_name": {"required": False, "type": str},
        "serious": {"allowed": [0, 1, None]},
    }

    @classmethod
    def validate_records(cls, records: List[Dict[str, Any]]) -> Dict[str, List]:
        """Validate a list of records."""
        results = {"passed": [], "failed": []}

        for idx, record in enumerate(records):
            is_valid, errors = cls.validate_record(record)
            if is_valid:
                results["passed"].append(record)
            else:
                results["failed"].append({"record": record, "errors": errors, "index": idx})

        logger.info(
            f"Validated {len(records)} records: "
            f"{len(results['passed'])} passed, {len(results['failed'])} failed"
        )
        return results

    @classmethod
    def validate_record(cls, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a single record."""
        errors = []

        for field, rules in cls.VALIDATION_RULES.items():
            value = record.get(field)

            # Required check
            if rules.get("required", False) and not value:
                errors.append(f"Required field '{field}' is missing")
                continue

            if value is None:
                continue

            # Type check (skip remaining checks if type is wrong to avoid comparison errors)
            expected_type = rules.get("type")
            if expected_type and not isinstance(value, expected_type):
                errors.append(
                    f"Field '{field}' has invalid type: "
                    f"expected {expected_type.__name__}, got {type(value).__name__}"
                )
                continue

            # Range check (only for numeric values)
            if "range" in rules and isinstance(value, (int, float)):
                min_val, max_val = rules["range"]
                if not (min_val <= value <= max_val):
                    errors.append(
                        f"Field '{field}' value {value} is outside range [{min_val}, {max_val}]"
                    )

            # Allowed-values check
            if "allowed" in rules and value not in rules["allowed"]:
                errors.append(
                    f"Field '{field}' value '{value}' not in allowed values {rules['allowed']}"
                )

        return len(errors) == 0, errors

    @staticmethod
    def generate_report(results: Dict[str, List]) -> str:
        """Generate a validation report (ASCII-only for Windows console safety)."""
        total = len(results["passed"]) + len(results["failed"])
        pass_rate = 100 * len(results["passed"]) / total if total > 0 else 0

        report = f"""
============================================
VALIDATION REPORT
============================================
Total Records: {total}
Passed: {len(results['passed'])} ({pass_rate:.1f}%)
Failed: {len(results['failed'])} ({100 - pass_rate:.1f}%)
============================================
"""
        if results["failed"]:
            report += "\nFailed Records:\n"
            for failed in results["failed"][:5]:
                report += f"\nRecord {failed['index']}:\n"
                for error in failed["errors"]:
                    report += f"  - {error}\n"
            if len(results["failed"]) > 5:
                report += f"\n... and {len(results['failed']) - 5} more failed records"

        return report
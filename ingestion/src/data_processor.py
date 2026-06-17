"""Data processing and flattening for FDA adverse events"""

from typing import List, Dict, Any
from datetime import datetime
from logger import logger


def _to_int(value: Any) -> Any:
    """Coerce a value to int, returning None if not possible."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _to_float(value: Any) -> Any:
    """Coerce a value to float, returning None if not possible."""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class DataProcessor:
    """Process and flatten FDA API responses"""

    @staticmethod
    def flatten_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten FDA API response into individual rows (one per drug-reaction combo)."""
        if not response or "results" not in response:
            logger.warning("Invalid or empty FDA response")
            return []

        flattened_rows = []
        for event in response["results"]:
            flattened_rows.extend(DataProcessor.flatten_event(event))

        logger.info(
            f"Flattened {len(response['results'])} events into {len(flattened_rows)} rows"
        )
        return flattened_rows

    @staticmethod
    def flatten_event(event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten a single FDA event with multiple drugs/reactions."""
        rows = []
        report_id = event.get("safetyreportid")

        if not report_id:
            return rows

        # Patient data (same for all drugs/reactions in this event)
        patient = event.get("patient", {}) or {}
        patient_age = patient.get("patientonsetage")
        patient_age_unit = patient.get("patientonsetageunit")
        patient_sex = patient.get("patientsex")
        patient_weight = patient.get("patientweight")

        # openFDA nests `drug` under `patient`; fall back to event root (sample format)
        drugs = patient.get("drug", event.get("drug", []))
        if not isinstance(drugs, list):
            drugs = [drugs]
        if not drugs:
            drugs = [{}]

        # Reactions are nested under `patient`
        reactions = patient.get("reaction", [])
        if not isinstance(reactions, list):
            reactions = [reactions]
        if not reactions:
            reactions = [{}]

        # One row per drug-reaction combination
        for drug in drugs:
            drug = drug or {}
            for reaction in reactions:
                reaction = reaction or {}
                row = {
                    # Report identifiers
                    "safetyreportid": report_id,
                    "report_type": event.get("reporttype"),

                    # Seriousness flags (coerced to int)
                    "serious": _to_int(event.get("serious")),
                    "seriousness_death": _to_int(event.get("seriousnessdeath")),
                    "seriousness_hospitalization": _to_int(event.get("seriousnesshospitalization")),
                    "seriousness_lifethreatening": _to_int(event.get("seriousnesslifethreatening")),
                    "seriousness_disability": _to_int(event.get("seriousnessdisability")),

                    # Patient data
                    "patient_onsetage": _to_int(patient_age),
                    "patient_onsetage_unit": _to_int(patient_age_unit),
                    "patient_sex": _to_int(patient_sex),
                    "patient_weight": _to_float(patient_weight),

                    # Drug data
                    "drug_name": drug.get("medicinalproduct"),
                    "drug_dose_value": drug.get("drugseparatedosagenumber"),
                    "drug_dose_unit": drug.get("drugdosagetext"),
                    "drug_route": drug.get("drugadministrationroute"),
                    "drug_indication": drug.get("drugindication"),

                    # Reaction data
                    "reaction_name": reaction.get("reactionmeddrapt"),
                    "reaction_outcome": _to_int(reaction.get("reactionoutcome")),
                    "reaction_meddra_pt": reaction.get("reactionmeddrapt"),
                    "reaction_meddra_llt": reaction.get("reactionmeddrallt"),

                    # Event dates
                    "event_date": event.get("eventdate"),
                    "report_date": event.get("reportdate"),
                    "received_date": event.get("receiptdate"),
                }
                rows.append(row)

        return rows

    @staticmethod
    def clean_values(data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize field values."""
        cleaned = {}
        for key, value in data.items():
            if value is None or value == "":
                cleaned[key] = None
                continue
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    cleaned[key] = None
                    continue
            cleaned[key] = value
        return cleaned

    @staticmethod
    def add_metadata(data: Dict[str, Any], source_drug: str, batch_id: str) -> Dict[str, Any]:
        """Add metadata to record."""
        data["loaded_at"] = datetime.utcnow().isoformat()
        data["source_drug"] = source_drug
        data["ingestion_batch_id"] = batch_id
        return data
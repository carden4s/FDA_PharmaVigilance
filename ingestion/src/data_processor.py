"""Data processing and flattening for FDA adverse events"""

from typing import List, Dict, Any
from datetime import datetime
from logger import logger


class DataProcessor:
    """Process and flatten FDA API responses"""
    
    @staticmethod
    def flatten_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten FDA API response into individual rows
        
        One adverse event can have multiple drugs and reactions.
        Output: One row per drug-reaction combination
        
        Args:
            response: FDA API JSON response
        
        Returns:
            List of flattened event records
        """
        if not response or "results" not in response:
            logger.warning("Invalid or empty FDA response")
            return []
        
        flattened_rows = []
        
        for event in response["results"]:
            flattened_rows.extend(DataProcessor.flatten_event(event))
        
        logger.info(f"Flattened {len(response['results'])} events into {len(flattened_rows)} rows")
        return flattened_rows
    
    @staticmethod
    def flatten_event(event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten single FDA event with multiple drugs/reactions
        
        Args:
            event: Single adverse event from FDA API
        
        Returns:
            List of rows, one per drug-reaction combo
        """
        rows = []
        report_id = event.get("safetyreportid")
        
        if not report_id:
            return rows
        
        # Get patient data (same for all drugs in this event)
        patient = event.get("patient", {})
        patient_age = patient.get("patientonsetage")
        patient_sex = patient.get("patientsex")
        patient_weight = patient.get("patientweight")
        
        # Get drugs list - FDA API stores drugs in patient object
        drugs = patient.get("drug", [])
        if not isinstance(drugs, list):
            drugs = [drugs] if drugs else []
        
        # Get reactions list - also in patient object
        reactions = patient.get("reaction", [])
        if not isinstance(reactions, list):
            reactions = [reactions] if reactions else []
        
        # If no reactions, create one row per drug
        if not reactions:
            reactions = [{}]
        
        # Create row for each drug-reaction combination
        for drug in drugs:
            for reaction in reactions:
                row = {
                    # Report identifiers
                    "safetyreportid": report_id,
                    "report_type": event.get("reporttype"),
                    
                    # Seriousness flags
                    "serious": event.get("serious"),
                    "seriousness_death": event.get("seriousnessdeath"),
                    "seriousness_hospitalization": event.get("seriousnesshospitalization"),
                    "seriousness_lifethreatening": event.get("seriousnesslifethreatening"),
                    "seriousness_disability": event.get("seriousnessdisability"),
                    
                    # Patient data
                    "patient_onsetage": patient_age,
                    "patient_sex": patient_sex,
                    "patient_weight": patient_weight,
                    
                    # Drug data
                    "drug_name": drug.get("medicinalproduct"),
                    "drug_dose_value": drug.get("openfda", {}).get("dosage_form", {}) or drug.get("drugseparatedosagenumber"),
                    "drug_dose_unit": drug.get("drugdosagetext"),
                    "drug_route": drug.get("drugadministrationroute"),
                    "drug_indication": drug.get("drugindication"),
                    
                    # Reaction data
                    "reaction_name": reaction.get("reactionmeddrapt"),
                    "reaction_outcome": reaction.get("reactionoutcome"),
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
    def normalize_field_names(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize field names to snake_case
        
        Args:
            data: Record with field names
        
        Returns:
            Normalized record
        """
        normalized = {}
        for key, value in data.items():
            # Convert to snake_case
            snake_case_key = key
            normalized[snake_case_key] = value
        
        return normalized
    
    @staticmethod
    def clean_values(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and normalize field values
        
        Args:
            data: Record to clean
        
        Returns:
            Cleaned record
        """
        cleaned = {}
        
        for key, value in data.items():
            # Handle None/null values
            if value is None or value == "":
                cleaned[key] = None
                continue
            
            # Handle numeric strings
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    cleaned[key] = None
                    continue
            
            cleaned[key] = value
        
        return cleaned
    
    @staticmethod
    def add_metadata(
        data: Dict[str, Any],
        source_drug: str,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Add metadata to record
        
        Args:
            data: Record
            source_drug: Which drug was being queried
            batch_id: Batch identifier
        
        Returns:
            Record with metadata
        """
        data["loaded_at"] = datetime.utcnow().isoformat()
        data["source_drug"] = source_drug
        data["ingestion_batch_id"] = batch_id
        
        return data

"""Configuration management for FDA ingestion pipeline"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    
    # Snowflake Configuration
    SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
    SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
    SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
    SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "PHARMA_DB")
    SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "BRONZE")
    SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "INGESTION_ROLE")
    
    # FDA API Configuration
    FDA_API_KEY = os.getenv("FDA_API_KEY")
    FDA_API_BASE_URL = os.getenv("FDA_API_BASE_URL", "https://api.fda.gov/drug/event.json")
    
    # Ingestion Configuration
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 1000))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))
    TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", 30))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/ingestion.log")
    
    # Environment
    ENV = os.getenv("ENV", "development")
    
    # Monitored Drugs
    MONITORED_DRUGS = [
        {"name": name, "fda_id": name.upper(), "priority": "normal"}
                for name in [
            "Aspirin", "Ibuprofen", "Acetaminophen", "Naproxen", "Metformin",
            "Atorvastatin", "Simvastatin", "Rosuvastatin", "Lisinopril", "Losartan",
            "Amlodipine", "Metoprolol", "Hydrochlorothiazide", "Furosemide", "Warfarin",
            "Clopidogrel", "Omeprazole", "Pantoprazole", "Gabapentin", "Pregabalin",
            "Sertraline", "Fluoxetine", "Citalopram", "Escitalopram", "Duloxetine",
            "Prednisone", "Levothyroxine", "Albuterol", "Insulin", "Tramadol",
            "Amoxicillin", "Azithromycin", "Ciprofloxacin", "Methotrexate", "Adalimumab",
            "Etanercept", "Rituximab", "Tocilizumab", "Apixaban", "Rivaroxaban",
            "Valsartan", "Olmesartan", "Ramipril", "Enalapril", "Carvedilol",
            "Diltiazem", "Verapamil", "Spironolactone", "Digoxin", "Hydralazine",
            "Clonidine", "Glipizide", "Glimepiride", "Sitagliptin", "Empagliflozin",
            "Dapagliflozin", "Semaglutide", "Liraglutide", "Pioglitazone", "Ezetimibe",
            "Pravastatin", "Fenofibrate", "Dabigatran", "Edoxaban", "Enoxaparin",
            "Heparin", "Ticagrelor", "Prasugrel", "Venlafaxine", "Bupropion",
            "Mirtazapine", "Trazodone", "Quetiapine", "Aripiprazole", "Olanzapine",
            "Risperidone", "Lamotrigine", "Lorazepam", "Alprazolam", "Clonazepam",
            "Zolpidem", "Topiramate", "Levetiracetam", "Oxycodone", "Hydrocodone",
            "Morphine", "Fentanyl", "Celecoxib", "Diclofenac", "Meloxicam",
            "Doxycycline", "Cephalexin", "Levofloxacin", "Metronidazole", "Clindamycin",
            "Nitrofurantoin", "Vancomycin", "Acyclovir", "Esomeprazole", "Ondansetron",
        ]
    ]
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Validate required configuration"""
        errors = []
        required_fields = [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PASSWORD",
            "FDA_API_KEY",
        ]
        
        for field in required_fields:
            if not getattr(cls, field):
                errors.append(f"Missing required config: {field}")
        
        return len(errors) == 0, errors


class DevelopmentConfig(Config):
    """Development configuration"""
    ENV = "development"
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production configuration"""
    ENV = "production"
    LOG_LEVEL = "INFO"
    BATCH_SIZE = 5000


def get_config() -> Config:
    """Get appropriate configuration"""
    env = os.getenv("ENV", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()

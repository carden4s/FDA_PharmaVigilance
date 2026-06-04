"""FDA API Client for adverse event data retrieval"""

import requests
import time
from typing import Optional, Dict, Any
from logger import logger
from config import Config

config = Config()


class FDAClient:
    """Client for FDA FAERS API"""
    
    def __init__(self, api_key: str, base_url: str = None):
        """
        Initialize FDA API client
        
        Args:
            api_key: FDA API key
            base_url: Base URL for FDA API
        """
        self.api_key = api_key
        self.base_url = base_url or config.FDA_API_BASE_URL
        self.timeout = config.TIMEOUT_SECONDS
        self.max_retries = config.MAX_RETRIES
    
    def test_connection(self) -> bool:
        """Test FDA API connection"""
        try:
            response = requests.get(
                self.base_url,
                params={"api_key": self.api_key, "limit": 1},
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.info("✓ FDA API connection successful")
            return True
        except Exception as e:
            logger.error(f"✗ FDA API connection failed: {str(e)}")
            return False
    
    def fetch_adverse_events(
        self,
        drug_name: str,
        limit: int = 1000,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch adverse events for a drug
        
        Args:
            drug_name: Drug name to query
            limit: Maximum records to return
            skip: Number of records to skip (pagination)
        
        Returns:
            FDA API response with results
        """
        query = f'patient.drug.medicinalproduct.exact:"{drug_name.upper()}"'
        
        params = {
            "api_key": self.api_key,
            "search": query,
            "limit": limit,
            "skip": skip,
        }
        
        logger.info(f"Fetching adverse events for {drug_name} (limit={limit}, skip={skip})")
        response = self._fetch_with_retry(params)
        
        if response and "results" in response:
            logger.info(f"Retrieved {len(response['results'])} records for {drug_name}")
        
        return response
    
    def _fetch_with_retry(self, params: Dict[str, Any], attempt: int = 1) -> Optional[Dict]:
        """
        Fetch with exponential backoff retry
        
        Args:
            params: Query parameters
            attempt: Current retry attempt
        
        Returns:
            API response or None on failure
        """
        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                wait_time = int(response.headers.get("X-Rate-Limit-Reset", 60))
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return self._fetch_with_retry(params, attempt)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt}/{self.max_retries}")
            if attempt < self.max_retries:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                return self._fetch_with_retry(params, attempt + 1)
            return None
        
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt}/{self.max_retries}: {e}")
            if attempt < self.max_retries:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                return self._fetch_with_retry(params, attempt + 1)
            return None
        
        except requests.exceptions.HTTPError as e:
            if response.status_code >= 500:
                logger.warning(f"Server error on attempt {attempt}/{self.max_retries}")
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    return self._fetch_with_retry(params, attempt + 1)
            else:
                logger.error(f"HTTP error: {response.status_code} - {e}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

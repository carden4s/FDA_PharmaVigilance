"""FDA API Client for adverse event data retrieval"""

import time
from typing import Optional, Dict, Any, List

import requests

from logger import logger
from config import Config

config = Config()


class FDAClient:
    """Client for FDA FAERS (openFDA drug/event) API"""

    PAGE_SIZE = 1000
    MAX_SKIP = 25000

    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or config.FDA_API_BASE_URL
        self.timeout = config.TIMEOUT_SECONDS
        self.max_retries = config.MAX_RETRIES
        self.session = requests.Session()        # reuse TCP/TLS (keep-alive)

    def test_connection(self) -> bool:
        try:
            params = {"limit": 1}
            if self.api_key:
                params["api_key"] = self.api_key
            response = self.session.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            logger.info("FDA API connection successful")
            return True
        except Exception as e:
            logger.error(f"FDA API connection failed: {str(e)}")
            return False

    def _build_search(self, drug_name: str,
                      start_date: Optional[str], end_date: Optional[str]) -> str:
        search = f'patient.drug.medicinalproduct.exact:"{drug_name.upper()}"'
        if start_date and end_date:
            search += f" AND receivedate:[{start_date} TO {end_date}]"
        return search

    def fetch_adverse_events(self, drug_name: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None,
                             max_records: Optional[int] = None) -> Dict[str, Any]:
        search = self._build_search(drug_name, start_date, end_date)
        window = f" [{start_date}..{end_date}]" if start_date and end_date else ""
        logger.info(f"Fetching adverse events for {drug_name}{window}")

        all_results: List[Dict[str, Any]] = []
        skip = 0
        total: Optional[int] = None

        while True:
            params = {"search": search, "limit": self.PAGE_SIZE, "skip": skip}
            if self.api_key:
                params["api_key"] = self.api_key

            response = self._fetch_with_retry(params)
            if not response or "results" not in response:
                break

            page = response["results"]
            all_results.extend(page)
            if total is None:
                total = response.get("meta", {}).get("results", {}).get("total", len(page))

            skip += self.PAGE_SIZE
            if len(page) < self.PAGE_SIZE:
                break
            if total is not None and skip >= total:
                break
            if skip >= self.MAX_SKIP:
                logger.warning(f"  {drug_name}: hit openFDA skip cap ({self.MAX_SKIP}); narrow the window")
                break
            if max_records and len(all_results) >= max_records:
                all_results = all_results[:max_records]
                break

        logger.info(f"Retrieved {len(all_results)} records for {drug_name}{window}")
        return {"results": all_results, "meta": {"total": total or len(all_results)}}

    def _fetch_with_retry(self, params: Dict[str, Any], attempt: int = 1) -> Optional[Dict]:
        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout)

            if response.status_code == 429:
                wait_time = int(response.headers.get("X-Rate-Limit-Reset", 60))
                logger.warning(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                return self._fetch_with_retry(params, attempt)

            if response.status_code == 404:
                return {"results": []}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt}/{self.max_retries}")
            if attempt < self.max_retries:
                time.sleep(2 ** attempt)
                return self._fetch_with_retry(params, attempt + 1)
            return None
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt}/{self.max_retries}: {e}")
            if attempt < self.max_retries:
                time.sleep(2 ** attempt)
                return self._fetch_with_retry(params, attempt + 1)
            return None
        except requests.exceptions.HTTPError as e:
            if response.status_code >= 500 and attempt < self.max_retries:
                logger.warning(f"Server error on attempt {attempt}/{self.max_retries}")
                time.sleep(2 ** attempt)
                return self._fetch_with_retry(params, attempt + 1)
            logger.error(f"HTTP error: {response.status_code} - {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
# ABOUTME: HTTP client for Store API communication
# ABOUTME: Wraps httpx with error handling and response parsing

import httpx
from typing import List, Dict, Any, Optional


class LegalMCPClient:
    """HTTP client for communicating with the Legal MCP Store API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the HTTP client

        Args:
            base_url: Base URL for the Store API (default: http://localhost:8000)
        """
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=300.0)

    def close(self):
        """Close the HTTP client"""
        self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes the client"""
        self.close()

    def health_check(self) -> bool:
        """
        Check if the Store API is reachable

        Returns:
            True if API is healthy (returns 200), False otherwise
        """
        try:
            response = self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    def list_codes(self) -> List[str]:
        """
        Get list of available legal codes from the database

        Returns:
            List of legal code identifiers (e.g., ['bgb', 'stgb'])

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
        """
        response = self.client.get("/legal-texts/gesetze-im-internet/codes")
        response.raise_for_status()
        return response.json()["codes"]

    def list_catalog(self) -> Dict[str, Any]:
        """
        Get catalog of importable legal codes

        Returns:
            Dictionary with catalog entries (code, title, url)

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
        """
        response = self.client.get("/legal-texts/gesetze-im-internet/catalog")
        response.raise_for_status()
        return response.json()

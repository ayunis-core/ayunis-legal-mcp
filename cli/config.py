# ABOUTME: Configuration management for CLI
# ABOUTME: Handles API URL from environment or default

import os


def get_api_url() -> str:
    """Get Store API URL from environment or use default"""
    url = os.getenv("LEGAL_API_BASE_URL", "http://localhost:8000")
    # Handle empty string case - fall back to default
    return url if url else "http://localhost:8000"

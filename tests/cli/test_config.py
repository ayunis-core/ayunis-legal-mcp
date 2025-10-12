# ABOUTME: Tests for CLI configuration module
# ABOUTME: Validates API URL resolution from environment and defaults

import os
import pytest
from cli.config import get_api_url


def test_get_api_url_returns_default_when_no_env_var(monkeypatch):
    """Test that get_api_url returns default URL when env var not set"""
    # Remove env var if it exists
    monkeypatch.delenv("LEGAL_API_BASE_URL", raising=False)

    url = get_api_url()

    assert url == "http://localhost:8000"


def test_get_api_url_returns_env_var_when_set(monkeypatch):
    """Test that get_api_url returns environment variable value when set"""
    test_url = "http://custom-api:9999"
    monkeypatch.setenv("LEGAL_API_BASE_URL", test_url)

    url = get_api_url()

    assert url == test_url


def test_get_api_url_with_empty_env_var_uses_default(monkeypatch):
    """Test that empty env var falls back to default"""
    monkeypatch.setenv("LEGAL_API_BASE_URL", "")

    url = get_api_url()

    assert url == "http://localhost:8000"

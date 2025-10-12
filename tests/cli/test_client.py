# ABOUTME: Tests for CLI HTTP client
# ABOUTME: Validates API communication with mocked httpx responses

import pytest
from unittest.mock import Mock, patch
import httpx
from cli.client import LegalMCPClient


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.Client for testing"""
    with patch("cli.client.httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client


def test_client_initialization_with_default_url():
    """Test that client initializes with default URL"""
    with patch("cli.client.httpx.Client") as mock_client_class:
        client = LegalMCPClient()

        mock_client_class.assert_called_once_with(
            base_url="http://localhost:8000",
            timeout=300.0
        )


def test_client_initialization_with_custom_url():
    """Test that client initializes with custom URL"""
    custom_url = "http://custom-api:9999"

    with patch("cli.client.httpx.Client") as mock_client_class:
        client = LegalMCPClient(base_url=custom_url)

        mock_client_class.assert_called_once_with(
            base_url=custom_url,
            timeout=300.0
        )


def test_health_check_returns_true_on_200(mock_httpx_client):
    """Test that health_check returns True when API returns 200"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_httpx_client.get.return_value = mock_response

    client = LegalMCPClient()
    result = client.health_check()

    assert result is True
    mock_httpx_client.get.assert_called_once_with("/health")


def test_health_check_returns_false_on_non_200(mock_httpx_client):
    """Test that health_check returns False when API returns non-200"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_httpx_client.get.return_value = mock_response

    client = LegalMCPClient()
    result = client.health_check()

    assert result is False


def test_health_check_returns_false_on_exception(mock_httpx_client):
    """Test that health_check returns False when request raises exception"""
    mock_httpx_client.get.side_effect = httpx.ConnectError("Connection failed")

    client = LegalMCPClient()
    result = client.health_check()

    assert result is False


def test_list_codes_returns_codes_list(mock_httpx_client):
    """Test that list_codes returns list of codes from API"""
    mock_response = Mock()
    mock_response.json.return_value = {"codes": ["bgb", "stgb", "gg"]}
    mock_httpx_client.get.return_value = mock_response

    client = LegalMCPClient()
    codes = client.list_codes()

    assert codes == ["bgb", "stgb", "gg"]
    mock_httpx_client.get.assert_called_once_with("/legal-texts/gesetze-im-internet/codes")


def test_list_codes_raises_on_http_error(mock_httpx_client):
    """Test that list_codes raises HTTPStatusError on API error"""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found",
        request=Mock(),
        response=Mock()
    )
    mock_httpx_client.get.return_value = mock_response

    client = LegalMCPClient()

    with pytest.raises(httpx.HTTPStatusError):
        client.list_codes()


def test_client_context_manager_closes_client(mock_httpx_client):
    """Test that using client as context manager closes it properly"""
    with LegalMCPClient() as client:
        pass

    mock_httpx_client.close.assert_called_once()


def test_client_close_method(mock_httpx_client):
    """Test that close method calls httpx client close"""
    client = LegalMCPClient()
    client.close()

    mock_httpx_client.close.assert_called_once()

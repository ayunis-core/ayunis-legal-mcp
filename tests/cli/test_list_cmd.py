# ABOUTME: Tests for list codes CLI command
# ABOUTME: Validates command behavior with mocked client

import pytest
from unittest.mock import Mock, patch, MagicMock
import typer
from typer.testing import CliRunner
from cli.commands.list_cmd import list_codes, list_catalog


runner = CliRunner()

# Create a Typer app for testing that wraps the command function
_test_app = typer.Typer()
_test_app.command()(list_codes)

# Create a separate Typer app for testing list_catalog
_test_catalog_app = typer.Typer()
_test_catalog_app.command()(list_catalog)


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_codes_success(mock_client_class):
    """Test list codes command with successful API response"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.list_codes.return_value = ["bgb", "stgb", "gg"]
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(_test_app)

    # Verify success
    assert result.exit_code == 0
    assert "bgb" in result.stdout
    assert "stgb" in result.stdout
    assert "gg" in result.stdout


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_codes_api_unreachable(mock_client_class):
    """Test list codes command when API is unreachable"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = False
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(_test_app)

    # Verify failure
    assert result.exit_code == 1
    assert "Error: Store API not reachable" in result.stdout
    assert "Make sure the Store API is running" in result.stdout


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_codes_with_json_output(mock_client_class):
    """Test list codes command with JSON output flag"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.list_codes.return_value = ["bgb", "stgb"]
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with --json flag
    result = runner.invoke(_test_app, ["--json"])

    # Verify success and JSON output
    assert result.exit_code == 0
    assert "bgb" in result.stdout
    assert "stgb" in result.stdout


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_codes_with_custom_api_url(mock_client_class):
    """Test list codes command with custom API URL"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.list_codes.return_value = ["bgb"]
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with custom API URL
    custom_url = "http://custom:9999"
    result = runner.invoke(_test_app, ["--api-url", custom_url])

    # Verify client was initialized with custom URL
    mock_client_class.assert_called_with(custom_url)
    assert result.exit_code == 0


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_codes_handles_exception(mock_client_class):
    """Test list codes command handles exceptions gracefully"""
    # Setup mock client that raises exception with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.list_codes.side_effect = Exception("Network error")
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(_test_app)

    # Verify failure
    assert result.exit_code == 1
    assert "Error:" in result.stdout


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_catalog_success(mock_client_class):
    """Test list catalog command with successful API response"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.list_catalog.return_value = {
        "count": 3,
        "entries": [
            {"code": "bgb", "title": "Bürgerliches Gesetzbuch", "url": "http://example.com/bgb"},
            {"code": "stgb", "title": "Strafgesetzbuch", "url": "http://example.com/stgb"},
            {"code": "gg", "title": "Grundgesetz", "url": "http://example.com/gg"}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(_test_catalog_app)

    # Verify success
    assert result.exit_code == 0
    assert "bgb" in result.stdout
    assert "Bürgerliches Gesetzbuch" in result.stdout
    assert "stgb" in result.stdout
    assert "Strafgesetzbuch" in result.stdout


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_catalog_api_unreachable(mock_client_class):
    """Test list catalog command when API is unreachable"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = False
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(_test_catalog_app)

    # Verify failure
    assert result.exit_code == 1
    assert "Error: Store API not reachable" in result.stdout
    assert "Make sure the Store API is running" in result.stdout


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_catalog_with_json_output(mock_client_class):
    """Test list catalog command with JSON output flag"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.list_catalog.return_value = {
        "count": 2,
        "entries": [
            {"code": "bgb", "title": "Bürgerliches Gesetzbuch", "url": "http://example.com/bgb"},
            {"code": "stgb", "title": "Strafgesetzbuch", "url": "http://example.com/stgb"}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with --json flag
    result = runner.invoke(_test_catalog_app, ["--json"])

    # Verify success and JSON output
    assert result.exit_code == 0
    assert "bgb" in result.stdout
    assert "stgb" in result.stdout


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_catalog_with_custom_api_url(mock_client_class):
    """Test list catalog command with custom API URL"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.list_catalog.return_value = {"count": 1, "entries": [{"code": "bgb", "title": "BGB", "url": "http://example.com"}]}
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with custom API URL
    custom_url = "http://custom:9999"
    result = runner.invoke(_test_catalog_app, ["--api-url", custom_url])

    # Verify client was initialized with custom URL
    mock_client_class.assert_called_with(custom_url)
    assert result.exit_code == 0


@patch("cli.commands.list_cmd.LegalMCPClient")
def test_list_catalog_handles_exception(mock_client_class):
    """Test list catalog command handles exceptions gracefully"""
    # Setup mock client that raises exception with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.list_catalog.side_effect = Exception("Network error")
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(_test_catalog_app)

    # Verify failure
    assert result.exit_code == 1
    assert "Error:" in result.stdout

# ABOUTME: Tests for search CLI command
# ABOUTME: Validates search behavior with mocked client

import pytest
from unittest.mock import MagicMock, patch
import typer
from typer.testing import CliRunner
from cli.commands.search_cmd import search_texts


runner = CliRunner()

# Create a Typer app for testing that wraps the command function
_test_app = typer.Typer()
_test_app.command()(search_texts)


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_success_without_code(mock_client_class):
    """Test searching texts successfully without code (searches all codes)"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.search_texts.return_value = {
        "code": None,
        "query": "Kaufvertrag",
        "count": 2,
        "results": [
            {"section": "§ 433", "sub_section": "1", "code": "bgb", "text": "Sample text about contract", "similarity_score": 0.95},
            {"section": "§ 434", "sub_section": "", "code": "bgb", "text": "Another text", "similarity_score": 0.85}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command without code (searches all)
    result = runner.invoke(_test_app, ["Kaufvertrag"])

    # Verify success
    assert result.exit_code == 0
    assert "§ 433" in result.stdout
    assert "§ 434" in result.stdout
    mock_client.search_texts.assert_called_once_with("Kaufvertrag", None, 10, 0.7)


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_success_with_code(mock_client_class):
    """Test searching texts successfully with code filter"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.search_texts.return_value = {
        "code": "bgb",
        "query": "Kaufvertrag",
        "count": 2,
        "results": [
            {"section": "§ 433", "sub_section": "1", "code": "bgb", "text": "Sample text about contract", "similarity_score": 0.95},
            {"section": "§ 434", "sub_section": "", "code": "bgb", "text": "Another text", "similarity_score": 0.85}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with --code option
    result = runner.invoke(_test_app, ["Kaufvertrag", "--code", "bgb"])

    # Verify success
    assert result.exit_code == 0
    assert "§ 433" in result.stdout
    assert "§ 434" in result.stdout
    mock_client.search_texts.assert_called_once_with("Kaufvertrag", "bgb", 10, 0.7)


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_with_code_short_option(mock_client_class):
    """Test searching with -c short option for code"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.search_texts.return_value = {
        "code": "stgb",
        "query": "Diebstahl",
        "count": 1,
        "results": [
            {"section": "§ 242", "sub_section": "1", "code": "stgb", "text": "Sample text", "similarity_score": 0.95}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with -c short option
    result = runner.invoke(_test_app, ["Diebstahl", "-c", "stgb"])

    # Verify success
    assert result.exit_code == 0
    mock_client.search_texts.assert_called_once_with("Diebstahl", "stgb", 10, 0.7)


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_with_custom_limit(mock_client_class):
    """Test searching with custom limit"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.search_texts.return_value = {
        "code": None,
        "query": "Kaufvertrag",
        "count": 1,
        "results": [
            {"section": "§ 433", "sub_section": "1", "code": "bgb", "text": "Sample text", "similarity_score": 0.95}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(_test_app, ["Kaufvertrag", "--limit", "5"])

    # Verify success
    assert result.exit_code == 0
    mock_client.search_texts.assert_called_once_with("Kaufvertrag", None, 5, 0.7)


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_with_custom_cutoff(mock_client_class):
    """Test searching with custom similarity cutoff"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.search_texts.return_value = {
        "code": None,
        "query": "Kaufvertrag",
        "count": 1,
        "results": [
            {"section": "§ 433", "sub_section": "1", "code": "bgb", "text": "Sample text", "similarity_score": 0.95}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with -x short option for cutoff
    result = runner.invoke(_test_app, ["Kaufvertrag", "--cutoff", "0.5"])

    # Verify success
    assert result.exit_code == 0
    mock_client.search_texts.assert_called_once_with("Kaufvertrag", None, 10, 0.5)


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_api_unreachable(mock_client_class):
    """Test search command when API is unreachable"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = False
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(_test_app, ["Kaufvertrag"])

    # Verify failure
    assert result.exit_code == 1
    assert "Error: Store API not reachable" in result.stdout


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_with_json_output(mock_client_class):
    """Test search command with JSON output"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.search_texts.return_value = {
        "code": "bgb",
        "query": "Kaufvertrag",
        "count": 1,
        "results": [
            {"section": "§ 433", "sub_section": "1", "code": "bgb", "text": "Sample text", "similarity_score": 0.95}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with --json flag
    result = runner.invoke(_test_app, ["Kaufvertrag", "--code", "bgb", "--json"])

    # Verify success and JSON output
    assert result.exit_code == 0
    assert "§ 433" in result.stdout


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_with_custom_api_url(mock_client_class):
    """Test search command with custom API URL"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.search_texts.return_value = {
        "code": "bgb",
        "query": "Kaufvertrag",
        "count": 1,
        "results": [
            {"section": "§ 433", "sub_section": "1", "code": "bgb", "text": "Sample text", "similarity_score": 0.95}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with custom API URL
    custom_url = "http://custom:9999"
    result = runner.invoke(_test_app, ["Kaufvertrag", "--code", "bgb", "--api-url", custom_url])

    # Verify client was initialized with custom URL
    mock_client_class.assert_called_with(custom_url)
    assert result.exit_code == 0


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_handles_exception(mock_client_class):
    """Test search command handles exceptions gracefully"""
    # Setup mock client that raises exception with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.search_texts.side_effect = Exception("Network error")
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(_test_app, ["Kaufvertrag"])

    # Verify failure
    assert result.exit_code == 1
    assert "Error:" in result.stdout


@patch("cli.commands.search_cmd.LegalMCPClient")
def test_search_with_code_and_all_options(mock_client_class):
    """Test searching with code and all other options combined"""
    # Setup mock client with context manager support
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.search_texts.return_value = {
        "code": "stgb",
        "query": "Diebstahl",
        "count": 1,
        "results": [
            {"section": "§ 242", "sub_section": "1", "code": "stgb", "text": "Sample text", "similarity_score": 0.4}
        ]
    }
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Run command with all options
    result = runner.invoke(_test_app, ["Diebstahl", "-c", "stgb", "-l", "5", "--cutoff", "0.5"])

    # Verify success
    assert result.exit_code == 0
    mock_client.search_texts.assert_called_once_with("Diebstahl", "stgb", 5, 0.5)

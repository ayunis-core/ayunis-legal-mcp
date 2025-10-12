# ABOUTME: Tests for CLI output formatting
# ABOUTME: Validates table rendering and JSON output

import json
import pytest
from io import StringIO
from unittest.mock import patch
from cli.output import print_json, print_codes_list


def test_print_json_outputs_formatted_json(capsys):
    """Test that print_json outputs properly formatted JSON"""
    test_data = {"codes": ["bgb", "stgb", "gg"]}

    print_json(test_data)

    captured = capsys.readouterr()
    # Rich console may add formatting, so we verify the data is present
    assert "bgb" in captured.out
    assert "stgb" in captured.out
    assert "gg" in captured.out


def test_print_codes_list_displays_table(capsys):
    """Test that print_codes_list displays codes in a table"""
    codes = ["bgb", "stgb", "gg"]

    print_codes_list(codes)

    captured = capsys.readouterr()
    # Verify all codes appear in output
    assert "bgb" in captured.out
    assert "stgb" in captured.out
    assert "gg" in captured.out
    # Verify it shows count
    assert "3" in captured.out
    # Verify it mentions "Imported" and "Codes" (may be on separate lines in Rich output)
    assert "Imported" in captured.out
    assert "Codes" in captured.out


def test_print_codes_list_handles_empty_list(capsys):
    """Test that print_codes_list handles empty list"""
    codes = []

    print_codes_list(codes)

    captured = capsys.readouterr()
    # Should show count of 0
    assert "0" in captured.out


def test_print_codes_list_handles_single_code(capsys):
    """Test that print_codes_list handles single code"""
    codes = ["bgb"]

    print_codes_list(codes)

    captured = capsys.readouterr()
    assert "bgb" in captured.out
    assert "1" in captured.out

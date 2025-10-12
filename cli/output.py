# ABOUTME: Output formatting utilities
# ABOUTME: Handles table rendering and JSON output

import json
from typing import Any, List
from rich.console import Console
from rich.table import Table

console = Console()


def print_json(data: Any):
    """
    Print data as formatted JSON

    Args:
        data: Data to output as JSON (will be serialized)
    """
    console.print_json(json.dumps(data))


def print_codes_list(codes: List[str]):
    """
    Print codes list as table

    Args:
        codes: List of legal code identifiers
    """
    table = Table(title=f"Imported Codes (Count: {len(codes)})")
    table.add_column("Code", style="cyan")

    for code in codes:
        table.add_row(code)

    console.print(table)


def print_catalog(catalog: dict):
    """
    Print catalog as table with code and title columns only

    Args:
        catalog: Catalog response with 'count' and 'entries' fields
    """
    entries = catalog.get("entries", [])
    table = Table(title=f"Available Legal Codes (Count: {catalog['count']})")
    table.add_column("Code", style="cyan")
    table.add_column("Title", style="white")

    for entry in entries:
        table.add_row(entry["code"], entry["title"])

    console.print(table)

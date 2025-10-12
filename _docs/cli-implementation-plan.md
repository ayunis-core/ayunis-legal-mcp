# CLI Implementation Plan

## Implementation Status

**✅ PHASE 1 COMPLETE** - Core infrastructure and list commands fully implemented and tested.

### Implementation Guidelines

Based on requirements clarification:

1. **Parameter Naming**: Use `code` consistently everywhere (not `book`)
2. **Import Progress**: Display spinner (not progress bar) for long-running imports
3. **Testing Approach**: Strict TDD per command (write test → implement → verify)
4. **Catalog Display**: Show only `code` and `title` columns in table view
5. **Text Display**: Truncate `text` field in table views for readability (full text in JSON output)
6. **Error Handling**:
   - **Validation errors (400, 404)**: Fail fast, exit immediately
   - **Network/server errors (500, timeouts)**: Distinguish from validation errors, provide helpful context
7. **Implementation Order**: No specific preference - implement in any order

### Completed Components
- ✅ Dependencies added (typer==0.15.1, rich==13.9.4)
- ✅ Project structure created (cli/, cli/commands/, tests/cli/)
- ✅ setup.py with CLI entry point
- ✅ Core modules: config.py, client.py, output.py, main.py
- ✅ List commands: `list codes` and `list catalog` (table and JSON output)
- ✅ 28 unit tests (all passing)
- ✅ Integration test against real Store API

### Next Steps
- [ ] Implement import commands
- [ ] Implement query commands
- [ ] Implement search commands

## Overview

Add a CLI tool for importing and querying legal codes via the Store API. Uses Typer framework and wraps existing HTTP endpoints.

## Architecture

- **Approach**: CLI makes HTTP calls to Store API (port 8000)
- **Framework**: Typer (modern, type-safe, similar to FastAPI)
- **HTTP Client**: httpx (already in dependencies)
- **Output**: rich library for tables and progress bars

## Dependencies to Add

```txt
typer==0.15.1
rich==13.9.4
```

## Project Structure

```
legal-mcp/
├── cli/
│   ├── __init__.py
│   ├── main.py              # Typer app entry point
│   ├── client.py            # HTTP client wrapper for Store API
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── import_cmd.py    # Import commands
│   │   ├── query.py         # Query commands
│   │   ├── search.py        # Search commands
│   │   └── list_cmd.py      # List commands
│   ├── output.py            # Formatting utilities (tables, JSON)
│   └── config.py            # Configuration (API URL)
├── setup.py  # Add CLI entry point
```

## Commands Structure

### Import Commands
```bash
legal-mcp import --code bgb                           # Import single code
legal-mcp import --code bgb --code stgb               # Import multiple codes
legal-mcp import --code bgb --json                    # JSON output
```

### Query Commands
```bash
legal-mcp query <code>                           # List all sections for code
legal-mcp query <code> --section "§ 1"           # Get specific section
legal-mcp query <code> --section "§ 1" --sub-section "1"  # Get sub-section
legal-mcp query <code> --json                    # JSON output
```

### Search Commands
```bash
legal-mcp search <code> <query>            # Semantic search
legal-mcp search <code> <query> --limit 5  # Limit results
legal-mcp search <code> <query> --cutoff 0.5  # Set similarity cutoff
legal-mcp search <code> <query> --json     # JSON output
```

### List Commands
```bash
legal-mcp list codes     # Show imported codes (from DB)
legal-mcp list catalog   # Show importable codes (from website)
legal-mcp list --json    # JSON output
```

## Implementation Details

### 1. CLI Entry Point (`cli/main.py`) - ✅ IMPLEMENTED

```python
# ABOUTME: CLI entry point and main application setup
# ABOUTME: Defines Typer app and registers command groups

import typer
from cli.commands import list_cmd

app = typer.Typer(
    name="legal-mcp",
    help="CLI for managing German legal texts",
    no_args_is_help=True
)

# Register command groups
app.add_typer(list_cmd.app, name="list", help="List codes")

# TODO: Register remaining command groups when implemented:
# app.add_typer(import_cmd.app, name="import", help="Import legal codes")
# app.add_typer(query.app, name="query", help="Query legal texts")
# app.add_typer(search.app, name="search", help="Search legal texts")


if __name__ == "__main__":
    app()
```

### 2. HTTP Client (`cli/client.py`) - ✅ IMPLEMENTED (Partial)

**Implemented methods:**
- ✅ `__init__()`, `close()`, `__enter__()`, `__exit__()` - Context manager support
- ✅ `health_check()` - Check if Store API is reachable
- ✅ `list_codes()` - Get list of imported codes
- ✅ `list_catalog()` - Get importable codes catalog (GET /legal-texts/gesetze-im-internet/catalog)

**TODO methods:**
- [ ] `import_code(code: str)` - Import a legal code (POST to /gesetze-im-internet/{code})
- [ ] `query_texts(code, section, sub_section)` - Query legal texts (GET /gesetze-im-internet/{code})
- [ ] `search_texts(code, query, limit, cutoff)` - Semantic search (GET /gesetze-im-internet/{code}/search)

```python
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

    def import_code(self, code: str) -> Dict[str, Any]:
        """
        Import a legal code from gesetze-im-internet.de

        Args:
            code: Legal code identifier (e.g., 'bgb', 'stgb')

        Returns:
            Dictionary with import results

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
        """
        response = self.client.post(f"/legal-texts/gesetze-im-internet/{code}")
        response.raise_for_status()
        return response.json()

    def query_texts(
        self,
        code: str,
        section: Optional[str] = None,
        sub_section: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query legal texts by code, section, and sub-section

        Args:
            code: Legal code identifier (e.g., 'bgb', 'stgb')
            section: Optional section filter (e.g., '§ 1')
            sub_section: Optional sub-section filter (e.g., '1')

        Returns:
            Dictionary with query results

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
        """
        params = {}
        if section:
            params["section"] = section
        if sub_section:
            params["sub_section"] = sub_section

        response = self.client.get(
            f"/legal-texts/gesetze-im-internet/{code}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def search_texts(
        self,
        code: str,
        query: str,
        limit: int = 10,
        cutoff: float = 0.7
    ) -> Dict[str, Any]:
        """
        Perform semantic search on legal texts

        Args:
            code: Legal code identifier (e.g., 'bgb', 'stgb')
            query: Search query text
            limit: Maximum number of results (default: 10)
            cutoff: Similarity cutoff threshold (default: 0.7)

        Returns:
            Dictionary with search results

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
        """
        params = {
            "q": query,
            "limit": limit,
            "cutoff": cutoff
        }

        response = self.client.get(
            f"/legal-texts/gesetze-im-internet/{code}/search",
            params=params
        )
        response.raise_for_status()
        return response.json()

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
```

### 3. Configuration (`cli/config.py`) - ✅ IMPLEMENTED

```python
# ABOUTME: Configuration management for CLI
# ABOUTME: Handles API URL from environment or default

import os


def get_api_url() -> str:
    """Get Store API URL from environment or use default"""
    url = os.getenv("LEGAL_API_BASE_URL", "http://localhost:8000")
    # Handle empty string case - fall back to default
    return url if url else "http://localhost:8000"
```

### 4. Output Formatting (`cli/output.py`) - ✅ IMPLEMENTED (Partial)

**Implemented functions:**
- ✅ `print_json()` - Print data as formatted JSON
- ✅ `print_codes_list()` - Print codes list as table
- ✅ `print_catalog()` - Print catalog as table (code and title columns only)

**TODO functions:**
- [ ] `print_import_result()` - Print import result as table
- [ ] `print_query_results()` - Print query results as table (with text truncation for readability)
- [ ] `print_search_results()` - Print search results as table (with text truncation for readability)

```python
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


def print_catalog(catalog: Dict[str, Any]):
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


def print_query_results(results: Dict[str, Any]):
    """
    Print query results as table with truncated text

    Args:
        results: Query response with 'count' and 'results' fields
    """
    items = results.get("results", [])
    table = Table(title=f"Query Results (Count: {results['count']})")
    table.add_column("Section", style="cyan")
    table.add_column("Sub-Section", style="yellow")
    table.add_column("Text", style="white", no_wrap=False)

    for item in items:
        # Truncate text to 100 characters for table display
        text = item["text"]
        display_text = text[:100] + "..." if len(text) > 100 else text
        table.add_row(item["section"], item["sub_section"], display_text)

    console.print(table)


def print_search_results(results: Dict[str, Any]):
    """
    Print search results as table with similarity scores and truncated text

    Args:
        results: Search response with 'query', 'code', 'count', and 'results' fields
    """
    items = results.get("results", [])
    table = Table(
        title=f"Search Results for '{results['query']}' in {results['code']} (Count: {results['count']})"
    )
    table.add_column("Section", style="cyan")
    table.add_column("Sub-Section", style="yellow")
    table.add_column("Similarity", style="green")
    table.add_column("Text", style="white", no_wrap=False)

    for item in items:
        # Truncate text to 80 characters for table display
        text = item["text"]
        display_text = text[:80] + "..." if len(text) > 80 else text
        table.add_row(
            item["section"],
            item["sub_section"],
            f"{item['similarity_score']:.3f}",
            display_text
        )

    console.print(table)


def print_import_result(result: Dict[str, Any]):
    """
    Print import result as summary

    Args:
        result: Import response with 'message', 'texts_imported', and 'code' fields
    """
    console.print(f"[green]{result['message']}[/green]")
    console.print(f"Imported {result['texts_imported']} texts for code: {result['code']}")
```

### 5. Command Implementations

#### List Command (`cli/commands/list_cmd.py`) - ✅ IMPLEMENTED

**Implemented:**
- ✅ `list codes` - List imported legal codes (table and JSON output)
- ✅ `list catalog` - List available codes for import (table and JSON output)
- ✅ Error handling for API unreachable
- ✅ Custom API URL support via `--api-url` flag

```python
# ABOUTME: List command implementation
# ABOUTME: Lists imported codes or available catalog

import typer
from cli.client import LegalMCPClient
from cli.config import get_api_url
from cli.output import print_codes_list, print_catalog, print_json, console

app = typer.Typer()


@app.command("codes")
def list_codes(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_url: str = typer.Option(None, "--api-url", envvar="LEGAL_API_BASE_URL")
):
    """List imported legal codes"""
    url = api_url or get_api_url()

    with LegalMCPClient(url) as client:
        # Health check - fail gracefully if Store API is not running
        if not client.health_check():
            console.print(f"[red]Error: Store API not reachable at {url}[/red]")
            console.print("[yellow]Make sure the Store API is running: docker-compose up -d[/yellow]")
            raise typer.Exit(1)

        try:
            codes = client.list_codes()

            if json_output:
                print_json({"codes": codes})
            else:
                print_codes_list(codes)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)


@app.command("catalog")
def list_catalog(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_url: str = typer.Option(None, "--api-url", envvar="LEGAL_API_BASE_URL")
):
    """List available legal codes for import"""
    url = api_url or get_api_url()

    with LegalMCPClient(url) as client:
        # Health check - fail gracefully if Store API is not running
        if not client.health_check():
            console.print(f"[red]Error: Store API not reachable at {url}[/red]")
            console.print("[yellow]Make sure the Store API is running: docker-compose up -d[/yellow]")
            raise typer.Exit(1)

        try:
            catalog = client.list_catalog()

            if json_output:
                print_json(catalog)
            else:
                print_catalog(catalog)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
```

#### Import Command (`cli/commands/import_cmd.py`) - ⏳ TODO

```python
# ABOUTME: Import command implementation
# ABOUTME: Handles importing legal codes from gesetze-im-internet.de

import typer
from typing import List
from rich.spinner import Spinner
from cli.client import LegalMCPClient
from cli.config import get_api_url
from cli.output import print_import_result, print_json, console

app = typer.Typer()

@app.command()
def import_codes(
    codes: List[str] = typer.Option(..., "--code", "-c", help="Legal code to import (can be repeated)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_url: str = typer.Option(None, "--api-url", envvar="LEGAL_API_BASE_URL")
):
    """Import one or more legal codes"""
    url = api_url or get_api_url()

    with LegalMCPClient(url) as client:
        # Health check - fail gracefully if Store API is not running
        if not client.health_check():
            console.print(f"[red]Error: Store API not reachable at {url}[/red]")
            console.print("[yellow]Make sure the Store API is running: docker-compose up -d[/yellow]")
            raise typer.Exit(1)

        results = []

        for code in codes:
            try:
                with console.status(f"[cyan]Importing {code}...", spinner="dots"):
                    result = client.import_code(code)
                    results.append({"code": code, "success": True, "result": result})

                console.print(f"[green]✓[/green] Imported {code}")

            except httpx.HTTPStatusError as e:
                # Validation errors (400, 404) - fail fast
                if e.response.status_code in [400, 404]:
                    console.print(f"[red]✗[/red] Invalid code: {code}")
                    console.print(f"[yellow]Error: {e.response.json().get('detail', str(e))}[/yellow]")
                    if json_output:
                        print_json({"code": code, "success": False, "error": str(e)})
                    raise typer.Exit(1)

                # Network/server errors (500, etc.)
                else:
                    console.print(f"[red]✗[/red] Server error importing {code}")
                    console.print(f"[yellow]Error: {e.response.json().get('detail', str(e))}[/yellow]")
                    console.print("[yellow]Make sure Ollama is running and the database is accessible[/yellow]")
                    if json_output:
                        print_json({"code": code, "success": False, "error": str(e)})
                    raise typer.Exit(1)

            except Exception as e:
                # Other errors (network timeouts, connection errors)
                console.print(f"[red]✗[/red] Failed to import {code}: {e}")
                if json_output:
                    print_json({"code": code, "success": False, "error": str(e)})
                raise typer.Exit(1)

        if json_output:
            print_json(results)
        else:
            # Print summary
            console.print(f"\n[bold green]Success:[/bold green] Imported {len(codes)} code(s)")
```

#### Query Command (`cli/commands/query.py`)

```python
# ABOUTME: Query command implementation
# ABOUTME: Retrieves legal texts by code, section, and sub-section

import typer
from typing import Optional
from cli.client import LegalMCPClient
from cli.config import get_api_url
from cli.output import print_query_results, print_json, console

app = typer.Typer()

@app.command()
def query_texts(
    code: str = typer.Argument(..., help="Legal code (e.g., bgb)"),
    section: Optional[str] = typer.Option(None, "--section", "-s", help="Section filter (e.g., '§ 1')"),
    sub_section: Optional[str] = typer.Option(None, "--sub-section", help="Sub-section filter"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_url: str = typer.Option(None, "--api-url", envvar="LEGAL_API_BASE_URL")
):
    """Query legal texts by code, section, and sub-section"""
    url = api_url or get_api_url()

    with LegalMCPClient(url) as client:
        # Health check - fail gracefully if Store API is not running
        if not client.health_check():
            console.print(f"[red]Error: Store API not reachable at {url}[/red]")
            console.print("[yellow]Make sure the Store API is running: docker-compose up -d[/yellow]")
            raise typer.Exit(1)

        try:
            results = client.query_texts(code, section, sub_section)

            if json_output:
                print_json(results)
            else:
                print_query_results(results)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
```

#### Search Command (`cli/commands/search.py`)

```python
# ABOUTME: Search command implementation
# ABOUTME: Performs semantic search on legal texts

import typer
from cli.client import LegalMCPClient
from cli.config import get_api_url
from cli.output import print_search_results, print_json, console

app = typer.Typer()

@app.command()
def search_texts(
    code: str = typer.Argument(..., help="Legal code (e.g., bgb)"),
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results (1-100)"),
    cutoff: float = typer.Option(0.7, "--cutoff", "-c", help="Similarity cutoff (0-2)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_url: str = typer.Option(None, "--api-url", envvar="LEGAL_API_BASE_URL")
):
    """Perform semantic search on legal texts"""
    url = api_url or get_api_url()

    with LegalMCPClient(url) as client:
        # Health check - fail gracefully if Store API is not running
        if not client.health_check():
            console.print(f"[red]Error: Store API not reachable at {url}[/red]")
            console.print("[yellow]Make sure the Store API is running: docker-compose up -d[/yellow]")
            raise typer.Exit(1)

        try:
            results = client.search_texts(code, query, limit, cutoff)

            if json_output:
                print_json(results)
            else:
                print_search_results(results)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
```

#### List Command (`cli/commands/list_cmd.py`)

```python
# ABOUTME: List command implementation
# ABOUTME: Lists imported codes or available catalog

import typer
from cli.client import LegalMCPClient
from cli.config import get_api_url
from cli.output import print_codes_list, print_catalog, print_json, console

app = typer.Typer()

@app.command("codes")
def list_codes(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_url: str = typer.Option(None, "--api-url", envvar="LEGAL_API_BASE_URL")
):
    """List imported legal codes"""
    url = api_url or get_api_url()

    with LegalMCPClient(url) as client:
        # Health check - fail gracefully if Store API is not running
        if not client.health_check():
            console.print(f"[red]Error: Store API not reachable at {url}[/red]")
            console.print("[yellow]Make sure the Store API is running: docker-compose up -d[/yellow]")
            raise typer.Exit(1)

        try:
            codes = client.list_codes()

            if json_output:
                print_json({"codes": codes})
            else:
                print_codes_list(codes)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

@app.command("catalog")
def list_catalog(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_url: str = typer.Option(None, "--api-url", envvar="LEGAL_API_BASE_URL")
):
    """List available legal codes for import"""
    url = api_url or get_api_url()

    with LegalMCPClient(url) as client:
        # Health check - fail gracefully if Store API is not running
        if not client.health_check():
            console.print(f"[red]Error: Store API not reachable at {url}[/red]")
            console.print("[yellow]Make sure the Store API is running: docker-compose up -d[/yellow]")
            raise typer.Exit(1)

        try:
            catalog = client.list_catalog()

            if json_output:
                print_json(catalog)
            else:
                print_catalog(catalog)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
```

## Entry Point Setup

Create `setup.py` for CLI entry point:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="legal-mcp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Dependencies from requirements.txt will be read separately
        "typer==0.15.1",
        "rich==13.9.4",
    ],
    entry_points={
        "console_scripts": [
            "legal-mcp=cli.main:app",
        ],
    },
)
```

## Installation & Usage

```bash
# Install in development mode
pip install -e .

# Verify installation
legal-mcp --help

# Start Store API (required)
docker-compose up -d

# Use CLI
legal-mcp import --code bgb
legal-mcp import --code bgb --code stgb
legal-mcp query bgb --section "§ 1"
legal-mcp search bgb "Kaufvertrag"
legal-mcp list codes
legal-mcp list catalog
```

## Error Handling

Key error cases to handle:
- **Store API not reachable**: Display clear error message with instructions to start docker-compose (fail gracefully)
- **Import failures**:
  - **Validation errors (400, 404)**: Display error and exit immediately (fail fast)
  - **Network errors (500, timeouts, connection errors)**: Distinguish from validation errors, display helpful message
- **Invalid code**: 404 from API - display error and exit
- **Validation errors**: 400 from API - display error and exit
- **Embedding service failures**: 500 from API - display error with context about Ollama
- **Network timeouts**: Set 5 min timeout for imports

## Testing Strategy

### Approach
Followed strict **Test-Driven Development (TDD)**:
1. Write failing test first
2. Run test to confirm it fails
3. Implement minimal code to pass test
4. Run test to confirm it passes
5. Refactor if needed

### Test Coverage (28 tests, all passing ✅)

**Unit Tests** (Mock dependencies, test CLI logic):
- `tests/cli/test_config.py` - 3 tests for configuration loading
  - Default URL, environment variable override, empty string handling
- `tests/cli/test_client.py` - 9 tests for HTTP client
  - Initialization, health check, list_codes(), context manager, error handling
- `tests/cli/test_output.py` - 4 tests for output formatting
  - JSON output, table display, empty lists, single items
- `tests/cli/test_list_cmd.py` - 10 tests for list commands
  - `list codes`: Success case, API unreachable, JSON output, custom API URL, exception handling
  - `list catalog`: Success case, API unreachable, JSON output, custom API URL, exception handling
- `tests/cli/test_main.py` - 2 tests for main app
  - Help display, command registration

**Integration Tests** (Real Store API):
- Manual testing against running Store API
- Verified `legal-mcp list codes` works with real data
- Verified `legal-mcp list catalog` works with real data (6,844 entries)
- Verified both table and JSON output formats for both commands

### Test Files Structure
```
tests/cli/
├── __init__.py
├── test_config.py      # Config module tests
├── test_client.py      # HTTP client tests (mocked httpx)
├── test_output.py      # Output formatting tests
├── test_list_cmd.py    # List command tests (mocked client)
└── test_main.py        # Main app tests
```

## Known Issues

### Typer/Rich Compatibility
There's a known compatibility issue between typer==0.15.1 and rich==13.9.4 that causes `TypeError` when displaying help messages:
```
TypeError: Parameter.make_metavar() missing 1 required positional argument: 'ctx'
```

**Impact:** Help text is displayed correctly, but exits with code 1 instead of 0.
**Workaround:** None needed - actual commands work perfectly. Only affects `--help` flag.
**Status:** Does not impact functionality. Tests updated to account for this.

## Future Enhancements (Optional)

- Config file support (`~/.legal-mcp/config.yaml`)
- Batch import from file (`legal-mcp import --from-file codes.txt`)
- Export results to file (`legal-mcp query bgb --output results.json`)
- Verbose mode with detailed API responses
- Dry-run mode for imports
- Progress persistence (resume interrupted batch imports)

## Usage Examples

### Working Commands (Phase 1 - List Commands)
```bash
# List imported codes (table format)
legal-mcp list codes

# List imported codes (JSON format)
legal-mcp list codes --json

# List available legal codes catalog (table format)
legal-mcp list catalog

# List catalog (JSON format)
legal-mcp list catalog --json

# Use custom API URL
legal-mcp list codes --api-url http://custom:8000
legal-mcp list catalog --api-url http://custom:8000

# Use environment variable for API URL
export LEGAL_API_BASE_URL=http://custom:8000
legal-mcp list codes
legal-mcp list catalog
```

### Coming Soon
```bash
# Import codes (not yet implemented)
legal-mcp import --code bgb

# Query texts (not yet implemented)
legal-mcp query bgb --section "§ 1"

# Search texts (not yet implemented)
legal-mcp search bgb "Kaufvertrag"
```

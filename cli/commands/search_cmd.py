# ABOUTME: Search command implementation
# ABOUTME: Performs semantic search on legal texts

from typing import Optional
import typer
from cli.client import LegalMCPClient
from cli.config import get_api_url
from cli.output import print_search_results, print_json, console

app = typer.Typer()


@app.command()
def search_texts(
    query: str = typer.Argument(..., help="Search query"),
    code: Optional[str] = typer.Option(
        None,
        "--code", "-c",
        help="Legal code to search (e.g., bgb). If not provided, searches all codes."
    ),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results (1-100)"),
    cutoff: float = typer.Option(0.7, "--cutoff", "-x", help="Similarity cutoff (0-2)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_url: str = typer.Option(None, "--api-url", envvar="LEGAL_API_BASE_URL")
):
    """
    Perform semantic search on legal texts.
    
    If no code is specified, searches across all available legal codes.
    
    Examples:
        legal-mcp search "Kaufvertrag"                    # Search all codes
        legal-mcp search "Kaufvertrag" --code bgb         # Search only BGB
        legal-mcp search "Diebstahl" -c stgb --limit 5    # Search StGB with limit
    """
    url = api_url or get_api_url()

    with LegalMCPClient(url) as client:
        # Health check - fail gracefully if Store API is not running
        if not client.health_check():
            console.print(f"[red]Error: Store API not reachable at {url}[/red]")
            console.print("[yellow]Make sure the Store API is running: docker-compose up -d[/yellow]")
            raise typer.Exit(1)

        try:
            results = client.search_texts(query, code, limit, cutoff)

            if json_output:
                print_json(results)
            else:
                print_search_results(results)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

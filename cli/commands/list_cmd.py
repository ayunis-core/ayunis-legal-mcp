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

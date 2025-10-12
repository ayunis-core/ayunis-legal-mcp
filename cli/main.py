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


if __name__ == "__main__":
    app()

# Legal MCP - German Legal Texts Search System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

A comprehensive system for searching and analyzing German legal texts using vector embeddings and semantic search, consisting of:

- **Store API**: FastAPI backend with PostgreSQL, pgvector, and Ollama embeddings
- **MCP Server**: FastMCP server providing tools for AI assistants to query legal texts
- **CLI Tool**: Command-line interface for importing and querying legal texts
- **Web Scraper**: Automatic extraction of legal texts from gesetze-im-internet.de
- **XML Parser**: Comprehensive parser for German legal XML format (gii-norm.dtd)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [CLI Tool](#cli-tool)
- [Environment Configuration](#environment-configuration)
- [API Documentation](#api-documentation)
- [Legal Text Features](#legal-text-features)
- [XML Parser](#xml-parser)
- [Development](#development)
- [Docker Commands](#docker-commands)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)

## Features

### Store API Features

- 🗄️ **PostgreSQL + pgvector** - Vector database for semantic search
- 🤖 **Ollama Integration** - Generate embeddings for legal texts
- 🌐 **Web Scraping** - Automatic extraction from gesetze-im-internet.de
- 📄 **XML Parsing** - Comprehensive parser for German legal XML format
- 🔍 **Semantic Search** - Vector-based similarity search for legal texts
- 📊 **Metadata Tracking** - Full document metadata and versioning
- 📝 **RESTful API** - FastAPI with automatic documentation
- 🐳 **Docker Support** - Easy deployment with containerization

### MCP Server Features

- 🔧 **FastMCP** - Modern MCP server implementation
- 🤝 **AI Assistant Integration** - Provides tools for querying legal texts
- 🔌 **HTTP API Client** - Connects to Store API for data access

### CLI Tool Features

- 📋 **List Commands** - View imported codes and available catalog
- 📥 **Import Commands** - Import legal codes with progress indication
- 🔍 **Query Commands** - Retrieve texts by code, section, and sub-section
- 🔎 **Search Commands** - Semantic search with similarity scoring
- 📊 **Multiple Output Formats** - Table view or JSON output
- ⚙️ **Configurable** - Custom API URL support via flag or environment variable

## Architecture

```
┌──────────────────────────────────────────────────┐
│                                                  │
│  Docker Network: legal-mcp-network               │
│                                                  │
│  ┌────────────────┐                              │
│  │  MCP Server    │ :8001                        │
│  │  (FastMCP)     │                              │
│  └───────┬────────┘                              │
│          │                                       │
│          │ LEGAL_API_BASE_URL                    │
│          │ http://store-api:8000                 │
│          │                                       │
│          ▼                                       │
│  ┌────────────────┐                              │
│  │  Store API     │ :8000                        │
│  │  (FastAPI)     │                              │
│  └───────┬────────┘                              │
│          │                                       │
│          │ DATABASE_URL                          │
│          │ postgresql://postgres:5432            │
│          │ OLLAMA_BASE_URL                       │
│          │                                       │
│          ▼                                       │
│  ┌────────────────┐                              │
│  │  PostgreSQL    │ :5432                        │
│  │  + pgvector    │                              │
│  └────────────────┘                              │
│                                                  │
└──────────────────────────────────────────────────┘
         │
         │ External Ollama Service
         │ (for embeddings)
         ▼
┌────────────────┐
│  Ollama API    │
│  (Remote/Local)│
└────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Ollama (local or remote endpoint for embeddings)
- Git

> ⚠️ **Important: Ollama Embedding Model**
>
> By default, this project uses the embedding model: `ryanshillington/Qwen3-Embedding-4B:latest`
>
> You must pull this model (or your configured alternative) before importing legal texts:
> ```bash
> ollama pull ryanshillington/Qwen3-Embedding-4B:latest
> ```
>
> You can use a different model by setting the `OLLAMA_EMBEDDING_MODEL` environment variable, but **the model must produce 2560-dimensional vectors**. Using a model with different dimensions will cause errors, as the database schema is fixed at 2560 dimensions. Changing to a model with different dimensions would require database schema modifications and re-importing all legal texts.

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd legal-mcp

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# Update OLLAMA_BASE_URL and OLLAMA_AUTH_TOKEN if needed
```

### 2. Start All Services

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps
```

This will start:

- **PostgreSQL** (host port 5436) - Database with pgvector extension
- **Store API** (port 8000) - FastAPI backend for legal texts
- **MCP Server** (port 8001) - FastMCP server for AI assistants

### 3. Run Database Migrations

```bash
# Run Alembic migrations to set up the database
docker-compose exec store-api alembic upgrade head
```

### 4. Import Legal Texts

```bash
# Import a test legal code (e.g., rag_1)
curl -X POST http://localhost:8000/legal-texts/gesetze-im-internet/rag_1

# Import German Civil Code (BGB)
curl -X POST http://localhost:8000/legal-texts/gesetze-im-internet/bgb

# Import other legal codes
curl -X POST http://localhost:8000/legal-texts/gesetze-im-internet/stgb  # Criminal Code
curl -X POST http://localhost:8000/legal-texts/gesetze-im-internet/gg    # Constitution
```

### 5. Test the API

```bash
# Check API health
curl http://localhost:8000/health

# Query legal texts by section
curl "http://localhost:8000/legal-texts/gesetze-im-internet/rag_1?section=%C2%A7%201"

# Semantic search (requires embeddings)
curl "http://localhost:8000/legal-texts/gesetze-im-internet/rag_1/search?q=Versicherung&limit=5"

# Access interactive API documentation
open http://localhost:8000/docs
```

## CLI Tool

The CLI provides a convenient command-line interface for managing legal texts without writing code.

### Installation

```bash
# Install in development mode (from project root)
pip install -e .

# Verify installation
legal-mcp --help
```

### Prerequisites

The CLI requires the Store API to be running:

```bash
# Start all services
docker-compose up -d

# Verify Store API is running
curl http://localhost:8000/health
```

### Available Commands

#### List Commands

**List Imported Codes**

```bash
# Show all imported legal codes in table format
legal-mcp list codes

# Output as JSON
legal-mcp list codes --json
```

**List Available Catalog**

```bash
# Show all available legal codes that can be imported
legal-mcp list catalog

# Output as JSON
legal-mcp list catalog --json
```

#### Import Command

```bash
# Import a single legal code
legal-mcp import --code bgb

# Import multiple legal codes
legal-mcp import --code bgb --code stgb --code gg

# Import with JSON output
legal-mcp import --code bgb --json
```

The import command displays a spinner while processing and shows progress for each code.

#### Query Command

```bash
# Query all texts for a legal code
legal-mcp query bgb

# Query specific section
legal-mcp query bgb --section "§ 1"

# Query specific sub-section
legal-mcp query bgb --section "§ 1" --sub-section "1"

# Output as JSON
legal-mcp query bgb --section "§ 1" --json
```

#### Search Command

```bash
# Semantic search in a legal code
legal-mcp search bgb "Kaufvertrag"

# Limit number of results
legal-mcp search bgb "Kaufvertrag" --limit 5

# Set similarity cutoff threshold (0-2, lower = stricter)
legal-mcp search bgb "Kaufvertrag" --cutoff 0.5

# Output as JSON
legal-mcp search bgb "Kaufvertrag" --json
```

### Configuration

**Default API URL**: `http://localhost:8000`

**Override with environment variable:**

```bash
export LEGAL_API_BASE_URL=http://custom-host:8000
legal-mcp list codes
```

**Override with command flag:**

```bash
legal-mcp list codes --api-url http://custom-host:8000
```

### Output Formats

**Table Format (default):**

- Clean, formatted tables with Rich library
- Text truncation for readability
- Color-coded output

**JSON Format:**

- Complete data with full text content
- Machine-readable for scripting
- Use `--json` flag with any command

### Example Workflow

```bash
# 1. Check available legal codes
legal-mcp list catalog

# 2. Import desired codes
legal-mcp import --code bgb --code stgb

# 3. Verify imports
legal-mcp list codes

# 4. Query specific sections
legal-mcp query bgb --section "§ 433"

# 5. Perform semantic search
legal-mcp search bgb "Kaufvertrag" --limit 10
```

## Environment Configuration

The application uses a `.env` file for configuration. See `.env.example` for a template.

### Required Environment Variables

```bash
# Ollama Configuration
OLLAMA_BASE_URL=https://your-ollama-endpoint.com
OLLAMA_AUTH_TOKEN=your-auth-token-here
OLLAMA_EMBEDDING_MODEL=ryanshillington/Qwen3-Embedding-4B:latest  # Optional, this is the default

# PostgreSQL Configuration
POSTGRES_HOST=postgres  # Use 'postgres' in Docker, 'localhost' for local dev
POSTGRES_PORT=5432      # Use 5432 in Docker, 5436 for local dev (see note below)
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=legal_mcp_db
```

> **Note:** The database user is hard-coded to `postgres` in `store/app/database.py` — there is no
> `POSTGRES_USER` setting. The container listens on 5432 but Compose publishes it on host port
> **5436** (`5436:5432`), so running the API outside Docker against the Compose database requires
> both `POSTGRES_HOST=localhost` and `POSTGRES_PORT=5436`.

> **Note:** The `OLLAMA_EMBEDDING_MODEL` variable allows you to use a different embedding model. However, **any alternative model must produce 2560-dimensional vectors** to be compatible with the database schema. The default model (`ryanshillington/Qwen3-Embedding-4B:latest`) is recommended.

### Additional Configuration (set in docker-compose.yml)

```bash
# MCP Server Configuration
LEGAL_API_BASE_URL=http://store-api:8000
```

The database URL is not an environment variable. `store/app/database.py` builds it from the
`POSTGRES_*` settings above, with the user fixed to `postgres` and the password URL-encoded:

```
postgresql+asyncpg://postgres:<POSTGRES_PASSWORD>@<POSTGRES_HOST>:<POSTGRES_PORT>/<POSTGRES_DB>
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### Legal Texts

- `POST /legal-texts/gesetze-im-internet/{book}` - Import legal text with embeddings
- `GET /legal-texts/gesetze-im-internet/codes` - List codes already imported into the database
- `GET /legal-texts/gesetze-im-internet/catalog` - List codes available for import from gii-toc.xml
- `GET /legal-texts/gesetze-im-internet/{code}` - Query legal texts by code/section
- `GET /legal-texts/gesetze-im-internet/{code}/search` - Semantic search with embeddings

#### System

- `GET /health` - Health check endpoint

## MCP Server

The MCP Server provides tools for AI assistants to interact with the legal text database through the Model Context Protocol.

### Available Tools

The MCP Server exposes the following tools:

- **`search_legal_texts`** - Perform semantic search on legal texts
  - Parameters: `query`, `code`, `limit` (1-20), `cutoff` (0-2)
  - Returns: List of matching legal text sections with similarity scores

- **`get_legal_section`** - Retrieve specific legal text sections
  - Parameters: `code`, `section`, `sub_section` (optional)
  - Returns: List of legal text sections matching the criteria

- **`get_available_codes`** - Get all available legal codes in the database
  - Returns: List of legal code identifiers

### Using the MCP Server

The MCP Server runs on port 8001 and can be accessed by MCP-compatible clients:

```bash
# Check MCP server is running
curl http://localhost:8001/health

# The MCP server automatically connects to the Store API
# using LEGAL_API_BASE_URL environment variable
```

For AI assistants, configure the MCP client to connect to `http://localhost:8001` (or the appropriate host/port for your deployment).

## Legal Text Features

### Importing Legal Texts

The system automatically:

1. Scrapes legal text XML from gesetze-im-internet.de
2. Parses the XML into structured legal text sections
3. Generates embeddings for each text section using Ollama
4. Stores the texts with their embeddings in PostgreSQL with pgvector

### Querying Legal Texts

Query by section identifier:

```bash
curl "http://localhost:8000/legal-texts/gesetze-im-internet/bgb?section=%C2%A7%201"
```

### Semantic Search

Search using natural language with vector similarity:

```bash
curl "http://localhost:8000/legal-texts/gesetze-im-internet/bgb/search?q=Kaufvertrag&limit=5&cutoff=0.7"
```

Parameters:

- `q` - Search query (required)
- `limit` - Maximum results (1-100, default: 10)
- `cutoff` - Similarity threshold (0-2, default: 0.5)
  - Lower values = stricter matching
  - 0.3-0.5: Very strict
  - 0.6-0.7: Good balance
  - 0.8-1.0: More permissive

## XML Parser

The system includes a comprehensive parser for the gii-norm.dtd format used by gesetze-im-internet.de.

### Parser Features

- **Complete DTD Coverage** - All major elements from gii-norm.dtd
- **Structured Data** - Type-safe dataclasses for all structures
- **Text Extraction** - Handles complex nested text with formatting
- **Table Support** - Captures table structures
- **Footnote Handling** - Extracts footnotes with references
- **Metadata Parsing** - Complete metadata extraction

### Using the Parser

```python
from app.scrapers import GesetzteImInternetScraper

# The scraper automatically uses the XML parser
scraper = GesetzteImInternetScraper()
legal_texts = scraper.scrape('bgb')

for text in legal_texts:
    print(f"Section: {text.section}")
    print(f"Text: {text.text}")
```

### Parsed Metadata

The parser extracts:

- Legal abbreviations (jurabk, amtabk)
- Dates (ausfertigung-datum)
- Citations (fundstelle)
- Titles (kurzue, langue, titel)
- Structural classification (gliederungseinheit)
- Section designations (enbez)
- Version information (standangabe)

## Development

### Local Development (without Docker)

1. **Install dependencies:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt

   # Install CLI tool in development mode
   pip install -e .
   ```

2. **Set up local database:**

   ```bash
   # Start only PostgreSQL
   docker-compose up postgres -d

   # Update .env to point at the published port on the host
   # POSTGRES_HOST=localhost
   # POSTGRES_PORT=5436
   ```

3. **Run migrations:**

   ```bash
   cd store
   alembic upgrade head
   ```

4. **Start Store API:**

   ```bash
   cd store
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Start MCP Server:**

   ```bash
   cd mcp
   export LEGAL_API_BASE_URL=http://localhost:8000
   python -m server.main
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_main.py -v

# Run CLI tests specifically
pytest tests/cli/ -v
```

## Contributing

We welcome contributions from the community! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- How to report bugs
- How to suggest features
- How to submit pull requests
- Development setup instructions
- Code style guidelines

## Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior through the project's reporting mechanisms.

## Security

Security is important to us. If you discover a security vulnerability, please follow our [Security Policy](SECURITY.md) for responsible disclosure. Do not open public issues for security vulnerabilities.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Legal texts sourced from [Gesetze im Internet](https://www.gesetze-im-internet.de/)
- Built with [FastAPI](https://fastapi.tiangolo.com/), [FastMCP](https://github.com/jlowin/fastmcp), and [Ollama](https://ollama.ai/)
- Vector similarity search powered by [pgvector](https://github.com/pgvector/pgvector)

## Support

- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and community chat

---

Made with ❤️ for the gov tech community

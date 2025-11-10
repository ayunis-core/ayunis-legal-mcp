# Legal MCP - Architecture and Development Guide

## Project Overview

Legal MCP is a semantic search system for German legal texts with two main components:

1. **Store API** (FastAPI) - Backend service with PostgreSQL + pgvector for storing and searching legal texts
2. **MCP Server** (FastMCP) - Model Context Protocol server that exposes legal search tools to AI assistants

**Purpose**: Enable AI assistants to semantically search German legal codes (BGB, StGB, GG, etc.) using natural language queries and retrieve specific legal sections.

## Architecture

```
┌─────────────────┐
│   AI Assistant  │
│  (via MCP SDK)  │
└────────┬────────┘
         │ stdio/http
         ▼
┌─────────────────┐
│   MCP Server    │  (Port 8001, FastMCP)
│                 │  Provides tools for searching legal texts
└────────┬────────┘
         │
         │ HTTP REST calls
         ▼
┌─────────────────┐
│   Store API     │  (Port 8000, FastAPI)
│                 │  REST endpoints for import, query, search
└────────┬────────┘
         │
         │ SQLAlchemy ORM (asyncpg)
         ▼
┌─────────────────┐
│   PostgreSQL    │  (Port 5432)
│   + pgvector    │  Stores legal texts with embeddings
└────────┬────────┘
         │
         │ HTTP API calls
         ▼
┌─────────────────┐
│     Ollama      │  (Port 11434, runs on host)
│                 │  Generates embeddings for semantic search
└─────────────────┘
```

## Directory Structure

```
legal-mcp/
├── store/                          # Store API (FastAPI backend)
│   ├── app/
│   │   ├── main.py                 # FastAPI app initialization
│   │   ├── config.py               # Settings (Pydantic Settings)
│   │   ├── database.py             # SQLAlchemy setup (async + sync engines)
│   │   ├── models.py               # Pydantic + SQLAlchemy models
│   │   ├── repository.py           # Data access layer
│   │   ├── embedding.py            # Ollama integration
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   ├── routers/                # API route handlers
│   │   └── scrapers/               # Legal text scrapers
│   │       └── gesetze_im_internet/
│   ├── alembic/                    # Database migrations
│   ├── tests/                      # Test suite
│   └── Dockerfile                  # Store API container
│
├── mcp/                            # MCP Server (FastMCP)
│   ├── server/
│   │   └── main.py                 # MCP server with tools
│   └── Dockerfile                  # MCP server container
│
├── docker-compose.yml              # Orchestration
├── requirements.txt                # Python dependencies
├── Makefile                        # Development commands
└── README.md                       # User documentation
```

## Key Components

### Store API (FastAPI)

Located in `store/app/`:

- **main.py** - FastAPI application entry point
- **models.py** - Data models (Pydantic for API, SQLAlchemy for database)
- **repository.py** - Database operations abstraction layer
- **embedding.py** - Embedding generation via Ollama
- **routers/legal_texts.py** - REST endpoints for legal texts
- **scrapers/** - Downloads and parses legal texts from sources

### MCP Server (FastMCP)

Located in `mcp/server/main.py`:

Provides read-only tools for AI assistants:
- `search_legal_texts` - Semantic search
- `get_legal_section` - Retrieve specific sections
- `get_available_codes` - List all available legal codes in the database

### Database

PostgreSQL with pgvector extension for vector similarity search. The main table stores:
- Legal text content
- Vector embeddings (2560-dimensional)
- Metadata (code, section, sub-section)
- Unique constraint on (code, section, sub_section) for upserts

Migrations managed via Alembic in `store/alembic/versions/`.

### Scrapers

Located in `store/app/scrapers/gesetze_im_internet/`:

- Downloads XML from gesetze-im-internet.de
- Parses gii-norm.dtd format
- Extracts structured legal text sections
- All scrapers implement the `Scraper` abstract base class

## Development Workflow

### Quick Start

```bash
# Start all services
make up

# Run migrations
make migrate

# Import a legal code
curl -X POST http://localhost:8000/legal-texts/gesetze-im-internet/bgb
```

### Common Commands

```bash
make help           # Show all available commands
make build          # Build Docker containers
make up             # Start services
make down           # Stop services
make logs           # View logs
make clean          # Remove containers + volumes
make migrate        # Run database migrations
make test           # Run tests
make shell-store    # Shell into store-api container
make shell-db       # PostgreSQL shell
```

See `Makefile` for the complete list of available commands.

### Local Development

```bash
# Start only PostgreSQL
docker-compose up postgres -d

# Set up Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
cd store && alembic upgrade head

# Start Store API
cd store && uvicorn app.main:app --reload

# Start MCP Server
cd mcp && python -m server.main
```

## Configuration

Environment variables are managed via Pydantic Settings in `store/app/config.py`.

Key variables:
- Database connection (POSTGRES_HOST, POSTGRES_PORT, etc.)
- Ollama endpoint (OLLAMA_BASE_URL)
- MCP Server API URL (LEGAL_API_BASE_URL)

Docker Compose sets appropriate defaults for containerized deployment.

## API Endpoints

Store API provides three main endpoints under `/legal-texts/gesetze-im-internet/{code}`:

- **POST** `/{code}` - Import a legal code
- **GET** `/{code}` - Query sections (params: section, sub_section)
- **GET** `/{code}/search` - Semantic search (params: q, limit, cutoff)

Full API documentation available at `http://localhost:8000/docs` when running.

## Design Patterns

### Repository Pattern
Database operations are abstracted through `LegalTextRepository` for testability and maintainability.

### Dependency Injection
FastAPI's `Depends()` used throughout for services, database sessions, and repositories.

### Async/Await
All I/O operations (database, HTTP, embeddings) use async/await for performance.

### Data Validation
Pydantic models validate all API inputs and outputs with type safety.

## Technical Details

### Vector Search
- Uses pgvector's cosine distance operator
- Lower distance = more similar (range: 0-2)
- Supports cutoff threshold for quality filtering

### Embedding Generation
- Ollama with Qwen3-Embedding-4B model
- 2560-dimensional vectors
- Batch processing for efficiency

### Database Upserts
- ON CONFLICT DO UPDATE for re-importing codes
- Unique constraint on (code, section, sub_section)

### XML Parsing
- Handles gii-norm.dtd format from gesetze-im-internet.de
- Extracts structured metadata and text content
- Preserves paragraph boundaries and sub-section identifiers

## Troubleshooting

### Services won't start
```bash
docker-compose logs        # Check logs
docker-compose ps          # Check status
```

### Database issues
```bash
docker-compose restart postgres
docker-compose exec postgres pg_isready -U legal_mcp
```

### Ollama not responding
- Ensure Ollama is running: `ollama serve`
- Pull the embedding model
- Check Docker can reach host (use `host.docker.internal`)

### Reset everything
```bash
make clean      # Removes containers and volumes
make build      # Rebuild
make up         # Start fresh
```

## Testing

```bash
make test                           # Run in container
docker-compose exec store-api pytest  # Direct execution
```

Tests located in `store/tests/`.

## Available Legal Codes

Examples from gesetze-im-internet.de:
- `bgb` - German Civil Code
- `stgb` - German Criminal Code
- `gg` - German Constitution
- `hgb` - German Commercial Code
- `zpo` - Code of Civil Procedure
- `stpo` - Code of Criminal Procedure

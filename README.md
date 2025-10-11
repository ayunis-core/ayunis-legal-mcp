# Legal MCP - German Legal Texts Search System

A comprehensive system for searching and analyzing German legal texts using vector embeddings and semantic search, consisting of:

- **Store API**: FastAPI backend with PostgreSQL, pgvector, and Ollama embeddings
- **MCP Server**: FastMCP server providing tools for AI assistants to query legal texts
- **Web Scraper**: Automatic extraction of legal texts from gesetze-im-internet.de
- **XML Parser**: Comprehensive parser for German legal XML format (gii-norm.dtd)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
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

- **PostgreSQL** (port 5432) - Database with pgvector extension
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

## Environment Configuration

The application uses a `.env` file for configuration. See `.env.example` for a template.

### Required Environment Variables

```bash
# Ollama Configuration
OLLAMA_BASE_URL=https://your-ollama-endpoint.com
OLLAMA_AUTH_TOKEN=your-auth-token-here

# PostgreSQL Configuration
POSTGRES_HOST=postgres  # Use 'postgres' in Docker, 'localhost' for local dev
```

### Additional Configuration (set in docker-compose.yml)

```bash
# Database URL (automatically constructed)
DATABASE_URL=postgresql+asyncpg://legal_mcp:legal_mcp_password@postgres:5432/legal_mcp_db

# MCP Server Configuration
LEGAL_API_BASE_URL=http://store-api:8000
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### Legal Texts

- `POST /legal-texts/gesetze-im-internet/{book}` - Import legal text with embeddings
- `GET /legal-texts/gesetze-im-internet/{code}` - Query legal texts by code/section
- `GET /legal-texts/gesetze-im-internet/{code}/search` - Semantic search with embeddings

#### System

- `GET /health` - Health check endpoint
- `GET /` - API information

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
   ```

2. **Set up local database:**

   ```bash
   # Start only PostgreSQL
   docker-compose up postgres -d

   # Update .env to use localhost
   # POSTGRES_HOST=localhost
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
```

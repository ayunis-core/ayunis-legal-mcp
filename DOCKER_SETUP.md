# Docker Setup Guide

## Quick Start

### 1. Start All Services

```bash
# Using Make (recommended)
make up

# Or using docker-compose directly
docker-compose up -d
```

This will start:

- **PostgreSQL** (port 5432) - Database with pgvector extension
- **Store API** (port 8000) - FastAPI backend for legal texts
- **MCP Server** (port 8001) - FastMCP server for AI assistants

### 2. Initialize Database

```bash
# Run migrations
make migrate

# Or manually
docker-compose exec store-api alembic upgrade head
```

### 3. Import Legal Texts

```bash
# Import German Civil Code (BGB)
make import-bgb

# Or manually
curl -X POST http://localhost:8000/legal-texts/gesetze-im-internet/bgb
```

### 4. Test the Setup

```bash
# Access API documentation
open http://localhost:8000/docs

# Test search
curl "http://localhost:8000/legal-texts/gesetze-im-internet/bgb/search?q=Kaufvertrag&limit=5"
```

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
│          │                                       │
│          ▼                                       │
│  ┌────────────────┐                              │
│  │  PostgreSQL    │ :5432                        │
│  │  + pgvector    │                              │
│  └────────────────┘                              │
│                                                  │
└──────────────────────────────────────────────────┘
```

## Environment Variables

### Store API

- `DATABASE_URL`: Connection to PostgreSQL
  - Default: `postgresql+asyncpg://legal_mcp:legal_mcp_password@postgres:5432/legal_mcp_db`
- `OLLAMA_HOST`: Ollama API endpoint for embeddings
  - Default: `http://host.docker.internal:11434`
  - Uses `host.docker.internal` to access Ollama running on your host machine

### MCP Server

- `LEGAL_API_BASE_URL`: Base URL for the Store API
  - Default: `http://store-api:8000`
  - Uses Docker service name `store-api` for internal communication

## Common Commands

```bash
# View all available commands
make help

# Start services
make up

# Stop services
make down

# View logs
make logs              # All services
make logs-store        # Store API only
make logs-mcp          # MCP Server only
make logs-db           # Database only

# Database operations
make migrate           # Run migrations
make shell-db          # Open PostgreSQL shell

# Container access
make shell-store       # Open shell in Store API
make shell-mcp         # Open shell in MCP Server

# Clean up everything
make clean             # Remove containers, networks, and volumes
```

## Development Mode

```bash
# Start with live reload
make dev

# This runs: docker-compose up
# Changes to ./store/app/ and ./mcp/server/ are reflected immediately
```

## Service Communication

### Internal (Container-to-Container)

Services communicate using Docker service names:

- MCP Server → Store API: `http://store-api:8000`
- Store API → PostgreSQL: `postgres:5432`

### External (Host-to-Container)

Access services from your host machine:

- Store API: `http://localhost:8000`
- MCP Server: `http://localhost:8001`
- PostgreSQL: `localhost:5432`

### Host Services (Container-to-Host)

Containers access services on your host:

- Ollama: `http://host.docker.internal:11434`

## Troubleshooting

### Services won't start

```bash
# Check logs
make logs

# Check specific service
make logs-store
make logs-mcp
```

### Database connection issues

```bash
# Check if PostgreSQL is healthy
docker-compose exec postgres pg_isready -U legal_mcp

# Restart PostgreSQL
docker-compose restart postgres
```

### MCP Server can't reach Store API

```bash
# Check if Store API is running
curl http://localhost:8000/docs

# Check MCP Server logs
make logs-mcp

# Verify network connectivity
docker-compose exec mcp-server ping store-api
```

### Reset everything

```bash
# Stop and remove everything
make clean

# Rebuild and start fresh
make build
make up
make migrate
```

### Check container status

```bash
# List running containers
make ps

# Or
docker-compose ps
```

## Ports

| Service    | Container Port | Host Port | Description     |
| ---------- | -------------- | --------- | --------------- |
| PostgreSQL | 5432           | 5432      | Database        |
| Store API  | 8000           | 8000      | FastAPI backend |
| MCP Server | 8001           | 8001      | FastMCP server  |

## Volumes

- `postgres_data`: Persists PostgreSQL database
- `./store/app`: Mounted for live reload (Store API code)
- `./store/data`: Data directory for documents
- `./mcp/server`: Mounted for live reload (MCP Server code)

## Networks

- `legal-mcp-network`: Bridge network connecting all services

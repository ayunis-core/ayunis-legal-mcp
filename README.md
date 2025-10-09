# Legal MCP - German Legal Texts Search System

A comprehensive system for searching and analyzing German legal texts, consisting of:

- **Store API**: FastAPI backend with PostgreSQL and vector embeddings
- **MCP Server**: FastMCP server providing tools for AI assistants to query legal texts

## Architecture

```
┌─────────────────┐
│   MCP Server    │  (Port 8001)
│   (FastMCP)     │
└────────┬────────┘
         │
         │ HTTP API calls
         │
         ▼
┌─────────────────┐
│   Store API     │  (Port 8000)
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │  (Port 5432)
│   + pgvector    │
└─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Ollama (running on host machine for embeddings)

### 1. Setup Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env if needed (default values should work for Docker setup)
```

### 2. Start All Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d
```

This will start:

- PostgreSQL database (port 5432)
- Store API (port 8000)
- MCP Server (port 8001)

### 3. Run Database Migrations

```bash
# Run Alembic migrations to set up the database
docker-compose exec store-api alembic upgrade head
```

### 4. Import Legal Texts

```bash
# Example: Import the German Civil Code (BGB)
curl -X POST http://localhost:8000/legal-texts/gesetze-im-internet/bgb
```

### 5. Test the API

```bash
# Search for legal texts
curl "http://localhost:8000/legal-texts/gesetze-im-internet/bgb/search?q=Kaufvertrag&limit=5"
```

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
   DATABASE_URL=postgresql+asyncpg://legal_mcp:legal_mcp_password@localhost:5432/legal_mcp_db
   ```

3. **Run migrations:**

   ```bash
   cd store
   alembic upgrade head
   ```

4. **Start Store API:**

   ```bash
   cd store
   uvicorn app.main:app --reload
   ```

5. **Start MCP Server:**
   ```bash
   cd mcp
   export LEGAL_API_BASE_URL=http://localhost:8000
   python -m server.main
   ```

### Project Structure

```
legal-mcp/
├── store/              # Store API (FastAPI)
│   ├── app/           # Application code
│   ├── alembic/       # Database migrations
│   ├── tests/         # Tests
│   ├── Dockerfile     # Store API container
│   └── requirements.txt
├── mcp/               # MCP Server
│   ├── server/        # Server code
│   │   └── main.py   # Main server file
│   ├── Dockerfile     # MCP server container
│   └── requirements.txt
├── docker-compose.yml # Main orchestration
├── requirements.txt   # Combined dependencies
└── README.md
```

## API Documentation

Once running, access the interactive API documentation:

- Store API: http://localhost:8000/docs
- Store API (alternative): http://localhost:8000/redoc

## Available Legal Codes

- `bgb` - Bürgerliches Gesetzbuch (German Civil Code)
- `stgb` - Strafgesetzbuch (German Criminal Code)
- `gg` - Grundgesetz (German Constitution)
- `hgb` - Handelsgesetzbuch (German Commercial Code)
- `zpo` - Zivilprozessordnung (Code of Civil Procedure)
- `stpo` - Strafprozessordnung (Code of Criminal Procedure)

## Environment Variables

### Store API

- `DATABASE_URL`: PostgreSQL connection string
- `OLLAMA_HOST`: Ollama API endpoint for embeddings

### MCP Server

- `LEGAL_API_BASE_URL`: Base URL for the Store API

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs store-api
```

### Database connection issues

```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check PostgreSQL health
docker-compose exec postgres pg_isready -U legal_mcp
```

### Reset everything

```bash
# Stop and remove all containers, volumes
docker-compose down -v

# Rebuild from scratch
docker-compose up --build
```

## License

[Your License Here]

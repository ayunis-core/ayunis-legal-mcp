# Legal MCP Setup Summary

## ✅ What Has Been Set Up

### 1. **FastAPI Application**

- Modern FastAPI backend with automatic API documentation
- Modular router structure for legal texts
- Type-safe data models with Pydantic

### 2. **PostgreSQL + pgvector**

- PostgreSQL database for data storage
- pgvector extension available for future vector operations
- SQLAlchemy ORM for database operations
- Async database support with asyncpg

### 3. **XML Parser for German Legal Texts**

- Comprehensive parser for gii-norm.dtd format
- Extracts metadata (abbreviations, dates, citations)
- Parses structured content (norms, paragraphs, footnotes, tables)
- Supports multiple parsing methods (file, string, bytes)

### 4. **Web Scraping Service**

- Scraper for gesetze-im-internet.de
- Automatic download of legal text XML files
- Configurable for different legal text sources

### 5. **Docker Compose Stack**

- PostgreSQL with pgvector
- FastAPI application
- Easy development and production deployment
- Health checks and proper networking

### 6. **API Endpoints**

- `GET /legal-texts/gesetze-im-internet/{book}` - Import legal text by abbreviation
- Interactive API documentation at `/docs` (Swagger UI) and `/redoc`
- Health check and info endpoints

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer (recommended)
- Docker and Docker Compose (for containerized deployment)

### Running the Application

#### Option 1: Docker (Recommended)

```bash
# Start the stack (PostgreSQL + API)
docker-compose up -d

# View logs
docker-compose logs -f api

# Access the application
open http://localhost:8000/docs
```

#### Option 2: Local Development

```bash
# 1. Install dependencies
uv pip install -r requirements.txt

# 2. Start PostgreSQL
docker-compose up -d postgres

# 3. Run the application
fastapi dev app/main.py
```

## 📝 Configuration

### Environment Variables

```bash
# Application
APP_NAME="Legal MCP API"
ADMIN_EMAIL=admin@example.com
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://legal_mcp:legal_mcp_password@localhost:5432/legal_mcp_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=legal_mcp
POSTGRES_PASSWORD=legal_mcp_password
POSTGRES_DB=legal_mcp_db

# Vector Database (for future use)
VECTOR_TABLE_NAME=legal_text_embeddings
EMBEDDING_DIMENSION=768
```

## 📚 API Usage Examples

### Import a Legal Text

```bash
# Import the German Civil Code (BGB)
curl "http://localhost:8000/legal-texts/gesetze-im-internet/bgb"

# Import other laws by abbreviation
curl "http://localhost:8000/legal-texts/gesetze-im-internet/stgb"  # Criminal Code
curl "http://localhost:8000/legal-texts/gesetze-im-internet/gg"    # Basic Law (Constitution)
```

### View API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Technology Stack

| Component           | Technology               | Purpose                        |
| ------------------- | ------------------------ | ------------------------------ |
| **Backend**         | FastAPI                  | Web framework                  |
| **Database**        | PostgreSQL + pgvector    | Data storage & vector support  |
| **ORM**             | SQLAlchemy               | Database operations            |
| **XML Parsing**     | lxml                     | Parse German legal XML         |
| **Web Scraping**    | BeautifulSoup4, requests | Content extraction             |
| **Package Manager** | uv                       | Fast Python package management |
| **Testing**         | pytest                   | Test framework                 |

## 📂 Project Structure

```
legal-mcp/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup
│   ├── models.py            # Pydantic data models
│   ├── dependencies.py      # Shared dependencies
│   ├── routers/
│   │   └── legal_texts.py   # Legal text endpoints
│   └── services/
│       ├── ingestion.py     # Ingestion service (stub)
│       └── scrapers/
│           ├── gesetzte_im_internet_scraper.py  # Web scraper
│           ├── xml_parser.py                     # XML parser
│           └── README_PARSER.md                  # Parser documentation
├── tests/
│   └── test_main.py         # API tests
├── _docs/
│   └── gii-norm.dtd         # DTD definition
├── docker-compose.yml       # Docker services
├── Dockerfile               # API container
├── requirements.txt         # Python dependencies
├── README.md               # Main documentation
├── LEGAL_FEATURES.md       # Legal features guide
├── PARSER_USAGE.md         # XML parser usage guide
└── SETUP_SUMMARY.md        # This file
```

## 🎯 Next Steps

1. **Implement Database Storage**: Add models and logic to store parsed legal texts in PostgreSQL

2. **Enhance API Endpoints**: Add endpoints for:

   - Listing stored legal texts
   - Searching through texts
   - Retrieving specific norms/paragraphs

3. **Add Error Handling**: Improve error handling in scrapers and parsers

4. **Implement Authentication**: Add proper auth to protect endpoints

5. **Add Background Tasks**: Use Celery or FastAPI BackgroundTasks for long-running imports

6. **Full-Text Search**: Implement PostgreSQL full-text search for legal texts

7. **Vector Search**: Integrate embeddings and semantic search capabilities

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View database logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U legal_mcp -d legal_mcp_db
```

### API Not Starting

```bash
# Check API logs
docker-compose logs -f api

# Verify dependencies are installed
uv pip list
```

### Import Failures

```bash
# Check if the book abbreviation is correct
# See gesetze-im-internet.de for available abbreviations

# View detailed logs
docker-compose logs -f api
```

## 📖 Documentation

- **Main README**: `README.md` - Project overview and getting started
- **Legal Features Guide**: `LEGAL_FEATURES.md` - Detailed feature documentation
- **XML Parser Usage**: `PARSER_USAGE.md` - Comprehensive parser guide
- **FastAPI Docs**: http://localhost:8000/docs (when running)

## 🤝 Contributing

The project follows modern Python best practices:

- Type hints throughout
- Pydantic for validation
- Async/await for I/O operations
- Modular architecture
- Comprehensive error handling

## 📄 License

MIT License - See LICENSE file for details.

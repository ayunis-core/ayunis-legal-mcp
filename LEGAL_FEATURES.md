# Legal Text Features

## Overview

The Legal MCP API provides features for importing and parsing German legal texts from gesetze-im-internet.de.

## Architecture

### Components

1. **Web Scraper** (`app/services/scrapers/gesetzte_im_internet_scraper.py`)

   - Extracts legal texts from gesetze-im-internet.de
   - Downloads XML files in the gii-norm.dtd format
   - Handles German legal text structure

2. **XML Parser** (`app/services/scrapers/xml_parser.py`)

   - Comprehensive parser for German legal XML format (gii-norm.dtd)
   - Extracts metadata (jurabk, amtabk, dates, citations)
   - Parses structured content (norms, paragraphs, footnotes, tables)
   - Handles complex document structures

3. **Database** (PostgreSQL + pgvector)

   - PostgreSQL for relational data storage
   - pgvector extension available for future vector operations
   - Stores document metadata and content

4. **API Endpoints** (`app/routers/legal_texts.py`)
   - Import legal texts from gesetze-im-internet.de
   - RESTful API for document management

## API Usage

### Import a Legal Text

```bash
# Import a specific law by its abbreviation
curl "http://localhost:8000/legal-texts/gesetze-im-internet/bgb"
```

Available endpoint:

- `GET /legal-texts/gesetze-im-internet/{book}` - Import a legal text by book abbreviation

## XML Parser

The XML parser (`GermanLegalXMLParser`) supports the complete gii-norm.dtd format used by gesetze-im-internet.de.

### Parsed Data Structures

**Metadata:**

- Legal abbreviation (jurabk)
- Official abbreviation (amtabk)
- Promulgation date (ausfertigung-datum)
- Citations (fundstelle)
- Titles and designations (kurzue, langue, titel, enbez)
- Structural units (gliederungseinheit)
- Version information (standangabe)

**Text Content:**

- Formatted paragraphs
- Tables with structure
- Footnotes and references
- Nested document structures

### Parser Usage Example

```python
from app.services.scrapers.xml_parser import GermanLegalXMLParser

# Initialize parser
parser = GermanLegalXMLParser()

# Parse an XML file
dokumente = parser.parse_file('path/to/legal_text.xml')

# Access parsed data
for norm in dokumente.norms:
    # Metadata
    print(f"Law: {norm.metadaten.jurabk}")
    print(f"Title: {norm.metadaten.titel}")

    # Text content
    if norm.textdaten and norm.textdaten.text:
        content = norm.textdaten.text.formatted_text
        if content:
            print(f"Content: {content.content}")

            # Paragraphs
            for para in content.paragraphs:
                print(f"Paragraph: {para}")

            # Footnotes
            for footnote in norm.textdaten.text.footnotes:
                print(f"Footnote {footnote.id}: {footnote.content}")

# Convert to dictionary for JSON export
data_dict = parser.to_dict(dokumente)
```

See `PARSER_USAGE.md` for comprehensive parser documentation.

## Docker Deployment

### Quick Start with Docker

```bash
# Start PostgreSQL and API
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Local Development Setup

```bash
# 1. Install dependencies
uv pip install -r requirements.txt

# 2. Start PostgreSQL
docker-compose up -d postgres

# 3. Run the application
fastapi dev app/main.py
```

### Stop the Stack

```bash
docker-compose down

# To also remove volumes (database data)
docker-compose down -v
```

## Configuration

Key environment variables:

### Database

- `DATABASE_URL` - Full database URL (default: postgresql+asyncpg://legal_mcp:legal_mcp_password@localhost:5432/legal_mcp_db)
- `POSTGRES_HOST` - Database host (default: localhost)
- `POSTGRES_PORT` - Database port (default: 5432)
- `POSTGRES_USER` - Database user (default: legal_mcp)
- `POSTGRES_PASSWORD` - Database password (default: legal_mcp_password)
- `POSTGRES_DB` - Database name (default: legal_mcp_db)

### Vector Database (for future use)

- `VECTOR_TABLE_NAME` - Table for embeddings (default: legal_text_embeddings)
- `EMBEDDING_DIMENSION` - Embedding dimensions (default: 768)

## Development

### Adding New Scrapers

To add support for a new legal text source:

1. Create a new scraper in `app/services/scrapers/`
2. Implement the scraping logic
3. Add appropriate error handling
4. Add a new endpoint in `app/routers/legal_texts.py`

### Working with the XML Parser

The parser supports:

- File parsing: `parse_file(filepath)`
- String parsing: `parse_string(xml_string)`
- Bytes parsing: `parse_bytes(xml_bytes)`

All parsing methods return a `Dokumente` object containing a list of `Norm` objects.

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View database logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U legal_mcp -d legal_mcp_db
```

### Import Failures

Common issues:

- Website unavailable or blocking requests
- Invalid book abbreviation
- Network connectivity issues

Check the API logs:

```bash
docker-compose logs -f api
```

## Future Enhancements

- [ ] Database storage for parsed legal texts
- [ ] Full-text search capabilities
- [ ] Document versioning and change tracking
- [ ] Support for additional legal text sources
- [ ] PDF export functionality
- [ ] Advanced filtering and querying
- [ ] Vector search integration for semantic queries
- [ ] Multi-language support

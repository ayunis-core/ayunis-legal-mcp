# Legal MCP API

A modern, high-performance FastAPI application for importing and parsing German legal texts from gesetze-im-internet.de.

## Features

- ✨ **FastAPI** - Modern, fast web framework for building APIs
- 🔧 **Pydantic** - Data validation using Python type annotations
- 📝 **Automatic API Documentation** - Interactive docs at `/docs` (Swagger UI) and `/redoc`
- 🧪 **Testing** - Comprehensive test suite with pytest
- ⚙️ **Configuration Management** - Environment-based settings with Pydantic Settings
- 📦 **Modular Structure** - Organized with routers and dependencies

### Legal Text Features

- 🗄️ **PostgreSQL + pgvector** - High-performance database with vector extension support
- 🌐 **Web Scraping** - Automatic extraction of legal texts from gesetze-im-internet.de
- 📄 **XML Parsing** - Comprehensive parser for German legal XML format (gii-norm.dtd)
- 📊 **Metadata Tracking** - Full document metadata and versioning
- 🐳 **Docker Compose** - Easy deployment with containerization

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── dependencies.py      # Shared dependencies
│   └── routers/             # API route modules
│       ├── __init__.py
│       ├── items.py         # Items endpoints
│       └── users.py         # Users endpoints
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Application tests
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment variables
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) - An extremely fast Python package installer and resolver (10-100x faster than pip!)

### Quick Start

We provide an automated setup script that installs everything you need:

```bash
# Make the setup script executable and run it
chmod +x setup.sh
./setup.sh
```

The script will:

- Check if `uv` is installed (and install it if needed)
- Create a virtual environment with `uv venv`
- Install all dependencies with `uv pip install`
- Create a `.env` configuration file

### Manual Installation

If you prefer manual setup:

1. **Install uv** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create a virtual environment:**

   ```bash
   uv venv
   ```

3. **Activate the virtual environment:**

   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```

4. **Install dependencies:**

   ```bash
   uv pip install -r requirements.txt
   ```

5. **Create `.env` file:**
   ```bash
   # Copy and customize the environment variables
   cat > .env << 'EOF'
   APP_NAME="Legal MCP API"
   ADMIN_EMAIL="admin@example.com"
   ITEMS_PER_USER=50
   DEBUG=false
   EOF
   ```

## Running the Application

### Development Server

Start the development server with auto-reload:

```bash
fastapi dev app/main.py
```

The application will be available at:

- API: http://127.0.0.1:8000
- Interactive API docs (Swagger UI): http://127.0.0.1:8000/docs
- Alternative API docs (ReDoc): http://127.0.0.1:8000/redoc

### Production Server

For production, use:

```bash
fastapi run app/main.py
```

Or with uvicorn directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Running Tests

Execute the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app tests/
```

## API Endpoints

### Root Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /info` - Application information

### Items

- `GET /items/` - List all items (with pagination)
- `GET /items/{item_id}` - Get a specific item
- `POST /items/` - Create a new item
- `PUT /items/{item_id}` - Update an item
- `DELETE /items/{item_id}` - Delete an item

### Users

- `GET /users/` - List all users (with pagination)
- `GET /users/me` - Get current user
- `GET /users/{username}` - Get a specific user
- `POST /users/` - Create a new user

## Configuration

The application uses Pydantic Settings for configuration management. Configuration can be set via:

1. Environment variables
2. `.env` file

Available settings:

- `APP_NAME` - Application name (default: "Legal MCP API")
- `ADMIN_EMAIL` - Administrator email
- `ITEMS_PER_USER` - Maximum items per user (default: 50)
- `DEBUG` - Debug mode (default: false)

## Development

### Adding New Routes

1. Create a new router file in `app/routers/`
2. Define your router with `APIRouter()`
3. Include it in `app/main.py` using `app.include_router()`

Example:

```python
# app/routers/new_route.py
from fastapi import APIRouter

router = APIRouter(prefix="/new", tags=["new"])

@router.get("/")
async def read_new():
    return {"message": "New route"}
```

```python
# app/main.py
from app.routers import new_route

app.include_router(new_route.router)
```

### Adding Dependencies

Define shared dependencies in `app/dependencies.py` and use them with FastAPI's `Depends()`:

```python
from fastapi import Depends
from app.dependencies import get_token_header

@router.get("/protected")
async def protected_route(token: str = Depends(get_token_header)):
    return {"message": "Protected data"}
```

## Why uv?

This project uses [uv](https://docs.astral.sh/uv/) instead of traditional pip for package management. Benefits include:

- ⚡ **10-100x faster** than pip for package installation and resolution
- 🦀 **Written in Rust** - Extremely performant and reliable
- 🔒 **Better dependency resolution** - More reliable than pip's resolver
- 📦 **Drop-in replacement** - Uses the same commands as pip (e.g., `uv pip install`)
- 🎯 **Modern Python tooling** - Replaces pip, pip-tools, pipx, poetry, and more

### uv Quick Reference

```bash
# Install packages
uv pip install package-name
uv pip install -r requirements.txt

# Uninstall packages
uv pip uninstall package-name

# List installed packages
uv pip list

# Freeze dependencies
uv pip freeze

# Check for conflicts
uv pip check

# Create virtual environment
uv venv
uv venv --python 3.11  # With specific Python version
```

## Technologies Used

- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server
- **pytest** - Testing framework
- **httpx** - HTTP client for testing
- **uv** - Fast Python package installer and resolver
- **PostgreSQL + pgvector** - Database with vector extension
- **SQLAlchemy** - ORM and database toolkit
- **BeautifulSoup4** - Web scraping
- **lxml** - XML parsing

## License

This project is licensed under the MIT License.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

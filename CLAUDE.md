# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Semantic search over German legal texts (BGB, StGB, GG, …), scraped from gesetze-im-internet.de,
embedded with Ollama and stored in PostgreSQL + pgvector. Three deliverables sit on top of one
backend:

```
MCP client (AI assistant)        legal-mcp CLI          curl / :8000/docs
        │ http :8001                  │ http                    │
        ▼                             ▼                         ▼
   mcp/server/main.py  ──────►  store/app (FastAPI, :8000)  ──►  Postgres+pgvector (host :5436)
                                        │
                                        └──► Ollama (embeddings, external)
```

`mcp/` and `cli/` are both thin HTTP clients of the Store API — they hold no database or
embedding logic. All real behaviour lives in `store/app/`.

## Commands

```bash
cp .env.example .env      # REQUIRED — docker-compose store-api uses env_file: .env
make up                   # docker-compose up -d
make migrate              # docker-compose exec store-api alembic upgrade head
make logs-store           # follow Store API logs
make clean                # down -v (drops the postgres volume)
```

Tests — **there are two suites and bare `pytest` only runs one of them**
(`pytest.ini` sets `testpaths = store/tests`, so the 49 CLI tests are skipped):

```bash
pytest store/tests tests/                 # everything (run from repo root)
pytest store/tests -v                     # backend only (this is what `make test` runs)
pytest tests/ -v                          # CLI only
pytest store/tests/test_repository.py::TestLegalTextRepository::test_add_legal_text -v
```

All tests are unit tests with mocked dependencies — no database or Ollama needed.
`rootdir` resolves to the repo root (`pytest.ini`) regardless of the directory you invoke from.
Tests **cannot** run inside the container: `.dockerignore` excludes them from the image
(see the comment in `store/Dockerfile`), so `docker-compose exec store-api pytest` will not work.

**No linter or formatter is configured** — no ruff/black/flake8 anywhere. The only static check is
`pyrightconfig.json`, and it covers `store/` and `mcp/` only; `cli/` and `tests/` are outside it.

Local dev without Docker:

```bash
docker-compose up postgres -d
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .   # -e . installs the `legal-mcp` CLI
(cd store && alembic upgrade head)                     # alembic.ini lives in store/
(cd store && uvicorn app.main:app --reload)
(cd mcp && LEGAL_API_BASE_URL=http://localhost:8000 python -m server.main)
```

## Configuration gotchas

- **Postgres is published on host port 5436**, not 5432 (`docker-compose.yml` maps `5436:5432`).
  `config.py` defaults `postgres_port=5432` and `.env.example` never sets it, so running the API
  outside Docker against the compose database needs **both** `POSTGRES_HOST=localhost` **and**
  `POSTGRES_PORT=5436`.
- **The DB user is hard-coded to `postgres`** in `store/app/database.py`; there is no
  `postgres_user` setting. (Consequence: `make shell-db` uses `-U legal_mcp` and does not work.)
- Settings come from `store/app/config.py` (Pydantic Settings, `.env`). `get_settings()` is
  `lru_cache`d — changing env vars requires a restart. Tests swap behaviour via
  `app.dependency_overrides` (see `store/tests/test_routers.py`), not by mutating the environment.
- `OLLAMA_EMBEDDING_MODEL` is configurable but the replacement **must emit 2560-dim vectors** —
  the column is `Vector(2560)` in `models.py` and `EMBEDDING_DIMENSION` in `embedding.py`.
  A different dimension means a migration plus a full re-import.
- Alembic's `env.py` imports `app.models` and reuses `app.database.SYNC_DATABASE_URL`, so
  migrations honour the same env vars as the app. Run alembic from `store/`.

## Things that are easy to get wrong

**Route declaration order in `store/app/routers/legal_texts.py` is load-bearing.** The literal
routes `/gesetze-im-internet/codes` and `/gesetze-im-internet/catalog` are declared *before*
`/gesetze-im-internet/{code}`. Any new literal route added after the `{code}` route will be
shadowed by it and never match.

**Every code-taking endpoint calls `validate_legal_code()` first** (`^[a-z0-9_-]+$`, ≤50 chars,
lowercased). This is SSRF protection — the code is interpolated into
`https://www.gesetze-im-internet.de/{code}/xml.zip`. Keep it on new endpoints.

**Upsert, not insert.** `LegalTextRepository.add_legal_texts_batch` uses
`ON CONFLICT ... DO UPDATE` against the named constraint
`uq_legal_texts_code_section_subsection` on `(code, section, sub_section)`. Re-importing a code is
idempotent. The scraper deliberately groups paragraphs by sub-section before creating rows so a
single import can't violate that constraint.

**Vector scores are cosine *distance*, not similarity** — 0 is identical, 2 is opposite, and
`cutoff` filters `distance <= cutoff`. Lower is better everywhere, including the `similarity_score`
field in API responses.

**`code` is the URL slug, not the legal abbreviation.** The scraper stores `rag_1` (from the URL),
not `RAG 1` (the XML's `jurabk`), so queries can round-trip.

**Embedding calls are batched** (`OLLAMA_BATCH_SIZE`, default 50) specifically to avoid 413s from
proxied Ollama instances. Don't collapse the loop in `embedding.py` back into one request.

## Store API surface

Five routes under `/legal-texts`, plus `GET /health` and OpenAPI at `/docs`:

| Method | Path | Notes |
|---|---|---|
| POST | `/gesetze-im-internet/{book}` | scrape → embed → upsert |
| GET | `/gesetze-im-internet/codes` | codes already in the DB |
| GET | `/gesetze-im-internet/catalog` | importable codes from gii-toc.xml (24h in-process cache) |
| GET | `/gesetze-im-internet/{code}` | `section`, `sub_section` (sub_section requires section) |
| GET | `/gesetze-im-internet/{code}/search` | `q`, `limit` 1–100 (10), `cutoff` 0–2 (0.7) |

## MCP server

`mcp/server/main.py` exposes exactly **three** tools — `search_legal_texts`, `get_legal_section`,
`get_available_codes`. (README also lists `import_legal_code`; that tool does not exist. Import is
intentionally not reachable over MCP.) Runs HTTP transport on `0.0.0.0:8001`; targets
`LEGAL_API_BASE_URL`; compose sets that to `http://store-api:8000`, and the in-code fallback is the
container name `http://legal-mcp-store-api:8000`.

**Nothing is authenticated.** `store/app/dependencies.py` has `get_query_token`/`get_token_header`
comparing against a hardcoded `"fake-super-secret-token"`, but no router depends on them — they are
tutorial leftovers, not a working auth layer.

## CLI

`pip install -e .` provides `legal-mcp` (Typer, entry point `cli.main:app`):
`legal-mcp list codes|catalog`, `import --code X`, `query CODE --section …`, `search CODE "query"`.
Every command takes `--json` for machine-readable output. API URL comes from `--api-url`, else
`LEGAL_API_BASE_URL`, else `http://localhost:8000`.

## Conventions

- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) — see CONTRIBUTING.md.
- Newer modules (`cli/*`, `mcp/server/main.py`, `catalog.py`) open with a two-line
  `# ABOUTME:` header; match it when adding files in those areas.
- Scrapers implement the `Scraper` ABC in `store/app/models.py`.
- Database access goes through `LegalTextRepository`; wire it in with FastAPI `Depends`
  (`store/app/dependencies.py`), which is also how tests substitute mocks.

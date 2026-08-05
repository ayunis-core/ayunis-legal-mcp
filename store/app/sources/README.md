# Adding a legal source adapter

Legal source integrations are split into three source-specific operations and one
shared import pipeline:

1. `get_catalog()` exposes stable source document IDs, legal abbreviations, titles,
   and canonical URLs.
2. `fetch_document(document_id)` performs source-specific network access.
3. `parse_document(...)` converts the source payload into `LegalDocument`.
4. `LegalImportService` hashes chunks, skips unchanged embeddings, and performs the
   document-scoped upsert.

Implement `LegalSourceAdapter` in `app/sources/` and keep HTTP/archive/XML details in
that adapter or its parser. Routers select an adapter and pass it to
`LegalImportService`; they must not parse source payloads or build database rows.

Use a stable, lowercase `source` identifier and an ISO-style `jurisdiction` such as
`DE` or `DE-BY`. `document_id` is owned by the source portal and must not be replaced
with `code`: the source ID may be opaque, while `code` is the human-facing legal
abbreviation used for filtering and citations.

Each parsed document should supply:

- source, jurisdiction, document ID, code, and title;
- canonical source URL;
- document type, build date, and applicable dates when the source provides them;
- text chunks with section and sub-section identifiers unique within the document.

Tests for a new adapter should use local fixtures and cover catalog mapping, fetch
errors, metadata, parsing, stable section keys, and end-to-end import through the
shared service. Live source portals must not be required by the automated test suite.

The generic query API supports exact lookup at `GET /legal-texts` and semantic search
at `GET /legal-texts/search`. Both accept jurisdiction, source, document, and code
filters. Source-specific compatibility routes may remain when existing callers rely
on them.

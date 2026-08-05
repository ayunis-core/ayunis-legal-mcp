"""Tests for source-independent legal import orchestration."""

import hashlib
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.import_service import LegalImportService
from app.models import LegalDocument, LegalDocumentMetadata, LegalText
from app.repository import LegalTextRepository
from app.sources import LegalSourceAdapter, LegalSourceCatalogEntry

pytestmark = pytest.mark.unit


def document() -> LegalDocument:
    return LegalDocument(
        metadata=LegalDocumentMetadata(
            source="test-source",
            jurisdiction="DE-BY",
            document_id="opaque-42",
            code="BayTest",
            document_title="Bayerisches Testgesetz",
            source_url="https://example.test/opaque-42",
        ),
        texts=[
            LegalText(
                text="(1) Testinhalt",
                code="BayTest",
                section="Art. 1",
                sub_section="1",
            )
        ],
    )


def adapter_for(parsed_document: LegalDocument) -> MagicMock:
    adapter = MagicMock(spec=LegalSourceAdapter)
    adapter.fetch_document.return_value = b"source payload"
    adapter.parse_document.return_value = parsed_document
    return adapter


def catalog_entry() -> LegalSourceCatalogEntry:
    return LegalSourceCatalogEntry(
        document_id="opaque-42",
        code="BayTest",
        title="Bayerisches Testgesetz",
        source_url="https://example.test/opaque-42",
    )


@pytest.mark.asyncio
async def test_import_hashes_embeds_and_upserts_changed_chunks():
    repository = AsyncMock(spec=LegalTextRepository)
    repository.get_content_hashes.return_value = {}
    embedding_service = AsyncMock()
    embedding_service.generate_embeddings.return_value = [[0.1] * 2560]
    parsed_document = document()

    result = await LegalImportService(repository, embedding_service).import_document(
        adapter_for(parsed_document),
        "opaque-42",
        catalog_entry=catalog_entry(),
    )

    assert result.texts_imported == 1
    assert result.texts_updated == 1
    repository.update_document_metadata.assert_awaited_once_with(
        parsed_document.metadata
    )
    embedding_service.generate_embeddings.assert_awaited_once_with(
        ["(1) Testinhalt"]
    )
    record = repository.add_legal_texts_batch.await_args.args[0][0]
    assert record.source == "test-source"
    assert record.jurisdiction == "DE-BY"
    assert record.document_id == "opaque-42"
    assert record.code == "BayTest"
    assert record.content_hash == hashlib.sha256(
        b"(1) Testinhalt"
    ).hexdigest()


@pytest.mark.asyncio
async def test_import_skips_embedding_for_unchanged_chunks():
    repository = AsyncMock(spec=LegalTextRepository)
    repository.get_content_hashes.return_value = {
        ("Art. 1", "1"): hashlib.sha256(b"(1) Testinhalt").hexdigest()
    }
    embedding_service = AsyncMock()

    result = await LegalImportService(repository, embedding_service).import_document(
        adapter_for(document()),
        "opaque-42",
        catalog_entry=catalog_entry(),
    )

    assert result.texts_imported == 1
    assert result.texts_updated == 0
    embedding_service.generate_embeddings.assert_not_awaited()
    repository.add_legal_texts_batch.assert_not_awaited()


@pytest.mark.asyncio
async def test_import_rejects_embedding_count_mismatch():
    repository = AsyncMock(spec=LegalTextRepository)
    repository.get_content_hashes.return_value = {}
    embedding_service = AsyncMock()
    embedding_service.generate_embeddings.return_value = []

    with pytest.raises(ValueError, match="different number of embeddings"):
        await LegalImportService(repository, embedding_service).import_document(
            adapter_for(document()),
            "opaque-42",
            catalog_entry=catalog_entry(),
        )

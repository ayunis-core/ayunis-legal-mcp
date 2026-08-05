"""Shared orchestration for legal-source imports."""

import asyncio
from dataclasses import dataclass
import hashlib
import logging
from typing import List, Sequence

from app.embedding import EmbeddingService
from app.models import LegalDocumentMetadata, LegalText, LegalTextDB
from app.repository import LegalTextRepository
from app.sources import LegalSourceAdapter, LegalSourceCatalogEntry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LegalImportResult:
    """Counts from importing one source document."""

    document_id: str
    code: str
    texts_imported: int
    texts_updated: int


class LegalImportService:
    """Fetch, parse, hash, embed, and upsert source-independent legal text."""

    def __init__(
        self,
        repository: LegalTextRepository,
        embedding_service: EmbeddingService,
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service

    async def import_document(
        self,
        adapter: LegalSourceAdapter,
        document_id: str,
        *,
        catalog_entry: LegalSourceCatalogEntry | None = None,
    ) -> LegalImportResult:
        """Import one document while avoiding embeddings for unchanged chunks."""
        if catalog_entry is None:
            catalog_entry = await asyncio.to_thread(
                adapter.get_catalog_entry, document_id
            )

        payload = await asyncio.to_thread(adapter.fetch_document, document_id)
        document = await asyncio.to_thread(
            adapter.parse_document, document_id, payload, catalog_entry
        )
        if not document.texts:
            raise ValueError(f"No legal texts found for document: {document_id}")

        metadata = document.metadata
        await self.repository.update_document_metadata(metadata)
        existing_hashes = await self.repository.get_content_hashes(
            source=metadata.source,
            jurisdiction=metadata.jurisdiction,
            document_id=metadata.document_id,
        )

        changed = []
        for legal_text in document.texts:
            content_hash = hashlib.sha256(legal_text.text.encode("utf-8")).hexdigest()
            key = (legal_text.section, legal_text.sub_section)
            if existing_hashes.get(key) != content_hash:
                changed.append((legal_text, content_hash))

        records: List[LegalTextDB] = []
        if changed:
            embeddings = await self.embedding_service.generate_embeddings(
                [legal_text.text for legal_text, _ in changed]
            )
            if len(embeddings) != len(changed):
                raise ValueError(
                    "Embedding service returned a different number of embeddings than texts"
                )
            for (legal_text, content_hash), embedding in zip(changed, embeddings):
                records.append(
                    self._to_database_record(
                        metadata, legal_text, content_hash, embedding
                    )
                )
            await self.repository.add_legal_texts_batch(records)

        logger.info(
            "Imported %s with %d total and %d changed texts",
            document_id,
            len(document.texts),
            len(records),
        )
        return LegalImportResult(
            document_id=metadata.document_id,
            code=metadata.code,
            texts_imported=len(document.texts),
            texts_updated=len(records),
        )

    @staticmethod
    def _to_database_record(
        metadata: LegalDocumentMetadata,
        legal_text: LegalText,
        content_hash: str,
        embedding: Sequence[float],
    ) -> LegalTextDB:
        return LegalTextDB(
            text=legal_text.text,
            text_vector=embedding,
            code=metadata.code,
            source=metadata.source,
            jurisdiction=metadata.jurisdiction,
            document_id=metadata.document_id,
            document_title=metadata.document_title,
            document_type=metadata.document_type,
            source_url=metadata.source_url,
            build_date=metadata.build_date,
            valid_from=metadata.valid_from,
            valid_to=metadata.valid_to,
            content_hash=content_hash,
            section=legal_text.section,
            sub_section=legal_text.sub_section,
        )

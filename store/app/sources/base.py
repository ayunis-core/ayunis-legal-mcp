"""Source-independent contracts for importing legal documents."""

from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models import LegalDocument


class LegalSourceCatalogEntry(BaseModel):
    """A document advertised by a legal source portal."""

    document_id: str = Field(description="Source-owned document identifier")
    code: str = Field(description="Human-facing legal abbreviation")
    title: str
    source_url: str
    document_type: Optional[str] = None


class SourceDocumentNotFound(ValueError):
    """Raised when a source catalog does not contain a requested document."""


class LegalSourceAdapter(ABC):
    """Catalog, transport, and parsing boundary for a legal source portal."""

    source: str
    jurisdiction: str

    @abstractmethod
    def get_catalog(self) -> List[LegalSourceCatalogEntry]:
        """Return documents currently advertised by the source."""

    def get_catalog_entry(self, document_id: str) -> LegalSourceCatalogEntry:
        """Resolve one source document from the catalog."""
        for entry in self.get_catalog():
            if entry.document_id == document_id:
                return entry
        raise SourceDocumentNotFound(
            f"Document {document_id!r} is not present in the {self.source} catalog"
        )

    @abstractmethod
    def fetch_document(self, document_id: str) -> bytes:
        """Fetch the source-owned representation of one document."""

    @abstractmethod
    def parse_document(
        self,
        document_id: str,
        payload: bytes,
        catalog_entry: Optional[LegalSourceCatalogEntry] = None,
    ) -> LegalDocument:
        """Parse a fetched payload into the shared legal-document model."""

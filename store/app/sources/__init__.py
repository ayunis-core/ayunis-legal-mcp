"""Legal source adapters."""

from app.sources.base import (
    LegalSourceAdapter,
    LegalSourceCatalogEntry,
    SourceDocumentNotFound,
)
from app.sources.gesetze_im_internet import GesetzeImInternetAdapter

__all__ = [
    "GesetzeImInternetAdapter",
    "LegalSourceAdapter",
    "LegalSourceCatalogEntry",
    "SourceDocumentNotFound",
]

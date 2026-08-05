"""Gesetze-im-Internet implementation of the legal source contract."""

from typing import List, Optional

from app.models import LegalDocument
from app.scrapers import GesetzteImInternetCatalog, GesetzteImInternetScraper
from app.sources.base import LegalSourceAdapter, LegalSourceCatalogEntry


class GesetzeImInternetAdapter(LegalSourceAdapter):
    """Federal-law adapter preserving the existing URL-slug document IDs."""

    source = "gesetze-im-internet"
    jurisdiction = "DE"

    def __init__(
        self,
        catalog: Optional[GesetzteImInternetCatalog] = None,
        scraper: Optional[GesetzteImInternetScraper] = None,
    ) -> None:
        self.catalog = catalog or GesetzteImInternetCatalog()
        self.scraper = scraper or GesetzteImInternetScraper()

    def get_catalog(self) -> List[LegalSourceCatalogEntry]:
        return [
            LegalSourceCatalogEntry(
                document_id=entry.code,
                code=entry.code,
                title=entry.title,
                source_url=entry.url,
            )
            for entry in self.catalog.get_catalog()
        ]

    def fetch_document(self, document_id: str) -> bytes:
        return self.scraper.fetch_document(document_id)

    def parse_document(
        self,
        document_id: str,
        payload: bytes,
        catalog_entry: Optional[LegalSourceCatalogEntry] = None,
    ) -> LegalDocument:
        return self.scraper.parse_document(
            code=document_id,
            zip_payload=payload,
            document_title=catalog_entry.title if catalog_entry else None,
            source_url=(
                catalog_entry.source_url
                if catalog_entry
                else f"https://www.gesetze-im-internet.de/{document_id}/xml.zip"
            ),
        )

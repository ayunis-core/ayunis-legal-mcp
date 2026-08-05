import io
import zipfile
from datetime import date, datetime
from typing import List

import requests

from app.models import (
    LegalDocument,
    LegalDocumentMetadata,
    Scraper,
    LegalText,
)
from .xml_parser import GermanLegalXMLParser, Norm


class GesetzteImInternetScraper(Scraper):
    """Scraper for legal texts from Gesetzte im Internet"""

    def scrape(self, code: str) -> List[LegalText]:
        """Compatibility wrapper returning only the parsed text chunks."""
        payload = self.fetch_document(code)
        return self.parse_document(code, payload).texts

    def fetch_document(self, code: str) -> bytes:
        """Fetch the official XML archive for a federal legal document."""
        url = f"https://www.gesetze-im-internet.de/{code}/xml.zip"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content

    def parse_document(
        self,
        code: str,
        zip_payload: bytes,
        document_title: str | None = None,
        source_url: str | None = None,
    ) -> LegalDocument:
        """Parse an official archive into the source-independent document model."""
        xml_data = self._extract_xml_from_zip(zip_payload)
        parser = GermanLegalXMLParser()
        result = parser.parse_bytes(xml_data)
        extracted_legal_texts: List[LegalText] = []
        for norm in result.norms:
            if (
                norm.textdaten
                and norm.textdaten.text
                and norm.textdaten.text.formatted_text
            ):
                if norm.metadaten.enbez:
                    # Group paragraphs by sub_section to avoid duplicates
                    # (multiple paragraphs with same sub_section get concatenated)
                    sub_section_texts: dict[str, list[str]] = {}
                    for p in norm.textdaten.text.formatted_text.paragraphs:
                        sub_section = self._extract_sub_section(p)
                        if sub_section not in sub_section_texts:
                            sub_section_texts[sub_section] = []
                        sub_section_texts[sub_section].append(p)

                    # Create one LegalText per unique sub_section
                    for sub_section, texts in sub_section_texts.items():
                        extracted_legal_texts.append(
                            LegalText(
                                text="\n\n".join(texts),
                                # we use the code from the url (e.g. rag_1) instead of the jurabk (e.g. RAG 1)
                                # so we know what to query later
                                code=code,
                                section=norm.metadaten.enbez,
                                sub_section=sub_section,
                            )
                        )
        if document_title is None:
            document_title = self._extract_document_title(result.norms) or code

        return LegalDocument(
            metadata=LegalDocumentMetadata(
                source="gesetze-im-internet",
                jurisdiction="DE",
                document_id=code,
                code=code,
                document_title=document_title,
                source_url=source_url
                or f"https://www.gesetze-im-internet.de/{code}/xml.zip",
                build_date=self._parse_date(result.builddate),
            ),
            texts=extracted_legal_texts,
        )

    def _extract_xml_from_zip(self, zip_file: bytes) -> bytes:
        with zipfile.ZipFile(io.BytesIO(zip_file), "r") as zip_ref:
            xml_files = [name for name in zip_ref.namelist() if name.endswith(".xml")]
            if not xml_files:
                raise ValueError("Legal source archive contains no XML document")
            with zip_ref.open(xml_files[0]) as file:
                return file.read()

    @staticmethod
    def _extract_document_title(norms: List[Norm]) -> str | None:
        for norm in norms:
            metadata = norm.metadaten
            if metadata.kurzue:
                return metadata.kurzue
            if metadata.langue:
                return metadata.langue
        return None

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        for date_format in ("%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        return None

    def _extract_sub_section(self, section: str) -> str:
        # if section number is present, the str begins with (n)
        if section.startswith("("):
            return section.split("(")[1].split(")")[0]
        # If no subsection number found, return empty string instead of full text
        return ""

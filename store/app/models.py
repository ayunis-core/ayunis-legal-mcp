"""
Pydantic models for API requests and responses
"""

from abc import abstractmethod, ABC
from datetime import date
from typing import List, Optional
from sqlalchemy import Column, Date, Integer, String, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector  # type: ignore
from pydantic import BaseModel, Field

Base = declarative_base()


class LegalText(BaseModel):
    """Pydantic model for legal text"""

    text: str = Field(description="The legal text content")
    code: str = Field(description="The legal code identifier")
    section: str = Field(description="The legal section identifier")
    sub_section: str = Field(description="The legal sub-section identifier")


class LegalDocumentMetadata(BaseModel):
    """Source-independent identity and citation metadata for a legal document."""

    source: str = Field(description="Stable legal source identifier")
    jurisdiction: str = Field(description="ISO-style jurisdiction identifier")
    document_id: str = Field(description="Source-owned document identifier")
    code: str = Field(description="Human-facing legal abbreviation")
    document_title: str = Field(description="Official or catalog document title")
    document_type: Optional[str] = Field(
        default=None, description="Source-provided document type"
    )
    source_url: Optional[str] = Field(
        default=None, description="Canonical URL at the source portal"
    )
    build_date: Optional[date] = Field(
        default=None, description="Date of the source export build"
    )
    valid_from: Optional[date] = Field(
        default=None, description="First applicable date, when supplied"
    )
    valid_to: Optional[date] = Field(
        default=None, description="Last applicable date, when supplied"
    )


class LegalDocument(BaseModel):
    """A parsed source document ready for shared import orchestration."""

    metadata: LegalDocumentMetadata
    texts: List[LegalText]


class LegalTextDB(Base):
    """
    SQLAlchemy model for legal text documents
    Uses 2560-dimension vectors for Qwen3-Embedding-4B model
    """

    __tablename__ = "legal_texts"
    __table_args__ = (
        # A source document owns its section namespace. Legal abbreviations are not
        # globally unique across German jurisdictions and source portals.
        UniqueConstraint(
            "source",
            "jurisdiction",
            "document_id",
            "section",
            "sub_section",
            name="uq_legal_texts_document_section_subsection",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    text_vector = Column(Vector(2560), nullable=False)  # type: ignore
    code = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    jurisdiction = Column(String(20), nullable=False, index=True)
    document_id = Column(String(255), nullable=False, index=True)
    document_title = Column(String(512), nullable=False)
    document_type = Column(String(100), nullable=True)
    source_url = Column(Text, nullable=True)
    build_date = Column(Date, nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    content_hash = Column(String(64), nullable=False)
    section = Column(String(255), nullable=False, index=True)
    sub_section = Column(String(255), nullable=False)


class Scraper(ABC):
    """Scraper for legal texts"""

    @abstractmethod
    def scrape(self, code: str) -> List[LegalText]:
        """Scrape a legal text from a code"""
        pass

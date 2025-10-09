"""
Pydantic models for API requests and responses
"""

from abc import abstractmethod, ABC
from typing import List
from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
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


class LegalTextDB(Base):
    """
    SQLAlchemy model for legal text documents
    Uses 2560-dimension vectors for Qwen3-Embedding-4B model
    """

    __tablename__ = "legal_texts"
    __table_args__ = (
        # Unique constraint: only one text per code+section+subsection combination
        UniqueConstraint(
            "code",
            "section",
            "sub_section",
            name="uq_legal_texts_code_section_subsection",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    text_vector = Column(Vector(2560), nullable=False)  # type: ignore
    code = Column(String(100), nullable=False, index=True)
    section = Column(String(50), nullable=False, index=True)
    sub_section = Column(String(50), nullable=False)


class Scraper(ABC):
    """Scraper for legal texts"""

    @abstractmethod
    def scrape(self, code: str) -> List[LegalText]:
        """Scrape a legal text from a code"""
        pass

"""The repository for the legal text"""

from typing import Optional, List, Tuple, Sequence, Any, Dict
from pydantic import BaseModel, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models import LegalTextDB


class LegalTextFilter(BaseModel):
    """
    Filter for querying legal texts

    Rules:
    - code: Optional, typically used to filter by legal code
    - section: Optional, filters by section identifier
    - sub_section: Optional, but can only be used when section is also provided
    """

    code: Optional[str] = None
    section: Optional[str] = None
    sub_section: Optional[str] = None

    @model_validator(mode="after")
    def validate_sub_section_requires_section(self) -> "LegalTextFilter":
        """Validate that sub_section can only be provided if section is also provided"""
        if self.sub_section and not self.section:
            raise ValueError(
                "sub_section filter can only be used when section filter is also provided"
            )
        return self


class LegalTextRepository:
    """The repository for the legal text"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_legal_text(
        self, filter: LegalTextFilter
    ) -> Optional[List[LegalTextDB]]:
        """
        Get legal texts matching the filter criteria

        Builds a dynamic query based on which filter fields are provided.
        All filters are optional, but sub_section requires section to be set.

        Args:
            filter: LegalTextFilter with optional code, section, and sub_section

        Returns:
            List of LegalTextDB objects matching the filter criteria

        Raises:
            ValueError: If sub_section is provided without section (validated by filter model)
        """
        query = select(LegalTextDB)

        # Code is required
        if filter.code:
            query = query.filter(LegalTextDB.code == filter.code)

        # Section is optional
        if filter.section:
            query = query.filter(LegalTextDB.section == filter.section)

        # Sub-section is optional
        if filter.sub_section:
            query = query.filter(LegalTextDB.sub_section == filter.sub_section)

        # Sort by section and sub_section
        query = query.order_by(LegalTextDB.section, LegalTextDB.sub_section)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_legal_text(self, legal_text: LegalTextDB) -> LegalTextDB:
        """Add a single legal text"""
        self.session.add(legal_text)
        await self.session.commit()
        await self.session.refresh(legal_text)
        return legal_text

    async def add_legal_texts_batch(
        self, legal_texts: List[LegalTextDB]
    ) -> List[LegalTextDB]:
        """
        Add or update multiple legal texts in a batch (upsert)

        If a legal text with the same (code, section, sub_section) combination
        already exists, it will be updated with the new text and embedding.
        Otherwise, a new record will be inserted.

        Args:
            legal_texts: List of LegalTextDB objects to insert or update

        Returns:
            List of LegalTextDB objects (note: returned objects won't have IDs for upserted records)
        """
        if not legal_texts:
            return []

        # Convert LegalTextDB objects to dictionaries for bulk insert
        values: List[Dict[str, Any]] = []
        for lt in legal_texts:
            values.append(
                {
                    "text": lt.text,
                    "text_vector": lt.text_vector,  # type: ignore
                    "code": lt.code,
                    "section": lt.section,
                    "sub_section": lt.sub_section,
                }
            )

        # Create insert statement with ON CONFLICT clause
        stmt = insert(LegalTextDB).values(values)

        # On conflict, update the text and text_vector
        # The constraint name matches what we created in the migration
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_legal_texts_code_section_subsection",
            set_={
                "text": stmt.excluded.text,
                "text_vector": stmt.excluded.text_vector,
            },
        )

        await self.session.execute(upsert_stmt)
        await self.session.commit()

        return legal_texts

    async def count_by_code(self, code: str) -> int:
        """Count legal texts by code"""
        query = select(LegalTextDB).filter(LegalTextDB.code == code)
        result = await self.session.execute(query)
        return len(list(result.scalars().all()))

    async def get_available_codes(self) -> List[str]:
        """Get all unique legal codes available in the database"""
        query = select(LegalTextDB.code).distinct().order_by(LegalTextDB.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def semantic_search(
        self,
        query_embedding: Sequence[float],
        code: Optional[str] = None,
        limit: int = 10,
        cutoff: Optional[float] = None,
    ) -> List[Tuple[LegalTextDB, float]]:
        """
        Perform semantic similarity search using vector embeddings

        Uses cosine distance to find the most similar legal texts to the query.
        Results are optionally filtered by code and ordered by similarity (closest first).

        Args:
            query_embedding: The embedding vector of the search query
            code: Optional legal code to filter by. If None, searches all codes.
            limit: Maximum number of results to return (default: 10)
            cutoff: Optional maximum cosine distance threshold (default: None)
                    Only return results with distance <= cutoff
                    Recommended values: 0.5 (very strict) to 1.0 (permissive)

        Returns:
            List of tuples containing (LegalTextDB, distance_score)
            where distance_score is the cosine distance (lower is more similar)

        Note:
            pgvector's <=> operator returns cosine distance where:
            - 0 means identical vectors
            - smaller values mean more similar
            - 2 means completely opposite vectors
        """
        # Use pgvector's cosine distance operator (<=>)
        # The operator returns distance, so we order ascending (closest first)
        distance_expr = LegalTextDB.text_vector.cosine_distance(query_embedding)  # type: ignore[attr-defined]

        query = (
            select(
                LegalTextDB,
                distance_expr.label("distance"),
            )
            .order_by("distance")
            .limit(limit)
        )

        # Filter by code only if specified
        if code is not None:
            query = query.filter(LegalTextDB.code == code)

        # Apply cutoff filter if specified
        if cutoff is not None:
            query = query.filter(distance_expr <= cutoff)

        result = await self.session.execute(query)
        rows = result.all()

        # Return list of (legal_text, distance) tuples
        return [(row[0], float(row[1])) for row in rows]

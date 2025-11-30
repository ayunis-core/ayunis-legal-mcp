"""
Legal texts router - Endpoints for importing and querying German legal texts
"""

import logging
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError

from app.scrapers import (
    GesetzteImInternetScraper,
    GesetzteImInternetCatalog,
    CatalogFetchError,
)
from app.repository import LegalTextRepository, LegalTextFilter
from app.embedding import EmbeddingService
from app.models import LegalTextDB
from app.dependencies import (
    get_legal_text_repository,
    get_embedding_service_dependency,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/legal-texts",
    tags=["legal-texts"],
    responses={404: {"description": "Not found"}},
)

# Security: Pattern for validating legal code format to prevent SSRF/injection attacks
CODE_PATTERN = re.compile(r"^[a-z0-9_-]+$", re.IGNORECASE)
MAX_CODE_LENGTH = 50


def validate_legal_code(code: str) -> str:
    """
    Validate legal code format to prevent SSRF and injection attacks

    Args:
        code: The legal code to validate

    Returns:
        The validated code in lowercase

    Raises:
        HTTPException: If the code format is invalid
    """
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Legal code cannot be empty"
        )

    if len(code) > MAX_CODE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Legal code too long. Maximum {MAX_CODE_LENGTH} characters."
        )

    if not CODE_PATTERN.match(code):
        raise HTTPException(
            status_code=400,
            detail="Invalid legal code format. Code must contain only letters, numbers, hyphens, and underscores."
        )

    return code.lower()


class LegalTextResponse(BaseModel):
    """Response model for a single legal text"""

    id: int
    text: str
    code: str
    section: str
    sub_section: str

    class Config:
        from_attributes = True


class LegalTextListResponse(BaseModel):
    """Response model for list of legal texts"""

    count: int
    results: List[LegalTextResponse]


class LegalTextSearchResult(BaseModel):
    """Response model for a single search result with similarity score"""

    text: str
    code: str
    section: str
    sub_section: str
    similarity_score: float = Field(
        description="Cosine distance (0 = identical, lower is more similar)"
    )

    class Config:
        from_attributes = True


class LegalTextSearchResponse(BaseModel):
    """Response model for semantic search results"""

    query: str
    code: Optional[str] = Field(
        default=None,
        description="Legal code filter used in the search. None if searching all codes."
    )
    count: int
    results: List[LegalTextSearchResult]


class LegalTextImportResponse(BaseModel):
    """Response for importing a legal text"""

    message: str
    texts_imported: int
    code: str


class AvailableCodesResponse(BaseModel):
    """Response model for available legal codes"""

    codes: List[str]


class LegalCodeCatalogEntryResponse(BaseModel):
    """Response model for a single catalog entry"""

    code: str = Field(description="Legal code identifier (e.g., 'bgb', 'stgb')")
    title: str = Field(description="Full title of the legal text")
    url: str = Field(description="URL to the XML zip file")


class CatalogResponse(BaseModel):
    """Response model for the catalog of importable legal codes"""

    count: int = Field(description="Total number of codes available for import")
    entries: List[LegalCodeCatalogEntryResponse] = Field(
        description="List of importable legal codes"
    )


@router.post("/gesetze-im-internet/{book}", response_model=LegalTextImportResponse)
async def import_legal_text(
    book: str,
    repository: LegalTextRepository = Depends(get_legal_text_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service_dependency),
):
    """
    Import a legal text from Gesetze im Internet

    This endpoint:
    1. Scrapes the legal text XML from gesetze-im-internet.de
    2. Parses the XML into structured legal text sections
    3. Generates embeddings for each text section using Ollama
    4. Stores the texts with their embeddings in the database

    Args:
        book: The legal code identifier (e.g., 'bgb', 'stgb')
        repository: Database repository (injected)
        embedding_service: Embedding service (injected)

    Returns:
        Response with success message and count of imported texts

    Raises:
        HTTPException: If scraping, embedding, or database operations fail
    """
    try:
        # Security: Validate code format to prevent SSRF/injection attacks
        book = validate_legal_code(book)
        logger.info(f"Starting import for legal code: {book}")

        # Validation: Check if code exists in catalog
        catalog_service = GesetzteImInternetCatalog()
        try:
            if not catalog_service.is_valid_code(book):
                logger.warning(f"Code {book} not found in catalog")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid legal code: {book}. Use /catalog endpoint to see available codes.",
                )
        except CatalogFetchError as catalog_error:
            # Graceful degradation: if catalog fetch fails, log and continue
            logger.warning(
                f"Could not validate code against catalog: {str(catalog_error)}. Proceeding with import attempt."
            )

        # Step 1: Scrape the legal texts
        scraper = GesetzteImInternetScraper()
        legal_texts = scraper.scrape(book)

        if not legal_texts:
            raise HTTPException(
                status_code=404,
                detail=f"No legal texts found for code: {book}",
            )

        logger.info(f"Scraped {len(legal_texts)} legal text sections")

        # Step 2: Generate embeddings for all texts (batch processing)
        logger.info("Generating embeddings...")
        texts_to_embed = [lt.text for lt in legal_texts]

        try:
            embeddings = await embedding_service.generate_embeddings(texts_to_embed)
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating embeddings: {str(e)}. Make sure Ollama is running and the model is available.",
            )

        logger.info(f"Generated {len(embeddings)} embeddings")

        # Step 3: Create database records with embeddings
        legal_text_dbs: List[LegalTextDB] = []
        for legal_text, embedding in zip(legal_texts, embeddings):
            legal_text_db = LegalTextDB(
                text=legal_text.text,
                text_vector=embedding,
                code=legal_text.code,
                section=legal_text.section,
                sub_section=legal_text.sub_section,
            )
            legal_text_dbs.append(legal_text_db)

        # Step 4: Save to database in batch
        logger.info("Saving to database...")
        await repository.add_legal_texts_batch(legal_text_dbs)

        logger.info(
            f"Successfully imported {len(legal_text_dbs)} texts for code: {book}"
        )

        return LegalTextImportResponse(
            message=f"Successfully imported legal texts for {book}",
            texts_imported=len(legal_text_dbs),
            code=book,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"Error importing legal text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error importing document: {str(e)}"
        )


@router.get("/gesetze-im-internet/codes", response_model=AvailableCodesResponse)
async def get_available_codes(
    repository: LegalTextRepository = Depends(get_legal_text_repository),
):
    """
    Get all available legal codes in the database

    Returns a list of unique legal code identifiers that have been
    imported into the database. Use these codes with other endpoints
    to query or search legal texts.

    Returns:
        List of available legal code identifiers (e.g., ['bgb', 'stgb', 'gg'])

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Fetching available legal codes")
        codes = await repository.get_available_codes()
        logger.info(f"Found {len(codes)} available legal codes")
        return AvailableCodesResponse(codes=codes)

    except Exception as e:
        logger.error(f"Error fetching available codes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching available codes: {str(e)}"
        )


@router.get("/gesetze-im-internet/catalog", response_model=CatalogResponse)
async def get_importable_catalog():
    """
    Get the catalog of all legal codes available for import from Gesetze im Internet

    This endpoint returns the complete list of legal codes that can be imported
    from the Gesetze im Internet website. This is different from the /codes endpoint
    which returns only the codes that have already been imported into the database.

    The catalog is fetched from the official Gesetze im Internet index:
    https://www.gesetze-im-internet.de/gii-toc.xml

    The catalog is cached for 24 hours to reduce load on the source website.

    Returns:
        List of all importable legal codes with their titles and URLs

    Raises:
        HTTPException: If catalog fetch fails
    """
    try:
        logger.info("Fetching importable legal codes catalog")
        catalog_service = GesetzteImInternetCatalog()
        catalog_entries = catalog_service.get_catalog()

        # Convert to response models
        entries = [
            LegalCodeCatalogEntryResponse(
                code=entry.code, title=entry.title, url=entry.url
            )
            for entry in catalog_entries
        ]

        logger.info(f"Found {len(entries)} codes in catalog")
        return CatalogResponse(count=len(entries), entries=entries)

    except Exception as e:
        logger.error(f"Error fetching catalog: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching catalog: {str(e)}")


@router.get("/gesetze-im-internet/{code}", response_model=LegalTextListResponse)
async def get_legal_texts(
    code: str,
    section: Optional[str] = Query(
        None, description="Filter by legal section (e.g., '§ 1', 'Art 1')"
    ),
    sub_section: Optional[str] = Query(
        None,
        description="Filter by sub-section number (e.g., '1', '2a'). Requires section parameter.",
    ),
    repository: LegalTextRepository = Depends(get_legal_text_repository),
):
    """
    Get legal texts by code with optional section and sub-section filters

    This endpoint retrieves legal texts from the database based on the provided filters:
    - **code** (required): The legal code identifier (e.g., 'bgb', 'stgb')
    - **section** (optional): The section identifier (e.g., '§ 1', 'Art 1')
    - **sub_section** (optional): The sub-section identifier (e.g., '1', '2')
      Note: sub_section can only be used when section is also provided

    Examples:
    - `/legal-texts/bgb` - Get all texts for the German Civil Code
    - `/legal-texts/bgb?section=§ 1` - Get all texts for § 1 BGB
    - `/legal-texts/bgb?section=§ 1&sub_section=1` - Get sub-section 1 of § 1 BGB
    - `/legal-texts/bgb?sub_section=1` - ❌ Invalid (requires section)

    Args:
        code: The legal code identifier (required)
        section: Optional section filter
        sub_section: Optional sub-section filter (requires section to be set)
        repository: Database repository (injected)

    Returns:
        List of matching legal texts with count

    Raises:
        HTTPException:
            - 400: If sub_section is provided without section
            - 404: If no texts found matching the filters
            - 500: If database query fails
    """
    try:
        # Security: Validate code format to prevent SSRF/injection attacks
        code = validate_legal_code(code)
        logger.info(
            f"Querying legal texts - code: {code}, section: {section}, sub_section: {sub_section}"
        )

        # Validate that sub_section can only be provided if section is also provided
        if sub_section and not section:
            raise HTTPException(
                status_code=400,
                detail="sub_section filter can only be used when section filter is also provided",
            )

        # Build filter (Pydantic will also validate at this point)
        try:
            filter = LegalTextFilter(
                code=code,
                section=section,
                sub_section=sub_section,
            )
        except ValidationError as e:
            # Handle Pydantic validation errors
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter parameters: {str(e)}",
            )

        # Query database
        legal_texts = await repository.get_legal_text(filter)

        if not legal_texts:
            raise HTTPException(
                status_code=404,
                detail=f"No legal texts found for code: {code}"
                + (f", section: {section}" if section else "")
                + (f", sub_section: {sub_section}" if sub_section else ""),
            )

        # Convert to response models (excluding embeddings)
        # Using Pydantic's from_attributes mode to convert SQLAlchemy models
        results = [LegalTextResponse.model_validate(lt) for lt in legal_texts]

        logger.info(f"Found {len(results)} legal texts matching the criteria")

        return LegalTextListResponse(count=len(results), results=results)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"Error querying legal texts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error querying legal texts: {str(e)}"
        )


@router.get("/search", response_model=LegalTextSearchResponse)
async def global_semantic_search_legal_texts(
    q: str = Query(..., description="Search query text", min_length=1),
    code: Optional[str] = Query(
        None,
        description="Optional legal code identifier to filter search (e.g., 'bgb', 'stgb'). If not provided, searches all codes.",
    ),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    cutoff: float = Query(
        0.7,
        description="Maximum cosine distance threshold (0-2, lower is more similar). Only return results with distance <= cutoff.",
        ge=0.0,
        le=2.0,
    ),
    repository: LegalTextRepository = Depends(get_legal_text_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service_dependency),
):
    """
    Perform semantic search on legal texts using embeddings

    This endpoint performs a semantic similarity search to find legal texts
    that are most similar in meaning to the provided query text.

    The search:
    1. Generates an embedding for the query text using Ollama
    2. Optionally filters texts by the specified legal code (if provided)
    3. Finds the most similar texts using cosine distance
    4. Filters out results above the cutoff threshold
    5. Returns results sorted by similarity (most similar first)

    **How similarity scores work:**
    - Cosine distance ranges from 0 to 2
    - 0 = identical vectors (most similar)
    - Lower values = more similar
    - Higher values = less similar
    - The cutoff parameter filters out results with distance > cutoff

    **Recommended cutoff values:**
    - 0.3-0.5: Very strict, only highly similar results
    - 0.6-0.7: Good balance (default: 0.7)
    - 0.8-1.0: More permissive, includes somewhat related results

    Examples:
    - `/legal-texts/search?q=Vertragsrecht` - Search for contract law across all codes
    - `/legal-texts/search?q=Vertragsrecht&code=bgb` - Search for contract law in BGB only
    - `/legal-texts/search?q=Diebstahl&limit=5` - Find 5 most relevant theft-related texts
    - `/legal-texts/search?q=Eigentum&cutoff=0.5` - Strict search for property-related texts

    Args:
        q: The search query text (required, minimum 1 character)
        code: Optional legal code identifier to filter by (e.g., 'bgb', 'stgb')
        limit: Maximum number of results to return (1-100, default: 10)
        cutoff: Maximum cosine distance threshold (0-2, default: 0.7)
        repository: Database repository (injected)
        embedding_service: Embedding service (injected)

    Returns:
        Search results with similarity scores (empty array if no results match the cutoff threshold)

    Raises:
        HTTPException:
            - 400: If query is invalid or code format is invalid
            - 500: If embedding generation or search fails
    """
    try:
        # Security: Validate code format if provided
        validated_code: Optional[str] = None
        if code is not None:
            validated_code = validate_legal_code(code)

        logger.info(
            f"Global semantic search - code: {validated_code}, query: '{q}', limit: {limit}, cutoff: {cutoff}"
        )

        # Step 1: Generate embedding for the search query
        try:
            query_embeddings = await embedding_service.generate_embeddings([q])
            query_embedding = query_embeddings[0]
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating query embedding: {str(e)}. Make sure Ollama is running.",
            )

        logger.info(f"Generated query embedding with dimension {len(query_embedding)}")

        # Step 2: Perform semantic search with optional code filter
        search_results = await repository.semantic_search(
            query_embedding=query_embedding,
            code=validated_code,
            limit=limit,
            cutoff=cutoff,
        )

        # Step 3: Convert to response models
        results: List[LegalTextSearchResult] = []
        for legal_text, distance in search_results:
            result = LegalTextSearchResult(
                text=str(legal_text.text),
                code=str(legal_text.code),
                section=str(legal_text.section),
                sub_section=str(legal_text.sub_section),
                similarity_score=float(distance),
            )
            results.append(result)

        code_info = f"code {validated_code}" if validated_code else "all codes"
        logger.info(f"Found {len(results)} results for query '{q}' in {code_info}")

        return LegalTextSearchResponse(
            query=q,
            code=validated_code,
            count=len(results),
            results=results,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"Error performing semantic search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error performing semantic search: {str(e)}"
        )


@router.get(
    "/gesetze-im-internet/{code}/search", response_model=LegalTextSearchResponse
)
async def semantic_search_legal_texts(
    code: str,
    q: str = Query(..., description="Search query text", min_length=1),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    cutoff: float = Query(
        0.7,
        description="Maximum cosine distance threshold (0-2, lower is more similar). Only return results with distance <= cutoff.",
        ge=0.0,
        le=2.0,
    ),
    repository: LegalTextRepository = Depends(get_legal_text_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service_dependency),
):
    """
    Perform semantic search on legal texts using embeddings (code-specific)

    This endpoint performs a semantic similarity search to find legal texts
    that are most similar in meaning to the provided query text, filtered by
    a specific legal code.

    Note: For searching across all codes, use /legal-texts/search instead.

    The search:
    1. Generates an embedding for the query text using Ollama
    2. Filters texts by the specified legal code
    3. Finds the most similar texts using cosine distance
    4. Filters out results above the cutoff threshold
    5. Returns results sorted by similarity (most similar first)

    **How similarity scores work:**
    - Cosine distance ranges from 0 to 2
    - 0 = identical vectors (most similar)
    - Lower values = more similar
    - Higher values = less similar
    - The cutoff parameter filters out results with distance > cutoff

    **Recommended cutoff values:**
    - 0.3-0.5: Very strict, only highly similar results
    - 0.6-0.7: Good balance (default: 0.7)
    - 0.8-1.0: More permissive, includes somewhat related results

    Examples:
    - `/legal-texts/gesetze-im-internet/bgb/search?q=Vertragsrecht` - Search for contract law in BGB (default cutoff: 0.7)
    - `/legal-texts/gesetze-im-internet/stgb/search?q=Diebstahl&limit=5` - Find 5 most relevant theft-related texts
    - `/legal-texts/gesetze-im-internet/bgb/search?q=Eigentum&cutoff=0.5` - Strict search for property-related texts

    Args:
        code: The legal code identifier (e.g., 'bgb', 'stgb')
        q: The search query text (required, minimum 1 character)
        limit: Maximum number of results to return (1-100, default: 10)
        cutoff: Maximum cosine distance threshold (0-2, default: 0.7)
        repository: Database repository (injected)
        embedding_service: Embedding service (injected)

    Returns:
        Search results with similarity scores (empty array if no results match the cutoff threshold)

    Raises:
        HTTPException:
            - 400: If query is invalid
            - 500: If embedding generation or search fails
    """
    try:
        # Security: Validate code format to prevent SSRF/injection attacks
        code = validate_legal_code(code)
        logger.info(
            f"Semantic search - code: {code}, query: '{q}', limit: {limit}, cutoff: {cutoff}"
        )

        # Step 1: Generate embedding for the search query
        try:
            query_embeddings = await embedding_service.generate_embeddings([q])
            query_embedding = query_embeddings[0]
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating query embedding: {str(e)}. Make sure Ollama is running.",
            )

        logger.info(f"Generated query embedding with dimension {len(query_embedding)}")

        # Step 2: Perform semantic search with cutoff
        search_results = await repository.semantic_search(
            query_embedding=query_embedding,
            code=code,
            limit=limit,
            cutoff=cutoff,
        )

        # Step 3: Convert to response models
        results: List[LegalTextSearchResult] = []
        for legal_text, distance in search_results:
            result = LegalTextSearchResult(
                text=str(legal_text.text),
                code=str(legal_text.code),
                section=str(legal_text.section),
                sub_section=str(legal_text.sub_section),
                similarity_score=float(distance),
            )
            results.append(result)

        logger.info(f"Found {len(results)} results for query '{q}' in code {code}")

        return LegalTextSearchResponse(
            query=q,
            code=code,
            count=len(results),
            results=results,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"Error performing semantic search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error performing semantic search: {str(e)}"
        )

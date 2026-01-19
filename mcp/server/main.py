"""
ABOUTME: Legal MCP Server providing tools for querying German legal texts
ABOUTME: Integrates with the legal-mcp store API via HTTP transport

A FastMCP server providing tools for querying German legal texts.
This server integrates with the legal-mcp store API to provide
semantic search and retrieval capabilities for legal documents.
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="Legal MCP Server",
    include_fastmcp_meta=True,
)

# Configuration for the legal texts API
API_BASE_URL = os.getenv("LEGAL_API_BASE_URL", "http://legal-mcp-store-api:8000")


class LegalTextResult(BaseModel):
    """Result from legal text query"""
    text: str
    code: str
    section: str
    sub_section: str
    similarity_score: Optional[float] = None


@mcp.tool()
async def search_legal_texts(
    query: str = Field(description="The search query text"),
    code: Optional[str] = Field(
        default=None,
        description="Optional legal code identifier (e.g., 'bgb', 'stgb'). If not provided, searches all codes."
    ),
    limit: int = Field(default=5, description="Maximum number of results", ge=1, le=20),
    cutoff: float = Field(
        default=0.7,
        description="Similarity threshold (0-2, lower is more similar)",
        ge=0.0,
        le=2.0,
    ),
) -> List[LegalTextResult]:
    """
    Perform semantic search on German legal texts.
    
    Searches through legal codes using semantic similarity to find relevant
    sections based on the query text. Lower similarity scores indicate better matches.
    
    If no code is provided, searches across all available legal codes in the database.
    
    Args:
        query: Natural language search query
        code: Optional legal code to search (bgb=Civil Code, stgb=Criminal Code). 
              If not provided, searches all codes.
        limit: Maximum number of results to return (1-20)
        cutoff: Maximum similarity distance threshold (0-2)
    
    Returns:
        List of matching legal text sections with similarity scores
    """
    try:
        async with httpx.AsyncClient() as client:
            # Build params - always include query, limit, cutoff
            params = {
                "q": query,
                "limit": limit,
                "cutoff": cutoff,
            }
            
            # Add code to params if provided (for the global search endpoint)
            if code is not None:
                params["code"] = code
            
            # Use the global search endpoint which accepts optional code parameter
            response = await client.get(
                f"{API_BASE_URL}/legal-texts/search",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                LegalTextResult(
                    text=result["text"],
                    code=result["code"],
                    section=result["section"],
                    sub_section=result["sub_section"],
                    similarity_score=result.get("similarity_score"),
                )
                for result in data.get("results", [])
            ]
    except httpx.HTTPError as e:
        logger.error(f"HTTP error searching legal texts: {e}")
        raise RuntimeError(f"Failed to search legal texts: {str(e)}")
    except Exception as e:
        logger.error(f"Error searching legal texts: {e}")
        raise RuntimeError(f"Error searching legal texts: {str(e)}")


@mcp.tool()
async def get_legal_section(
    code: str = Field(description="Legal code identifier (e.g., 'bgb', 'stgb')"),
    section: str = Field(description="Section identifier (e.g., '§ 1', 'Art 1')"),
    sub_section: Optional[str] = Field(
        default=None,
        description="Optional sub-section identifier (e.g., '1', '2a')",
    ),
) -> List[LegalTextResult]:
    """
    Retrieve specific legal text sections by code and section number.
    
    Gets the exact text of a specific legal section or sub-section from
    German legal codes.
    
    Args:
        code: Legal code identifier (bgb, stgb, etc.)
        section: Section identifier (e.g., '§ 1')
        sub_section: Optional sub-section identifier
    
    Returns:
        List of legal text sections matching the criteria
    """
    try:
        async with httpx.AsyncClient() as client:
            params = {"section": section}
            if sub_section:
                params["sub_section"] = sub_section
            
            response = await client.get(
                f"{API_BASE_URL}/legal-texts/gesetze-im-internet/{code}",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                LegalTextResult(
                    text=result["text"],
                    code=result["code"],
                    section=result["section"],
                    sub_section=result["sub_section"],
                )
                for result in data.get("results", [])
            ]
    except httpx.HTTPError as e:
        logger.error(f"HTTP error getting legal section: {e}")
        raise RuntimeError(f"Failed to get legal section: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting legal section: {e}")
        raise RuntimeError(f"Error getting legal section: {str(e)}")


@mcp.tool()
async def get_available_codes() -> List[str]:
    """
    Get all available legal codes in the database.

    Returns a list of legal code identifiers that have been imported
    and are available for querying and searching.

    Returns:
        List of available legal code identifiers (e.g., ['bgb', 'stgb', 'gg'])
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/legal-texts/gesetze-im-internet/codes",
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            return data.get("codes", [])
    except httpx.HTTPError as e:
        logger.error(f"HTTP error getting available codes: {e}")
        raise RuntimeError(f"Failed to get available codes: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting available codes: {e}")
        raise RuntimeError(f"Error getting available codes: {str(e)}")


# For running with the FastMCP CLI or directly
if __name__ == "__main__":
    # Run with HTTP transport for network accessibility
    mcp.run(transport="http", host="0.0.0.0", port=8001)


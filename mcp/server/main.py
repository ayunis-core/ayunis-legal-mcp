"""
Legal MCP Server

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
API_BASE_URL = os.getenv("LEGAL_API_BASE_URL", "http://localhost:8000")


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
    code: str = Field(description="Legal code identifier (e.g., 'bgb', 'stgb')"),
    limit: int = Field(default=5, description="Maximum number of results", ge=1, le=20),
    cutoff: float = Field(
        default=0.5,
        description="Similarity threshold (0-2, lower is more similar)",
        ge=0.0,
        le=2.0,
    ),
) -> List[LegalTextResult]:
    """
    Perform semantic search on German legal texts.
    
    Searches through legal codes using semantic similarity to find relevant
    sections based on the query text. Lower similarity scores indicate better matches.
    
    Args:
        query: Natural language search query
        code: Legal code to search (bgb=Civil Code, stgb=Criminal Code)
        limit: Maximum number of results to return (1-20)
        cutoff: Maximum similarity distance threshold (0-2)
    
    Returns:
        List of matching legal text sections with similarity scores
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/legal-texts/gesetze-im-internet/{code}/search",
                params={
                    "q": query,
                    "limit": limit,
                    "cutoff": cutoff,
                },
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
async def import_legal_code(
    code: str = Field(description="Legal code identifier to import (e.g., 'bgb', 'stgb')"),
) -> str:
    """
    Import a German legal code from Gesetze im Internet.
    
    Downloads and imports a complete legal code into the database,
    including generating embeddings for semantic search. This may
    take several minutes for large codes.
    
    Args:
        code: Legal code identifier (bgb=Civil Code, stgb=Criminal Code)
    
    Returns:
        Success message with import statistics
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/legal-texts/gesetze-im-internet/{code}",
                timeout=300.0,  # 5 minutes for large imports
            )
            response.raise_for_status()
            data = response.json()
            
            return f"✓ {data['message']}\nImported {data['texts_imported']} legal texts for code '{data['code']}'"
    except httpx.HTTPError as e:
        logger.error(f"HTTP error importing legal code: {e}")
        raise RuntimeError(f"Failed to import legal code: {str(e)}")
    except Exception as e:
        logger.error(f"Error importing legal code: {e}")
        raise RuntimeError(f"Error importing legal code: {str(e)}")


@mcp.resource("legal://codes/available")
def list_available_codes() -> str:
    """
    List available German legal codes that can be queried.
    
    Returns:
        Formatted list of available legal codes with descriptions
    """
    codes = {
        "bgb": "Bürgerliches Gesetzbuch (German Civil Code)",
        "stgb": "Strafgesetzbuch (German Criminal Code)",
        "gg": "Grundgesetz (German Constitution)",
        "hgb": "Handelsgesetzbuch (German Commercial Code)",
        "zpo": "Zivilprozessordnung (Code of Civil Procedure)",
        "stpo": "Strafprozessordnung (Code of Criminal Procedure)",
    }
    
    result = "Available German Legal Codes:\n\n"
    for code, description in codes.items():
        result += f"• {code.upper()}: {description}\n"
    
    return result


@mcp.resource("legal://server/info")
def server_info() -> str:
    """
    Get information about the Legal MCP server.
    
    Returns:
        Server information and usage instructions
    """
    return """
Legal MCP Server

This server provides tools for querying and analyzing German legal texts
from the Gesetze im Internet database.

Tools:
• search_legal_texts: Semantic search across legal codes
• get_legal_section: Retrieve specific legal sections
• import_legal_code: Import legal codes into the database

Resources:
• legal://codes/available: List of available legal codes
• legal://server/info: This information

To get started, use import_legal_code to load a legal code (e.g., 'bgb'),
then use search_legal_texts or get_legal_section to query it.

API Base URL: {API_BASE_URL}
"""


# For running with the FastMCP CLI or directly
if __name__ == "__main__":
    # Run with stdio transport (default for MCP)
    # You can also use: mcp.run(transport="http", port=8001)
    mcp.run()


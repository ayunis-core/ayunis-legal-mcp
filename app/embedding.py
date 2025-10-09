"""
Embedding service for generating text embeddings using Ollama
"""

import logging
from typing import List, Optional, Sequence
from ollama import AsyncClient, ResponseError
from app.config import Settings

logger = logging.getLogger(__name__)

MODEL = "ryanshillington/Qwen3-Embedding-4B:latest"
EMBEDDING_DIMENSION = 2560
TIMEOUT = 30  # Request timeout in seconds


class EmbeddingService:
    """
    Service for generating text embeddings using Ollama SDK
    """

    def __init__(self, settings: Settings):
        """
        Initialize the embedding service

        Args:
            settings: Application settings containing Ollama configuration
        """
        self.model = MODEL

        if settings.ollama_auth_token and settings.ollama_auth_token != "":
            self.client = AsyncClient(
                host=settings.ollama_base_url,
                timeout=TIMEOUT,
                headers={"Authorization": f"Bearer {settings.ollama_auth_token}"},
            )
        else:
            self.client = AsyncClient(host=settings.ollama_base_url, timeout=TIMEOUT)

    async def generate_embeddings(self, texts: List[str]) -> Sequence[Sequence[float]]:
        """
        Generate embedding vectors for the given texts

        Args:
            texts: List of input texts to generate embeddings for

        Returns:
            A list of embedding vectors (one per input text)

        Raises:
            ResponseError: If the request to Ollama fails
            ValueError: If the response is invalid or texts list is empty
        """
        if not texts or len(texts) == 0:
            raise ValueError("Texts list cannot be empty")

        try:
            response = await self.client.embed(
                model=self.model,
                input=texts,
            )
            embeddings = response.embeddings
            return embeddings

        except ResponseError as e:
            logger.error(f"Ollama ResponseError: {e.error}")
            if e.status_code == 404:
                logger.error(
                    f"Model '{self.model}' not found. Please pull the model first: ollama pull {self.model}"
                )
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {str(e)}")
            raise


def get_embedding_service(settings: Optional[Settings] = None) -> EmbeddingService:
    """
    Get an instance of the embedding service

    Args:
        settings: Optional settings instance. If not provided, will use default settings

    Returns:
        An instance of EmbeddingService
    """
    if settings is None:
        from app.config import get_settings

        settings = get_settings()

    return EmbeddingService(settings)

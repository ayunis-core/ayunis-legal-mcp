"""Tests for application configuration"""

import pytest
from unittest.mock import patch


class TestOllamaEmbeddingModelConfig:
    """Tests for OLLAMA_EMBEDDING_MODEL configuration"""

    def test_default_embedding_model(self):
        """Test that default embedding model is set correctly"""
        from app.config import Settings

        settings = Settings()
        assert settings.ollama_embedding_model == "ryanshillington/Qwen3-Embedding-4B:latest"

    def test_embedding_model_from_env(self):
        """Test that OLLAMA_EMBEDDING_MODEL env var is respected"""
        with patch.dict(
            "os.environ",
            {"OLLAMA_EMBEDDING_MODEL": "custom/model:v1"},
            clear=False,
        ):
            from app.config import Settings

            settings = Settings()
            assert settings.ollama_embedding_model == "custom/model:v1"

    def test_embedding_service_uses_configured_model(self):
        """Test that EmbeddingService uses the model from settings"""
        from app.config import Settings
        from app.embedding import EmbeddingService

        with patch.dict(
            "os.environ",
            {"OLLAMA_EMBEDDING_MODEL": "test/embedding-model:latest"},
            clear=False,
        ):
            settings = Settings()
            service = EmbeddingService(settings)
            assert service.model == "test/embedding-model:latest"

"""
Application configuration using Pydantic Settings
"""

from functools import lru_cache
from pydantic import Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Application settings
    app_name: str = "Legal MCP API"
    admin_email: EmailStr = "admin@example.com"
    items_per_user: int = Field(default=50, gt=0, lt=1000)
    debug: bool = False

    # Database settings
    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="legal_mcp")
    postgres_password: str = Field(default="legal_mcp_password")
    postgres_db: str = Field(default="legal_mcp_db")

    # Ollama settings
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Base URL for Ollama service"
    )
    ollama_auth_token: str = Field(
        default="", description="Ollama authentication token"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance
    Using lru_cache to avoid reading .env file on every request
    """
    return Settings()

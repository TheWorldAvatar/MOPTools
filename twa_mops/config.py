"""Centralized configuration for MOPTools.

This module provides centralized configuration management using Pydantic.
All configuration settings are loaded from environment variables or
use default values.

Usage:
    from config import settings, get_kg_client
    
    # Access settings
    print(settings.sparql_endpoint)
    
    # Get a configured KG client
    kg_client = get_kg_client()
"""

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings for MOPTools.
    
    Attributes:
        sparql_endpoint: The SPARQL endpoint URL for KG queries
        data_dir: Directory for storing local data files
        default_recursion: Default recursion depth for KG queries
        kg_username: Optional username for KG authentication
        kg_password: Optional password for KG authentication
        fs_url: File server URL for geometry files
        fs_username: File server username
        fs_password: File server password
        timeout: Default timeout in seconds for network requests
        max_retries: Maximum number of retry attempts for failed requests
        retry_delay: Initial delay between retries in seconds
    """
    
    # SPARQL endpoint configuration
    sparql_endpoint: str = "http://localhost:3838/blazegraph/namespace/ontomops/sparql"
    
    # Data directory - single consistent location
    # Relative to current working directory. Recommended: twa_mops/data/
    data_dir: str = "data"
    
    # Default recursion depth for KG queries
    default_recursion: int = -1
    
    # KG authentication (optional)
    kg_username: str = ""
    kg_password: str = ""
    
    # File server configuration (optional)
    fs_url: str = ""
    fs_username: str = ""
    fs_password: str = ""
    
    # Network configuration
    timeout: int = 30  # Default timeout in seconds for network requests
    max_retries: int = 3  # Maximum number of retry attempts for failed requests
    retry_delay: float = 1.0  # Initial delay between retries in seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_kg_client():
    """Get a configured KnowledgeGraphClient instance.
    
    Returns:
        KnowledgeGraphClient: Configured client instance
    
    Example:
        >>> from config import get_kg_client
        >>> kg_client = get_kg_client()
        >>> results = kg_client.pull_objects(['http://example.com/iri'])
    """
    from twa_mops.kg.client import KnowledgeGraphClient
    
    return KnowledgeGraphClient(
        endpoint=settings.sparql_endpoint,
        max_cache_size=128,
        username=settings.kg_username if settings.kg_username else None,
        password=settings.kg_password if settings.kg_password else None,
        fs_url=settings.fs_url if settings.fs_url else None,
        fs_username=settings.fs_username if settings.fs_username else None,
        fs_password=settings.fs_password if settings.fs_password else None,
        timeout=settings.timeout,
        max_retries=settings.max_retries,
        retry_delay=settings.retry_delay,
    )

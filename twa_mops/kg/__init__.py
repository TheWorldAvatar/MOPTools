"""Knowledge Graph interaction module."""

from .client import KnowledgeGraphClient
from .compatibility import PySparqlClientCompatibility, create_compatible_sparql_client

__all__ = [
    'KnowledgeGraphClient',
    'PySparqlClientCompatibility',
    'create_compatible_sparql_client',
]

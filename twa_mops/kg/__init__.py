"""Knowledge Graph interaction module."""

from .client import (
    KnowledgeGraphClient,
    KnowledgeGraphError,
    QueryError,
    ObjectNotFoundError,
    InvalidObjectError,
)
from .compatibility import PySparqlClientCompatibility, create_compatible_sparql_client

__all__ = [
    'KnowledgeGraphClient',
    'KnowledgeGraphError',
    'QueryError',
    'ObjectNotFoundError',
    'InvalidObjectError',
    'PySparqlClientCompatibility',
    'create_compatible_sparql_client',
]

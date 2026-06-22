"""Compatibility layer for PySparqlClient.

This module provides a wrapper that makes KnowledgeGraphClient compatible
with existing code that expects PySparqlClient interface.
"""

from .client import KnowledgeGraphClient


class PySparqlClientCompatibility(KnowledgeGraphClient):
    """KnowledgeGraphClient with PySparqlClient-compatible interface.
    
    This class extends KnowledgeGraphClient to provide the same interface
    as PySparqlClient, allowing existing code to work without modifications.
    
    Usage:
        # Instead of:
        from twa.kg_operations import PySparqlClient
        sparql_client = PySparqlClient(endpoint, endpoint)
        
        # You can use:
        from kg.compatibility import PySparqlClientCompatibility
        sparql_client = PySparqlClientCompatibility(endpoint)
        
        # Existing code like ontomops.ChemicalBuildingUnit.pull_from_kg() will work
    """
    
    def __init__(
        self,
        query_endpoint: str,
        update_endpoint: str,
        kg_user: str = None,
        kg_password: str = None,
        fs_url: str = None,
        fs_user: str = None,
        fs_pwd: str = None,
    ):
        """Initialize with PySparqlClient-compatible parameters.
        
        Args:
            query_endpoint: SPARQL query endpoint URL
            update_endpoint: SPARQL update endpoint URL
            kg_user: Knowledge graph username
            kg_password: Knowledge graph password
            fs_url: File server URL
            fs_user: File server username
            fs_pwd: File server password
        """
        # Map PySparqlClient parameters to KnowledgeGraphClient parameters
        super().__init__(
            endpoint=query_endpoint,
            max_cache_size=128,
            username=kg_user,
            password=kg_password,
            fs_url=fs_url,
            fs_username=fs_user,
            fs_password=fs_pwd,
        )
    
    def upload_graph(self, graph):
        """Upload RDF graph (alias for compatibility)."""
        return self.sparql_client.upload_graph(graph)


# Factory function for easy creation
def create_compatible_sparql_client(
    query_endpoint: str,
    update_endpoint: str,
    kg_user: str = None,
    kg_password: str = None,
    fs_url: str = None,
    fs_user: str = None,
    fs_pwd: str = None,
):
    """Create a KnowledgeGraphClient that's compatible with PySparqlClient.
    
    Returns:
        PySparqlClientCompatibility: A client compatible with PySparqlClient
    """
    return PySparqlClientCompatibility(
        query_endpoint=query_endpoint,
        update_endpoint=update_endpoint,
        kg_user=kg_user,
        kg_password=kg_password,
        fs_url=fs_url,
        fs_user=fs_user,
        fs_pwd=fs_pwd,
    )

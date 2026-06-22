"""Knowledge Graph Client for MOPTools.

This module provides the KnowledgeGraphClient class for interacting with
the Knowledge Graph using SPARQL queries with batching and caching support.
"""

from functools import lru_cache
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel

try:
    from twa.kg_operations import PySparqlClient
except ImportError:
    PySparqlClient = None


class KnowledgeGraphClient:
    """Client for interacting with the Knowledge Graph.
    
    Provides methods for pulling and pushing objects to/from the KG using
    batched SPARQL queries with caching support.
    
    Args:
        endpoint: The SPARQL endpoint URL
        max_cache_size: Maximum number of objects to cache (default: 128)
        username: Optional username for authenticated endpoints
        password: Optional password for authenticated endpoints
        fs_url: Optional file server URL for geometry files
        fs_username: Optional file server username
        fs_password: Optional file server password
    """
    
    def __init__(
        self,
        endpoint: str,
        max_cache_size: int = 128,
        username: Optional[str] = None,
        password: Optional[str] = None,
        fs_url: Optional[str] = None,
        fs_username: Optional[str] = None,
        fs_password: Optional[str] = None,
    ):
        """Initialize the KnowledgeGraphClient.
        
        Args:
            endpoint: The SPARQL endpoint URL
            max_cache_size: Maximum number of objects to cache (default: 128)
            username: Optional username for authenticated endpoints
            password: Optional password for authenticated endpoints
            fs_url: Optional file server URL for geometry files
            fs_username: Optional file server username
            fs_password: Optional file server password
        """
        if PySparqlClient is None:
            raise ImportError(
                "twa.kg_operations.PySparqlClient is required. "
                "Please install the twa package."
            )
        
        self.endpoint = endpoint
        self.max_cache_size = max_cache_size
        self.username = username
        self.password = password
        self.fs_url = fs_url
        self.fs_username = fs_username
        self.fs_password = fs_password
        
        # Initialize the SPARQL client
        self.sparql_client = PySparqlClient(
            query_endpoint=endpoint,
            update_endpoint=endpoint,
            kg_user=username,
            kg_password=password,
            fs_url=fs_url,
            fs_user=fs_username,
            fs_pwd=fs_password,
        )
    
    def pull_objects(
        self,
        iris: List[str],
        depth: int = -1,
    ) -> List[Dict[str, Any]]:
        """Pull objects from KG using batched SPARQL query.
        
        Args:
            iris: List of IRIs to pull from the KG
            depth: Recursion depth for property traversal (-1 = infinite, 0 = no recursion)
        
        Returns:
            List of dictionaries containing the pulled object data
        """
        if not iris:
            return []
        
        # Convert to tuple for caching
        iris_tuple = tuple(sorted(iris))
        
        # Use cached internal method
        return self._pull_objects_cached(iris_tuple, depth)
    
    @lru_cache(maxsize=128)
    def _pull_objects_cached(
        self,
        iris: tuple,
        depth: int = -1,
    ) -> List[Dict[str, Any]]:
        """Internal cached method for pulling objects."""
        # Create batched query with UNION for multiple IRIs
        iris_str = " ".join(f"<{iri}>" for iri in iris)
        
        # For now, use simple query; depth handling would require more complex SPARQL
        query = f"""
        SELECT ?s ?p ?o WHERE {{
          VALUES ?s {{ {iris_str} }}
          ?s ?p ?o .
        }}
        """
        
        results = self.sparql_client.perform_query(query)
        return [dict(row) for row in results]
    
    def pull_single_object(
        self,
        iri: str,
        depth: int = -1,
    ) -> List[Dict[str, Any]]:
        """Pull a single object from KG by IRI.
        
        Args:
            iri: The IRI of the object to pull
            depth: Recursion depth for property traversal
        
        Returns:
            List of dictionaries containing the pulled object data
        """
        return self.pull_objects([iri], depth=depth)
    
    def push_objects(
        self,
        objects: List[Any],
        depth: int = -1,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Any]:
        """Push objects to KG with provenance tracking.
        
        This method delegates to the underlying PySparqlClient for pushing
        RDF graphs to the Knowledge Graph.
        
        Args:
            objects: List of objects to push to the KG (typically BaseClass instances)
            depth: Recursion depth for collecting related objects (-1 = infinite)
            provenance: Optional provenance information to include
        
        Returns:
            Tuple of (graph_to_remove, graph_to_add) - the RDF graphs that were
            removed and added during the push operation
        
        Raises:
            ValueError: If objects list is empty
            Exception: If push operation fails
        """
        if not objects:
            raise ValueError("No objects to push")
        
        from rdflib import Graph
        
        # Collect all triples from all objects
        g_to_remove = Graph()
        g_to_add = Graph()
        
        for obj in objects:
            # Check if object has _collect_diff_to_graph method (from BaseClass)
            if hasattr(obj, '_collect_diff_to_graph'):
                obj_g_to_remove, obj_g_to_add = obj._collect_diff_to_graph(
                    g_to_remove, g_to_add, depth
                )
                g_to_remove += obj_g_to_remove
                g_to_add += obj_g_to_add
            else:
                # For Pydantic models, we need to serialize them to RDF first
                # This is a placeholder for future implementation
                raise NotImplementedError(
                    f"Pushing Pydantic models is not yet implemented. "
                    f"Object type: {type(obj)}"
                )
        
        # Add provenance if provided
        if provenance:
            # TODO: Add provenance triples to g_to_add
            pass
        
        # Perform the actual push using the underlying SPARQL client
        result = self.sparql_client.delete_and_insert_graphs(g_to_remove, g_to_add)
        
        return g_to_remove, g_to_add
    
    def push_single_object(
        self,
        obj: Any,
        depth: int = -1,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Any]:
        """Push a single object to KG.
        
        Convenience method for pushing a single object.
        
        Args:
            obj: The object to push
            depth: Recursion depth for collecting related objects
            provenance: Optional provenance information
        
        Returns:
            Tuple of (graph_to_remove, graph_to_add)
        """
        return self.push_objects([obj], depth=depth, provenance=provenance)
    
    def clear_cache(self):
        """Clear the LRU cache for pull operations."""
        self._pull_objects_cached.cache_clear()
    
    def execute_query(
        self,
        query: str,
    ) -> Any:
        """Execute a raw SPARQL query.
        
        Args:
            query: The SPARQL query string to execute
        
        Returns:
            The query results
        """
        return self.sparql_client.perform_query(query)
    
    def upload_graph(
        self,
        graph,
    ) -> bool:
        """Upload an RDF graph to the KG.
        
        Args:
            graph: The RDF graph to upload
        
        Returns:
            True if upload was successful
        """
        return self.sparql_client.upload_graph(graph)
    
    def download_file(
        self,
        remote_path: str,
        local_path: str,
    ) -> bool:
        """Download a file from the KG file server.
        
        Args:
            remote_path: The remote file path
            local_path: The local destination path
        
        Returns:
            True if download was successful
        """
        return self.sparql_client.download_file(remote_path, local_path)
    
    def upload_file(
        self,
        local_path: str,
    ) -> tuple:
        """Upload a file to the KG file server.
        
        Args:
            local_path: The local file path to upload
        
        Returns:
            Tuple of (remote_path, timestamp)
        """
        return self.sparql_client.upload_file(local_path)
    
    def perform_query(self, query: str) -> Any:
        """Alias for execute_query to match PySparqlClient interface.
        
        Args:
            query: The SPARQL query string to execute
        
        Returns:
            The query results
        """
        return self.execute_query(query)
    
    def delete_and_insert_graphs(self, g_to_remove: Any, g_to_add: Any) -> Any:
        """Alias for the underlying SPARQL client method.
        
        Args:
            g_to_remove: RDF graph of triples to remove
            g_to_add: RDF graph of triples to add
        
        Returns:
            The result from the SPARQL client
        """
        return self.sparql_client.delete_and_insert_graphs(g_to_remove, g_to_add)

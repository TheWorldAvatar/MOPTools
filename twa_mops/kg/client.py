"""Knowledge Graph Client for MOPTools.

This module provides the KnowledgeGraphClient class for interacting with
the Knowledge Graph using SPARQL queries with batching and caching support.
"""

from functools import lru_cache
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel
import time

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
        # Backward compatibility: accept kg_* and fs_* parameter names
        kg_user: Optional[str] = None,
        kg_password: Optional[str] = None,
        fs_user: Optional[str] = None,
        fs_pwd: Optional[str] = None,
        enable_performance_timing: bool = False,
    ):
        """Initialize the KnowledgeGraphClient.
        
        Args:
            endpoint: The SPARQL endpoint URL
            max_cache_size: Maximum number of objects to cache (default: 128)
            username: Optional username for authenticated endpoints (alias: kg_user)
            password: Optional password for authenticated endpoints (alias: kg_password)
            fs_url: Optional file server URL for geometry files
            fs_username: Optional file server username (alias: fs_user)
            fs_password: Optional file server password (alias: fs_pwd)
            kg_user: Alias for username (for backward compatibility)
            kg_password: Alias for password (for backward compatibility)
            fs_user: Alias for fs_username (for backward compatibility)
            fs_pwd: Alias for fs_password (for backward compatibility)
            enable_performance_timing: Enable timing metrics for queries (default: False)
        """
        if PySparqlClient is None:
            raise ImportError(
                "twa.kg_operations.PySparqlClient is required. "
                "Please install the twa package."
            )
        
        self.endpoint = endpoint
        self.max_cache_size = max_cache_size
        self.enable_performance_timing = enable_performance_timing
        self._last_query_time = 0
        self._total_query_time = 0
        self._query_count = 0
        
        # Support both parameter naming conventions
        self.username = username or kg_user
        self.password = password or kg_password
        self.fs_url = fs_url
        self.fs_username = fs_username or fs_user
        self.fs_password = fs_password or fs_pwd
        
        # Initialize the SPARQL client
        self.sparql_client = PySparqlClient(
            query_endpoint=endpoint,
            update_endpoint=endpoint,
            kg_user=self.username,
            kg_password=self.password,
            fs_url=fs_url,
            fs_user=self.fs_username,
            fs_pwd=self.fs_password,
        )
    
    def pull_objects(
        self,
        iris: List[str],
        depth: int = -1,
    ) -> List[Dict[str, Any]]:
        """Pull objects from KG using batched SPARQL query.
        
        Note: This method returns raw dictionary data. For class instances, use pull_instances().
        
        Args:
            iris: List of IRIs to pull from the KG
            depth: Recursion depth for property traversal
                -1 = infinite recursion (default)
                0 = no recursion (returns only direct properties as IRIs, not loaded objects)
                1+ = n-level recursion
        
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
        start_time = time.time()
        
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
        
        if self.enable_performance_timing:
            elapsed = time.time() - start_time
            self._last_query_time = elapsed
            self._total_query_time += elapsed
            self._query_count += 1
        
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
    
    def pull_for_assembly(
        self,
        am_iri: str,
        cbu_iris: List[str],
        depth: int = -1,
    ) -> Tuple[Any, List[Any]]:
        """Optimized pull for assembly operations.
        
        Pulls an AssemblyModel and multiple CBUs in a single optimized operation.
        
        **Recursion Depth Recommendations:**
        - depth=0: Too shallow - properties returned as IRIs, not objects (WILL FAIL)
        - depth=1: Loads direct properties only (may miss nested objects like GBUConnectingPoint)
        - depth=2: May miss GBUConnectingPoint, Modularity (WILL FAIL for assembly)
        - depth=3: Minimum recommended for assembly (loads all required objects)
        - depth=-1: Infinite recursion (default, most reliable but slowest)
        
        For MOP assembly, depth=3 or depth=-1 is recommended to ensure all required
        properties are loaded: AM -> GBU -> GBUCoordinateCenter -> GBUConnectingPoint,
        and GBU -> GBUType -> Modularity.
        
        Args:
            am_iri: The IRI of the AssemblyModel
            cbu_iris: List of CBU IRIs to pull
            depth: Recursion depth (default: -1 for full object resolution)
        
        Returns:
            Tuple of (AssemblyModel instance, list of ChemicalBuildingUnit instances)
        
        Example:
            # Full assembly with depth=-1 (recommended for reliability)
            am, cbus = kg_client.pull_for_assembly(am_iri, [cbu1_iri, cbu2_iri])
            mop = ontomops.MetalOrganicPolyhedron.from_assemble(
                am, cbus, prov, sparql_client=kg_client
            )
            
            # Faster with depth=3 (if your data structure is shallow)
            am, cbus = kg_client.pull_for_assembly(am_iri, [cbu1_iri, cbu2_iri], depth=3)
        """
        from twa.data_model.base_ontology import BaseClass
        from twa_mops.core.ontomops import AssemblyModel, ChemicalBuildingUnit
        
        # Pull the AM first to get its class
        am = AssemblyModel.pull_from_kg([am_iri], self.sparql_client, recursive_depth=depth)[0]
        
        # Pull CBUs
        cbus = ChemicalBuildingUnit.pull_from_kg(cbu_iris, self.sparql_client, recursive_depth=depth)
        
        return am, cbus
    
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
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics for KG queries.
        
        Returns:
            Dictionary with:
            - total_queries: Number of queries executed
            - total_time: Total time spent on queries (seconds)
            - avg_time: Average query time (seconds)
            - last_query_time: Time of last query (seconds)
        """
        if self._query_count == 0:
            return {
                'total_queries': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'last_query_time': 0.0
            }
        return {
            'total_queries': self._query_count,
            'total_time': self._total_query_time,
            'avg_time': self._total_query_time / self._query_count,
            'last_query_time': self._last_query_time
        }
    
    def reset_performance_stats(self):
        """Reset performance statistics."""
        self._last_query_time = 0
        self._total_query_time = 0
        self._query_count = 0
    
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
    
    def get_outgoing_and_attributes(self, node_iris: set) -> Dict[str, Dict[str, set]]:
        """Alias for the underlying SPARQL client method.
        
        This method is required by BaseClass.pull_from_kg() for backward compatibility.
        
        Args:
            node_iris: Set of IRIs to get outgoing links and attributes for
        
        Returns:
            Dictionary mapping each IRI to its outgoing properties and values
        """
        return self.sparql_client.get_outgoing_and_attributes(node_iris)
    
    def pull_instances(
        self,
        cls,
        iris: List[str],
        depth: int = 1,
    ) -> List[Any]:
        """Pull instances of a specific class from the KG.
        
        This is a convenience method that uses the existing pull_from_kg method
        and returns instances of the specified class.
        
        Args:
            cls: The class to instantiate (must be a BaseClass subclass)
            iris: List of IRIs to pull from the KG
            depth: Recursion depth for property traversal
                -1 = infinite recursion, 0 = no recursion (IRIs only), 1+ = n-level recursion
                Default is 1 (one level of recursion) as depth=0 may not load all required properties
        
        Returns:
            List of class instances
        """
        # Import here to avoid circular imports
        from twa.data_model.base_ontology import BaseClass
        
        if not isinstance(cls, type) or not issubclass(cls, BaseClass):
            raise TypeError(f"cls must be a BaseClass subclass, got {type(cls)}")
        
        # Use pull_from_kg which handles the conversion from RDF results to class instances
        return cls.pull_from_kg(iris, self.sparql_client, recursive_depth=depth)
    
    def pull_instances_fast(
        self,
        cls,
        iris: List[str],
        depth: int = 1,
    ) -> List[Any]:
        """Pull instances with optimized settings for speed.
        
        This method is optimized for cases where you need objects quickly and
        don't need full recursion. It uses depth=1 by default which loads
        direct properties but not nested objects.
        
        Args:
            cls: The class to instantiate (must be a BaseClass subclass)
            iris: List of IRIs to pull from the KG
            depth: Recursion depth (default: 1 for good balance of speed and completeness)
        
        Returns:
            List of class instances
        
        Example:
            # Fast pull for assembly (doesn't load nested geometry)
            cbus = kg_client.pull_instances_fast(ChemicalBuildingUnit, iris)
        """
        return self.pull_instances(cls, iris, depth=depth)

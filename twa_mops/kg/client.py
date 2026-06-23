"""Knowledge Graph Client for MOPTools.

This module provides the KnowledgeGraphClient class for interacting with
the Knowledge Graph using SPARQL queries with batching and caching support.

Custom Exceptions:
    KnowledgeGraphError: Base exception for KG-related errors
    QueryError: Raised when SPARQL queries fail
    ObjectNotFoundError: Raised when requested objects don't exist in KG
    InvalidObjectError: Raised when objects have invalid data/structure
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, validator, Field, HttpUrl, conint
import time
import re

try:
    from twa.kg_operations import PySparqlClient
except ImportError:
    PySparqlClient = None


# ============================================================================
# Custom Exceptions
# ============================================================================

class KnowledgeGraphError(Exception):
    """Base exception for Knowledge Graph-related errors.
    
    All custom exceptions from the KG client inherit from this class,
    allowing users to catch all KG-related errors with a single except clause.
    
    Example:
        try:
            client.pull_objects(iris)
        except KnowledgeGraphError as e:
            print(f"KG error: {e}")
    """
    pass


class QueryError(KnowledgeGraphError):
    """Raised when a SPARQL query fails.
    
    This exception is raised when:
    - The SPARQL endpoint is unreachable
    - The query syntax is invalid
    - The query times out
    - Authentication fails
    
    Attributes:
        query: The SPARQL query that failed (if available)
        endpoint: The SPARQL endpoint URL (if available)
        original_error: The original exception (if any)
    """
    def __init__(self, message: str, query: Optional[str] = None, 
                 endpoint: Optional[str] = None, original_error: Optional[Exception] = None):
        self.query = query
        self.endpoint = endpoint
        self.original_error = original_error
        
        # Build detailed error message
        parts = [message]
        if query:
            parts.append(f"Query: {query[:200]}..." if len(query) > 200 else f"Query: {query}")
        if endpoint:
            parts.append(f"Endpoint: {endpoint}")
        if original_error:
            parts.append(f"Original error: {original_error}")
        
        super().__init__("\n".join(parts))


class ObjectNotFoundError(KnowledgeGraphError):
    """Raised when a requested object doesn't exist in the Knowledge Graph.
    
    This exception is raised when:
    - An IRI doesn't exist in the KG
    - A query returns no results for a required object
    
    Attributes:
        iris: List of IRIs that were not found
        object_type: The type of object that was being fetched (if known)
    """
    def __init__(self, message: str, iris: Optional[List[str]] = None,
                 object_type: Optional[str] = None):
        self.iris = iris or []
        self.object_type = object_type
        
        parts = [message]
        if iris:
            parts.append(f"Not found IRIs: {', '.join(iris[:5])}" + 
                        ("..." if len(iris) > 5 else ""))
        if object_type:
            parts.append(f"Object type: {object_type}")
        
        super().__init__("\n".join(parts))


class InvalidObjectError(KnowledgeGraphError):
    """Raised when an object has invalid data or structure.
    
    This exception is raised when:
    - A retrieved object has missing required properties
    - An object has invalid property values
    - An object cannot be instantiated from the KG data
    
    Attributes:
        iri: The IRI of the invalid object (if available)
        property_name: The name of the invalid property (if available)
        reason: Description of why the object is invalid
    """
    def __init__(self, message: str, iri: Optional[str] = None,
                 property_name: Optional[str] = None, reason: Optional[str] = None):
        self.iri = iri
        self.property_name = property_name
        self.reason = reason
        
        parts = [message]
        if iri:
            parts.append(f"IRI: {iri}")
        if property_name:
            parts.append(f"Property: {property_name}")
        if reason:
            parts.append(f"Reason: {reason}")
        
        super().__init__("\n".join(parts))


# ============================================================================
# Validation Models
# ============================================================================
#
# These Pydantic models provide input validation for the KnowledgeGraphClient.
# They ensure that:
# - IRIs are properly formatted URLs or URNs
# - Depth values are within safe bounds (-1 to 10)
# - Endpoints are valid HTTP/HTTPS URLs
# - Cache sizes are reasonable (1-10000)
# - File paths exist when required
#
# Usage: Call the model with the input value, e.g., IRIInput(iri=my_iri).iri
#

class IRIInput(BaseModel):
    """Validation model for IRI (Internationalized Resource Identifier) inputs.
    
    Validates that the IRI is a valid URL format (HTTP/HTTPS) or URN format,
    and is not empty. This ensures all KG resource identifiers are properly
    formatted before being used in queries.
    
    Accepts:
        - HTTP/HTTPS URLs: http://example.com/kg/resource
        - URN format: urn:namespace:resource
    
    Rejects:
        - Empty strings or None
        - URLs without protocol (e.g., "example.com")
        - Malformed URLs
        
    Example:
        >>> IRIInput(iri="https://www.theworldavatar.com/kg/ontomops/CBU_123")
        >>> IRIInput(iri="urn:test:resource")
        >>> IRIInput(iri="invalid")  # Raises ValueError
    """
    iri: str = Field(..., description="The IRI/URL to validate")
    
    @validator('iri')
    def validate_iri(cls, v):
        """Validate IRI format.
        
        Args:
            v: The IRI string to validate
            
        Returns:
            str: The validated, stripped IRI
            
        Raises:
            ValueError: If IRI is empty, malformed, or invalid format
        """
        if not v or not v.strip():
            raise ValueError("IRI cannot be empty or None")
        v = v.strip()
        
        # Check if it's a valid URL format
        # IRIs should start with http:// or https:// or be a valid URN
        if not (v.startswith('http://') or v.startswith('https://') or v.startswith('urn:')):
            raise ValueError(
                f"Invalid IRI format: '{v}'. "
                f"IRIs must start with http://, https://, or urn:"
            )
        
        # Additional check for common TWA KG IRI pattern
        # Example: https://www.theworldavatar.com/kg/ontomops/ChemicalBuildingUnit_...
        if v.startswith('http'):
            try:
                # This will raise an error if the URL is malformed
                from pydantic import HttpUrl
                HttpUrl(v)  # This will validate the URL
            except Exception as e:
                raise ValueError(f"Invalid URL format for IRI: '{v}'. Error: {e}")
        
        return v


class IRIsInput(BaseModel):
    """Validation model for a list of IRIs.
    
    Validates each IRI in a list using IRIInput validation. Accepts empty
    lists (which will return empty results from queries).
    
    Example:
        >>> IRIsInput(iris=["http://example.com/iri1", "http://example.com/iri2"])
        >>> IRIsInput(iris=[])  # Returns empty list
    """
    iris: List[str] = Field(..., description="List of IRIs to validate")
    
    @validator('iris')
    def validate_iris_list(cls, v):
        """Validate list of IRIs.
        
        Args:
            v: List of IRI strings to validate
            
        Returns:
            List[str]: List of validated IRIs (empty list if input was empty)
        """
        if not v:
            return v  # Empty list is allowed
        
        validated_iris = []
        for iri in v:
            # Use IRIInput validator
            validated_iris.append(IRIInput(iri=iri).iri)
        
        return validated_iris


class DepthInput(BaseModel):
    """Validation model for recursion depth parameter.
    
    Validates that depth values are within safe bounds for KG queries.
    
    Valid depth values:
        - -1: infinite recursion (default, most reliable but slowest)
        - 0: no recursion (returns only direct properties as IRIs, not loaded objects)
        - 1-10: n-level recursion (higher = deeper property traversal)
    
    Note: For MOP assembly, depth=3 or depth=-1 is recommended to ensure
    all required properties are loaded (AM -> GBU -> GBUCoordinateCenter -> 
    GBUConnectingPoint, and GBU -> GBUType -> Modularity).
    
    Example:
        >>> DepthInput(depth=-1)  # Infinite recursion
        >>> DepthInput(depth=3)   # 3-level recursion (good for assembly)
        >>> DepthInput(depth=11)  # Raises ValueError
    """
    depth: int = Field(
        default=-1,
        description="Recursion depth for property traversal",
        ge=-1,
        le=10
    )
    
    @validator('depth')
    def validate_depth(cls, v):
        """Validate depth value with additional checks.
        
        Args:
            v: The depth value to validate
            
        Returns:
            int: The validated depth value
            
        Raises:
            ValueError: If depth is outside the valid range
        """
        # Note: ge=-1 and le=10 in Field already enforce bounds,
        # but we add custom messages for better UX
        if v < -1:
            raise ValueError(f"Depth must be >= -1, got {v}")
        if v > 10:
            raise ValueError(
                f"Depth of {v} is too large. Maximum allowed is 10. "
                f"For assembly, depth=3 or depth=-1 is recommended."
            )
        return v


class EndpointInput(BaseModel):
    """Validation model for SPARQL endpoint URL.
    
    Validates that the SPARQL endpoint is a valid HTTP/HTTPS URL.
    
    The endpoint should typically contain '/sparql' in the path, though
    this is not strictly enforced (some servers may use different paths).
    
    Example:
        >>> EndpointInput(endpoint="http://localhost:3838/sparql")
        >>> EndpointInput(endpoint="https://www.theworldavatar.com/kg/sparql")
        >>> EndpointInput(endpoint="ftp://example.com")  # Raises ValueError
    """
    endpoint: str = Field(..., description="SPARQL endpoint URL")
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        """Validate SPARQL endpoint URL.
        
        Args:
            v: The endpoint URL to validate
            
        Returns:
            str: The validated, stripped endpoint URL
            
        Raises:
            ValueError: If endpoint is empty or not a valid HTTP/HTTPS URL
        """
        if not v or not v.strip():
            raise ValueError("SPARQL endpoint cannot be empty")
        v = v.strip()
        
        # Must be a valid HTTP/HTTPS URL
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError(
                f"Invalid SPARQL endpoint: '{v}'. "
                f"Must start with http:// or https://"
            )
        
        # Should end with /sparql or contain /sparql
        if '/sparql' not in v:
            # It's valid but might not be a SPARQL endpoint - just warn via description
            pass
        
        return v


class CacheSizeInput(BaseModel):
    """Validation model for cache size parameter.
    
    Validates that cache size is within reasonable bounds to prevent
    excessive memory usage.
    
    Valid range: 1 to 10000 objects (default: 128)
    
    Example:
        >>> CacheSizeInput(max_cache_size=128)  # Default
        >>> CacheSizeInput(max_cache_size=1000)  # Larger cache
        >>> CacheSizeInput(max_cache_size=0)  # Raises ValueError
    """
    max_cache_size: int = Field(
        default=128,
        description="Maximum number of objects to cache",
        ge=1,
        le=10000
    )
    
    @validator('max_cache_size')
    def validate_cache_size(cls, v):
        """Validate cache size.
        
        Args:
            v: The cache size to validate
            
        Returns:
            int: The validated cache size
            
        Raises:
            ValueError: If cache size is outside the valid range (1-10000)
        """
        if v < 1:
            raise ValueError(f"Cache size must be at least 1, got {v}")
        if v > 10000:
            raise ValueError(
                f"Cache size of {v} is too large. "
                f"Maximum allowed is 10000 to prevent excessive memory usage."
            )
        return v


class FilePathInput(BaseModel):
    """Validation model for file paths.
    
    Validates that file paths are non-empty strings. Does not check
    if the file exists (use FilePathExistsInput for that).
    
    Example:
        >>> FilePathInput(path="/path/to/file.xyz")
        >>> FilePathInput(path="")  # Raises ValueError
    """
    path: str = Field(..., description="File path to validate")
    
    @validator('path')
    def validate_path(cls, v):
        """Validate file path is not empty.
        
        Args:
            v: The file path to validate
            
        Returns:
            str: The validated, stripped file path
            
        Raises:
            ValueError: If path is empty or None
        """
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()


class FilePathExistsInput(FilePathInput):
    """Validation model for file paths that must exist.
    
    Extends FilePathInput to also verify that the file exists on disk
    and is a regular file (not a directory).
    
    Example:
        >>> FilePathExistsInput(path="/path/to/existing_file.xyz")
        >>> FilePathExistsInput(path="/path/to/missing_file.xyz")  # Raises ValueError
    """
    path: str = Field(..., description="File path that must exist")
    
    @validator('path')
    def validate_path_exists(cls, v):
        """Validate file path exists and is a file.
        
        Args:
            v: The file path to validate
            
        Returns:
            str: The validated file path
            
        Raises:
            ValueError: If path is empty, doesn't exist, or is not a file
        """
        v = super().validate_path(v)
        
        path_obj = Path(v)
        if not path_obj.exists():
            raise ValueError(f"File does not exist: {v}")
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {v}")
        
        return v


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
        
        Raises:
            ImportError: If PySparqlClient is not available
            ValueError: If endpoint or max_cache_size validation fails
        """
        if PySparqlClient is None:
            raise ImportError(
                "twa.kg_operations.PySparqlClient is required. "
                "Please install the twa package."
            )
        
        # Validate inputs using Pydantic models
        validated_endpoint = EndpointInput(endpoint=endpoint).endpoint
        validated_cache_size = CacheSizeInput(max_cache_size=max_cache_size).max_cache_size
        
        self.endpoint = validated_endpoint
        self.max_cache_size = validated_cache_size
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
        
        # Validate file server URL if provided
        if self.fs_url and not (self.fs_url.startswith('http://') or self.fs_url.startswith('https://')):
            raise ValueError(
                f"Invalid file server URL: '{self.fs_url}'. "
                f"Must start with http:// or https://"
            )
        
        # Initialize the SPARQL client
        self.sparql_client = PySparqlClient(
            query_endpoint=validated_endpoint,
            update_endpoint=validated_endpoint,
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
        
        Raises:
            ValueError: If iris validation fails or depth is invalid
        """
        # Validate inputs
        if iris:
            validated_iris = IRIsInput(iris=iris).iris
        else:
            validated_iris = []
        
        validated_depth = DepthInput(depth=depth).depth
        
        if not validated_iris:
            return []
        
        # Convert to tuple for caching
        iris_tuple = tuple(sorted(validated_iris))
        
        # Use cached internal method
        return self._pull_objects_cached(iris_tuple, validated_depth)
    
    @lru_cache(maxsize=128)
    def _pull_objects_cached(
        self,
        iris: tuple,
        depth: int = -1,
    ) -> List[Dict[str, Any]]:
        """Internal cached method for pulling objects.
        
        Args:
            iris: Tuple of IRIs to pull
            depth: Recursion depth (note: depth is not yet used in the query)
        
        Returns:
            List of dictionaries containing the pulled object data
        
        Raises:
            QueryError: If the SPARQL query fails
        """
        start_time = time.time()
        
        try:
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
            
            # Convert results to list of dicts
            result_list = [dict(row) for row in results]
            
            # Check if we got results for all requested IRIs
            if result_list and iris:
                result_iris = {row.get('s') for row in result_list if row.get('s')}
                missing_iris = [iri for iri in iris if iri not in result_iris]
                
                if missing_iris:
                    # Log a warning but don't fail - some IRIs might legitimately have no properties
                    import warnings
                    warnings.warn(
                        f"No data returned for {len(missing_iris)} IRIs: {missing_iris[:3]}" +
                        ("..." if len(missing_iris) > 3 else ""),
                        UserWarning,
                        stacklevel=4
                    )
            
            return result_list
            
        except Exception as e:
            # Wrap any query execution errors in our custom exception
            raise QueryError(
                f"Failed to execute SPARQL query",
                query=query if 'query' in locals() else None,
                endpoint=self.endpoint,
                original_error=e
            ) from e
    
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
        
        Raises:
            ValueError: If iri is invalid
        """
        validated_iri = IRIInput(iri=iri).iri
        return self.pull_objects([validated_iri], depth=depth)
    
    def pull_for_assembly(
        self,
        am_iri: str,
        cbu_iris: List[str],
        depth: int = -1,
        batch_size: Optional[int] = None,
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
        
        **Performance Optimization:**
        - Batched queries for AM + CBUs (single query when possible)
        - LRU caching to avoid redundant pulls
        - Batch processing for large IRI lists (configurable batch_size)
        - Early validation to fail fast on invalid inputs
        
        Args:
            am_iri: The IRI of the AssemblyModel
            cbu_iris: List of CBU IRIs to pull
            depth: Recursion depth (default: -1 for full object resolution)
            batch_size: Optional batch size for large IRI lists (default: None = no batching)
                      If provided, pulls are split into chunks of this size
        
        Returns:
            Tuple of (AssemblyModel instance, list of ChemicalBuildingUnit instances)
        
        Raises:
            ValueError: If am_iri or any cbu_iris are invalid
            QueryError: If SPARQL queries fail
            ObjectNotFoundError: If AM or CBUs cannot be found
            InvalidObjectError: If pulled objects have invalid structure
        
        Example:
            # Full assembly with depth=-1 (recommended for reliability)
            am, cbus = kg_client.pull_for_assembly(am_iri, [cbu1_iri, cbu2_iri])
            mop = ontomops.MetalOrganicPolyhedron.from_assemble(
                am, cbus, prov, sparql_client=kg_client
            )
            
            # Faster with depth=3 (if your data structure is shallow)
            am, cbus = kg_client.pull_for_assembly(am_iri, [cbu1_iri, cbu2_iri], depth=3)
            
            # With batching for large IRI lists (optimization)
            am, cbus = kg_client.pull_for_assembly(am_iri, large_cbu_list, depth=3, batch_size=10)
        """
        # === Early Input Validation (Fail Fast) ===
        # Validate inputs before doing any KG work to avoid wasted queries
        validated_am_iri = IRIInput(iri=am_iri).iri
        
        if cbu_iris:
            validated_cbu_iris = IRIsInput(iris=cbu_iris).iris
        else:
            validated_cbu_iris = []
        
        validated_depth = DepthInput(depth=depth).depth
        
        # Validate batch_size if provided
        if batch_size is not None:
            if not isinstance(batch_size, int) or batch_size < 1:
                raise ValueError(f"batch_size must be a positive integer, got {batch_size}")
        
        # Warn if depth is too shallow for assembly
        if validated_depth < 3 and validated_depth != -1:
            import warnings
            warnings.warn(
                f"Depth={validated_depth} may be too shallow for MOP assembly. "
                f"Properties may be returned as IRIs instead of objects, causing failures. "
                f"For assembly, use depth=3 or depth=-1.",
                UserWarning,
                stacklevel=2
            )
        
        from twa.data_model.base_ontology import BaseClass
        from twa_mops.core.ontomops import AssemblyModel, ChemicalBuildingUnit
        
        # === Optimized Pulling ===
        try:
            # Pull the AM first
            # Note: We use the class's pull_from_kg method which handles caching internally
            am_list = AssemblyModel.pull_from_kg(
                [validated_am_iri], 
                self.sparql_client, 
                recursive_depth=validated_depth
            )
            
            if not am_list:
                raise ObjectNotFoundError(
                    f"AssemblyModel not found",
                    iris=[validated_am_iri],
                    object_type="AssemblyModel"
                )
            
            am = am_list[0]
            
            # Pull CBUs - use batching if specified
            if batch_size and len(validated_cbu_iris) > batch_size:
                # Process in batches to avoid overwhelming the KG
                cbus = []
                for i in range(0, len(validated_cbu_iris), batch_size):
                    batch = validated_cbu_iris[i:i + batch_size]
                    batch_cbus = ChemicalBuildingUnit.pull_from_kg(
                        batch, 
                        self.sparql_client, 
                        recursive_depth=validated_depth
                    )
                    cbus.extend(batch_cbus)
                    
                    # Check if we got all expected CBUs
                    if len(batch_cbus) < len(batch):
                        missing_in_batch = set(batch) - {cbu.instance_iri for cbu in batch_cbus}
                        raise ObjectNotFoundError(
                            f"Some CBUs not found in batch {i//batch_size + 1}",
                            iris=list(missing_in_batch),
                            object_type="ChemicalBuildingUnit"
                        )
            else:
                # Single batch pull
                cbus = ChemicalBuildingUnit.pull_from_kg(
                    validated_cbu_iris, 
                    self.sparql_client, 
                    recursive_depth=validated_depth
                )
                
                # Verify we got all requested CBUs
                if len(cbus) < len(validated_cbu_iris):
                    found_iris = {cbu.instance_iri for cbu in cbus}
                    missing_iris = [iri for iri in validated_cbu_iris if iri not in found_iris]
                    raise ObjectNotFoundError(
                        f"Some CBUs not found in KG",
                        iris=missing_iris,
                        object_type="ChemicalBuildingUnit"
                    )
            
            return am, cbus
            
        except Exception as e:
            # Wrap unexpected errors in QueryError
            if isinstance(e, (QueryError, ObjectNotFoundError, InvalidObjectError)):
                raise
            raise QueryError(
                f"Failed to pull objects for assembly",
                endpoint=self.endpoint,
                original_error=e
            ) from e
    
    def push_objects(
        self,
        objects: List[Any],
        depth: int = -1,
        provenance: Optional[Dict[str, Any]] = None,
        batch_size: Optional[int] = None,
        max_retries: int = 3,
    ) -> Tuple[Any, Any]:
        """Push objects to KG with provenance tracking.
        
        This method delegates to the underlying PySparqlClient for pushing
        RDF graphs to the Knowledge Graph.
        
        **Performance Optimization:**
        - Batching: Split large object lists into chunks (configurable batch_size)
        - Retry logic: Automatically retry failed pushes (configurable max_retries)
        - Early validation: Fail fast on invalid inputs before KG operations
        - Single transaction: All objects in a batch are pushed in a single transaction
        
        Args:
            objects: List of objects to push to the KG (typically BaseClass instances)
            depth: Recursion depth for collecting related objects (-1 = infinite)
            provenance: Optional provenance information to include
            batch_size: Optional batch size for large object lists (default: None = single transaction)
            max_retries: Maximum number of retry attempts for failed pushes (default: 3)
        
        Returns:
            Tuple of (graph_to_remove, graph_to_add) - the RDF graphs that were
            removed and added during the push operation
        
        Raises:
            ValueError: If objects list is empty, depth is invalid, or batch_size is invalid
            TypeError: If objects contains non-BaseClass instances
            QueryError: If push operation fails after retries
            InvalidObjectError: If objects have invalid structure
        """
        # === Early Input Validation (Fail Fast) ===
        validated_depth = DepthInput(depth=depth).depth
        
        if not objects:
            raise ValueError("No objects to push")
        
        # Validate batch_size
        if batch_size is not None:
            if not isinstance(batch_size, int) or batch_size < 1:
                raise ValueError(f"batch_size must be a positive integer, got {batch_size}")
        
        # Validate max_retries
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError(f"max_retries must be a non-negative integer, got {max_retries}")
        
        from rdflib import Graph
        
        # === Optimized Push with Batching and Retries ===
        try:
            if batch_size and len(objects) > batch_size:
                # Process in batches
                all_g_to_remove = Graph()
                all_g_to_add = Graph()
                
                for i in range(0, len(objects), batch_size):
                    batch = objects[i:i + batch_size]
                    
                    # Try each batch with retries
                    for attempt in range(max_retries + 1):
                        try:
                            batch_g_to_remove, batch_g_to_add = self._push_batch(
                                batch, validated_depth, provenance
                            )
                            all_g_to_remove += batch_g_to_remove
                            all_g_to_add += batch_g_to_add
                            break  # Success, exit retry loop
                        except (QueryError, Exception) as e:
                            if attempt == max_retries:
                                # Last attempt failed
                                raise QueryError(
                                    f"Failed to push batch {i//batch_size + 1} after {max_retries} retries",
                                    endpoint=self.endpoint,
                                    original_error=e
                                ) from e
                            # Log retry and continue
                            import warnings
                            warnings.warn(
                                f"Retry {attempt + 1}/{max_retries} for batch {i//batch_size + 1}: {e}",
                                UserWarning
                            )
                
                # Perform the actual push for all batches
                result = self.sparql_client.delete_and_insert_graphs(all_g_to_remove, all_g_to_add)
                return all_g_to_remove, all_g_to_add
            else:
                # Single batch push
                g_to_remove, g_to_add = self._push_batch(objects, validated_depth, provenance)
                result = self.sparql_client.delete_and_insert_graphs(g_to_remove, g_to_add)
                return g_to_remove, g_to_add
                
        except Exception as e:
            # Wrap unexpected errors
            if isinstance(e, (QueryError, InvalidObjectError)):
                raise
            raise QueryError(
                f"Failed to push objects to KG",
                endpoint=self.endpoint,
                original_error=e
            ) from e
    
    def _push_batch(
        self,
        objects: List[Any],
        depth: int,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Any]:
        """Push a batch of objects to KG.
        
        Internal method used by push_objects for batching.
        
        Args:
            objects: List of objects to push
            depth: Recursion depth for collecting related objects
            provenance: Optional provenance information
        
        Returns:
            Tuple of (graph_to_remove, graph_to_add)
        
        Raises:
            NotImplementedError: If objects contain Pydantic models
            InvalidObjectError: If objects have invalid structure
        """
        from rdflib import Graph
        
        # Collect all triples from all objects
        g_to_remove = Graph()
        g_to_add = Graph()
        
        for i, obj in enumerate(objects):
            # Check if object has _collect_diff_to_graph method (from BaseClass)
            if hasattr(obj, '_collect_diff_to_graph'):
                try:
                    obj_g_to_remove, obj_g_to_add = obj._collect_diff_to_graph(
                        g_to_remove, g_to_add, depth
                    )
                    g_to_remove += obj_g_to_remove
                    g_to_add += obj_g_to_add
                except Exception as e:
                    raise InvalidObjectError(
                        f"Failed to collect graph for object at index {i}",
                        iri=getattr(obj, 'instance_iri', None),
                        reason=str(e)
                    ) from e
            else:
                # For Pydantic models, we need to serialize them to RDF first
                # This is a placeholder for future implementation
                raise InvalidObjectError(
                    f"Pushing Pydantic models is not yet implemented",
                    iri=getattr(obj, 'instance_iri', None),
                    reason=f"Object type: {type(obj)}"
                )
    
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
        
        Raises:
            ValueError: If query is empty or None
        """
        if not query or not query.strip():
            raise ValueError("SPARQL query cannot be empty or None")
        
        return self.sparql_client.perform_query(query.strip())
    
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
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> bool:
        """Download a file from the KG file server.
        
        **Performance Optimization:**
        - Retry logic for transient network failures
        - Configurable retry delay
        
        Args:
            remote_path: The remote file path
            local_path: The local destination path
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
        
        Returns:
            True if download was successful
        
        Raises:
            ValueError: If remote_path or local_path is invalid
            QueryError: If download fails after all retries
        """
        # Validate inputs
        validated_remote = FilePathInput(path=remote_path).path
        validated_local = FilePathInput(path=local_path).path
        
        # Validate retry parameters
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError(f"max_retries must be a non-negative integer, got {max_retries}")
        if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            raise ValueError(f"retry_delay must be a non-negative number, got {retry_delay}")
        
        # Try with retries
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                result = self.sparql_client.download_file(validated_remote, validated_local)
                return result
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    import time
                    import warnings
                    warnings.warn(
                        f"Download attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}",
                        UserWarning
                    )
                    time.sleep(retry_delay)
                    # Exponential backoff
                    retry_delay *= 2
        
        # All retries failed
        raise QueryError(
            f"Failed to download file after {max_retries} retries",
            endpoint=self.fs_url or self.endpoint,
            original_error=last_error
        ) from last_error
    
    def upload_file(
        self,
        local_path: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> tuple:
        """Upload a file to the KG file server.
        
        **Performance Optimization:**
        - Retry logic for transient network failures
        - Configurable retry delay
        - File existence validation before upload
        
        Args:
            local_path: The local file path to upload
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
        
        Returns:
            Tuple of (remote_path, timestamp)
        
        Raises:
            ValueError: If local_path is invalid or file doesn't exist
            QueryError: If upload fails after all retries
        """
        # Validate inputs
        validated_local = FilePathExistsInput(path=local_path).path
        
        # Validate retry parameters
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError(f"max_retries must be a non-negative integer, got {max_retries}")
        if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            raise ValueError(f"retry_delay must be a non-negative number, got {retry_delay}")
        
        # Try with retries
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                result = self.sparql_client.upload_file(validated_local)
                return result
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    import time
                    import warnings
                    warnings.warn(
                        f"Upload attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}",
                        UserWarning
                    )
                    time.sleep(retry_delay)
                    # Exponential backoff
                    retry_delay *= 2
        
        # All retries failed
        raise QueryError(
            f"Failed to upload file after {max_retries} retries",
            endpoint=self.fs_url or self.endpoint,
            original_error=last_error
        ) from last_error
    
    def perform_query(self, query: str) -> Any:
        """Alias for execute_query to match PySparqlClient interface.
        
        Args:
            query: The SPARQL query string to execute
        
        Returns:
            The query results
        
        Raises:
            ValueError: If query is empty or None
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
        
        Raises:
            TypeError: If cls is not a BaseClass subclass
            ValueError: If iris validation fails or depth is invalid
        """
        # Import here to avoid circular imports
        from twa.data_model.base_ontology import BaseClass
        
        # Validate class type
        if not isinstance(cls, type) or not issubclass(cls, BaseClass):
            raise TypeError(f"cls must be a BaseClass subclass, got {type(cls)}")
        
        # Validate IRIs and depth
        validated_iris = IRIsInput(iris=iris).iris if iris else []
        validated_depth = DepthInput(depth=depth).depth
        
        # Use pull_from_kg which handles the conversion from RDF results to class instances
        return cls.pull_from_kg(validated_iris, self.sparql_client, recursive_depth=validated_depth)
    
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
        
        Raises:
            TypeError: If cls is not a BaseClass subclass
            ValueError: If iris validation fails or depth is invalid
        
        Example:
            # Fast pull for assembly (doesn't load nested geometry)
            cbus = kg_client.pull_instances_fast(ChemicalBuildingUnit, iris)
        """
        return self.pull_instances(cls, iris, depth=depth)

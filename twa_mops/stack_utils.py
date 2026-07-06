"""Stack switching utilities for MOPTools.

This module provides utilities for switching between local and remote stacks,
with automatic validation of connectivity and configuration.

Usage:
    from stack_utils import switch_stack, validate_stack_connectivity, get_stack_config
    
    # Switch to remote stack
    switch_stack("remote")
    
    # Validate current stack connectivity
    validate_stack_connectivity()
    
    # Get current stack configuration
    config = get_stack_config()
"""

import os
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)


class StackType(Enum):
    """Enumeration of available stack types."""
    LOCAL = "local"
    REMOTE = "remote"


# Stack configurations
STACK_CONFIGS = {
    StackType.LOCAL: {
        "sparql_endpoint": "http://localhost:3838/blazegraph/namespace/ontomops/sparql",
        "fs_url": "http://localhost:8000/",
        "namespace": "ontomops",
        "name": "Local Stack",
        "description": "Local development stack with Blazegraph and file server"
    },
    StackType.REMOTE: {
        "sparql_endpoint": "http://68.183.227.15:3838/blazegraph/namespace/ontomops_ogm_dummy/sparql",
        "fs_url": "http://68.183.227.15:3838/file-server/",
        "namespace": "ontomops",
        "name": "Remote Stack", 
        "description": "Remote production stack at The World Avatar (namespace: ontomops, blazegraph namespace: ontomops_ogm_dummy)"
    }
}

# Global state for current stack
_current_stack: StackType = StackType.LOCAL


def get_stack_config(stack_type: Optional[StackType] = None) -> Dict[str, Any]:
    """Get configuration for a specific stack type.
    
    Args:
        stack_type: The stack type to get configuration for. If None, uses current stack.
        
    Returns:
        Dictionary containing stack configuration
        
    Raises:
        ValueError: If stack_type is not recognized
    """
    if stack_type is None:
        stack_type = _current_stack
    
    if stack_type not in STACK_CONFIGS:
        raise ValueError(f"Unknown stack type: {stack_type}. Available types: {list(STACK_CONFIGS.keys())}")
    
    return STACK_CONFIGS[stack_type].copy()


def get_current_stack() -> StackType:
    """Get the current stack type.
    
    Returns:
        The current stack type
    """
    return _current_stack


def switch_stack(stack_name: str, validate: bool = True) -> StackType:
    """Switch to a different stack.
    
    Args:
        stack_name: Name of the stack to switch to ("local" or "remote")
        validate: Whether to validate stack connectivity after switching (default: True)
        
    Returns:
        The stack type that was switched to
        
    Raises:
        ValueError: If stack_name is not recognized
        ConnectionError: If validate=True and connectivity validation fails
    """
    global _current_stack
    
    # Convert string to StackType
    stack_name = stack_name.lower()
    if stack_name == "local":
        new_stack = StackType.LOCAL
    elif stack_name == "remote":
        new_stack = StackType.REMOTE
    else:
        raise ValueError(f"Unknown stack: {stack_name}. Available stacks: 'local', 'remote'")
    
    old_stack = _current_stack
    _current_stack = new_stack
    
    logger.info(f"Switching from {old_stack.value} stack to {new_stack.value} stack")
    
    if validate:
        validate_stack_connectivity()
    
    return new_stack


def validate_stack_connectivity() -> bool:
    """Validate that the current stack is reachable.
    
    Tests both SPARQL endpoint and file server connectivity.
    
    Returns:
        True if both endpoints are reachable
        
    Raises:
        ConnectionError: If SPARQL endpoint or file server is not reachable
    """
    config = get_stack_config()
    sparql_endpoint = config["sparql_endpoint"]
    fs_url = config["fs_url"]
    
    import requests
    
    # Test SPARQL endpoint
    try:
        test_query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"
        response = requests.post(
            sparql_endpoint,
            data={"query": test_query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10  # Use a shorter timeout for connectivity testing
        )
        response.raise_for_status()
        logger.info(f"SPARQL endpoint {sparql_endpoint} is reachable.")
    except Exception as e:
        logger.error(f"SPARQL endpoint {sparql_endpoint} failed: {e}")
        raise ConnectionError(f"SPARQL endpoint {sparql_endpoint} is not reachable: {e}")
    
    # Test file server (just check if it responds, not if it has files)
    try:
        response = requests.get(fs_url, timeout=10)
        # File server might return 400 for root directory, which is still a valid response
        if response.status_code in [200, 400, 404]:
            logger.info(f"File server {fs_url} is reachable.")
        else:
            logger.warning(f"File server {fs_url} responded with status {response.status_code}")
    except Exception as e:
        logger.error(f"File server {fs_url} failed: {e}")
        raise ConnectionError(f"File server {fs_url} is not reachable: {e}")
    
    return True


def apply_stack_config_to_client(client) -> None:
    """Apply current stack configuration to a KnowledgeGraphClient.
    
    Args:
        client: The KnowledgeGraphClient instance to configure
    """
    config = get_stack_config()
    
    # Update client configuration
    client.endpoint = config["sparql_endpoint"]
    client.fs_url = config["fs_url"]
    
    logger.info(f"Applied {_current_stack.value} stack configuration to client")


def get_client_for_stack(stack_name: Optional[str] = None, **kwargs) -> Any:
    """Get a KnowledgeGraphClient configured for a specific stack.
    
    Args:
        stack_name: Name of the stack ("local" or "remote"). If None, uses current stack.
        **kwargs: Additional arguments to pass to KnowledgeGraphClient constructor
        
    Returns:
        Configured KnowledgeGraphClient instance
    """
    if stack_name is not None:
        switch_stack(stack_name, validate=False)  # Don't validate yet, let client do it
    
    config = get_stack_config()
    
    from twa_mops.kg.client import KnowledgeGraphClient
    from twa_mops.config import settings
    
    # Determine if we're using the remote stack
    current_stack = get_current_stack()
    is_remote = current_stack == StackType.REMOTE
    
    # Use longer timeout for remote stack (120 seconds) to handle slow connections
    # For local stack, use the configured timeout or default
    effective_timeout = kwargs.get('timeout', settings.timeout if is_remote else 30)
    if is_remote and effective_timeout == 30:  # Only override if not explicitly set
        effective_timeout = 120
    
    # Merge stack config with any provided kwargs
    client_kwargs = {
        "endpoint": config["sparql_endpoint"],
        "fs_url": config["fs_url"],
        "timeout": effective_timeout,
        "max_retries": kwargs.get('max_retries', 3),
        "retry_delay": kwargs.get('retry_delay', 1.0),
        **kwargs
    }
    
    return KnowledgeGraphClient(**client_kwargs)


def list_stacks() -> Dict[str, Dict[str, Any]]:
    """List all available stacks and their configurations.
    
    Returns:
        Dictionary mapping stack names to their configurations
    """
    return {
        stack_type.value: {
            "name": config["name"],
            "description": config["description"],
            "sparql_endpoint": config["sparql_endpoint"],
            "fs_url": config["fs_url"],
            "namespace": config["namespace"],
            "is_current": stack_type == _current_stack
        }
        for stack_type, config in STACK_CONFIGS.items()
    }


def get_current_namespace() -> str:
    """Get the current namespace for the active stack.
    
    Returns:
        The namespace string (e.g., 'ontomops' or 'ontomops_ogm_dummy')
    """
    config = get_stack_config()
    return config.get("namespace", "ontomops")


def convert_iri_namespace(iri: str, target_namespace: Optional[str] = None) -> str:
    """Convert an IRI from one namespace to another.
    
    Args:
        iri: The IRI to convert
        target_namespace: The target namespace. If None, uses the current stack's namespace.
        
    Returns:
        The IRI with the namespace replaced
        
    Example:
        >>> convert_iri_namespace(
        ...     'https://www.theworldavatar.com/kg/ontomops/ChemicalBuildingUnit_123',
        ...     'ontomops_ogm_dummy'
        ... )
        'https://www.theworldavatar.com/kg/ontomops_ogm_dummy/ChemicalBuildingUnit_123'
    """
    if target_namespace is None:
        target_namespace = get_current_namespace()
    
    # Replace the namespace in the IRI
    for stack_type, config in STACK_CONFIGS.items():
        source_namespace = config["namespace"]
        if source_namespace in iri:
            return iri.replace(source_namespace, target_namespace)
    
    # If no known namespace found, just use the target namespace
    if "ontomops" in iri:
        # Find the position after the last slash before ontomops
        parts = iri.split("/")
        for i, part in enumerate(parts):
            if "ontomops" in part:
                parts[i] = target_namespace
                return "/".join(parts)
    
    return iri


def get_iri_for_stack(iri: str, stack_name: str) -> str:
    """Get an IRI converted for a specific stack.
    
    Args:
        iri: The IRI to convert
        stack_name: The stack name ('local' or 'remote')
        
    Returns:
        The IRI with the appropriate namespace for the specified stack
    """
    stack_type = StackType.LOCAL if stack_name == "local" else StackType.REMOTE
    target_namespace = STACK_CONFIGS[stack_type]["namespace"]
    return convert_iri_namespace(iri, target_namespace)


def discover_available_iris(stack_name: Optional[str] = None, limit: int = 50) -> Dict[str, List[str]]:
    """Discover available IRIs (AssemblyModels, ChemicalBuildingUnits, GenericBuildingUnits) from a stack.
    
    Args:
        stack_name: The stack name ('local' or 'remote'). If None, uses current stack.
        limit: Maximum number of IRIs to return per type
        
    Returns:
        Dictionary with keys 'assembly_models', 'chemical_building_units', 'generic_building_units'
        containing lists of IRIs
    """
    import requests
    
    if stack_name is not None:
        old_stack = _current_stack
        switch_stack(stack_name, validate=False)
    
    try:
        config = get_stack_config()
        sparql_endpoint = config["sparql_endpoint"]
        namespace = config["namespace"]
        
        results = {
            "assembly_models": [],
            "chemical_building_units": [],
            "generic_building_units": []
        }
        
        # Query for each type
        queries = {
            "assembly_models": f"SELECT DISTINCT ?iri WHERE {{ ?iri a <https://www.theworldavatar.com/kg/{namespace}/AssemblyModel> }} LIMIT {limit}",
            "chemical_building_units": f"SELECT DISTINCT ?iri WHERE {{ ?iri a <https://www.theworldavatar.com/kg/{namespace}/ChemicalBuildingUnit> }} LIMIT {limit}",
            "generic_building_units": f"SELECT DISTINCT ?iri WHERE {{ ?iri a <https://www.theworldavatar.com/kg/{namespace}/GenericBuildingUnit> }} LIMIT {limit}"
        }
        
        for key, query in queries.items():
            try:
                response = requests.post(
                    sparql_endpoint,
                    data={"query": query},
                    headers={"Accept": "application/sparql-results+json"},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                for binding in data.get("results", {}).get("bindings", []):
                    results[key].append(binding["iri"]["value"])
            except Exception as e:
                logger.warning(f"Failed to query {key}: {e}")
        
        return results
    finally:
        if stack_name is not None:
            # Switch back to original stack
            _current_stack = old_stack
            logger.info(f"Restored stack to {old_stack.value}")

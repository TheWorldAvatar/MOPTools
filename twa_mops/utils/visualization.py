"""Visualization utilities for MOPTools.

This module provides simple visualization functions that use xyzrender for
interactive 3D visualization with automatic pore detection for MOPs.
Plotly functions are preserved as fallback for when xyzrender is not available.

The xyzrender backend provides better performance and more features for
visualizing molecular structures and automatically detects pores in MOPs.
"""

from typing import Optional, Any, List, Tuple
import os
import tempfile
import uuid

# Try to import networkx for direct graph creation
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

# Try to import xyzrender
try:
    import xyzrender
    XYZRENDER_AVAILABLE = True
except ImportError:
    XYZRENDER_AVAILABLE = False

# Try to import plotly
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Try to import pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class VisualizationError(Exception):
    """Base exception for visualization errors."""
    pass


class BackendNotAvailableError(VisualizationError):
    """Raised when neither xyzrender nor plotly is available."""
    pass


class InvalidGeometryError(VisualizationError):
    """Raised when geometry data is invalid or missing."""
    pass


# ============================================================================
# XYZ File Path Utilities
# ============================================================================

def _get_xyz_file_path_from_geometry(obj, data_dir=None) -> Optional[str]:
    """Extract XYZ file path from an object's geometry and find the actual file.
    
    Args:
        obj: Object with hasGeometry property (MOP, CBU, or AM)
        data_dir: Data directory to search for the file
    
    Returns:
        Path to XYZ file, or None if not available
    """
    try:
        geometry = list(obj.hasGeometry)[0]
        if hasattr(geometry, 'hasGeometryFile') and geometry.hasGeometryFile:
            file_path = list(geometry.hasGeometryFile)[0]
            
            # If it's a URL, extract the filename
            if file_path.startswith(('http://', 'https://')):
                file_path = file_path.split('/')[-1]
            
            # If the file exists at the given path, return it
            if os.path.exists(file_path):
                return file_path
            
            # Otherwise, search for the file in common locations
            search_paths = []
            if data_dir:
                search_paths.append(data_dir)
            
            # Add default search paths
            search_paths.extend(['.', 'data', '../data', '../../data', 'twa_mops/data', 
                               '../twa_mops/data', 'tutorials/data', 'tutorials'])
            
            # Look for the file in search paths
            for search_path in search_paths:
                test_path = os.path.join(search_path, file_path)
                if os.path.exists(test_path):
                    return test_path
            
            # Return the filename anyway (might be found later)
            return file_path
    except (IndexError, AttributeError):
        pass
    return None


def _create_xyz_networkx_graph(coordinates: List[Tuple[str, float, float, float]], center_to_cp_only: bool = False) -> Optional[Any]:
    """Create a networkx graph from coordinate data for direct use with xyzrender.
    
    Args:
        coordinates: List of tuples (element_label, x, y, z)
        center_to_cp_only: If True, only create edges from center (index 0) to connecting points.
                         If False, create edges between consecutive nodes (default behavior).
    
    Returns:
        networkx.Graph object ready for xyzrender.Molecule(), or None if creation failed
    """
    if not coordinates or not NETWORKX_AVAILABLE:
        return None
    
    try:
        import networkx as nx
        
        # Create a networkx graph
        graph = nx.Graph()
        
        # Define atomic properties for common elements
        atomic_data = {
            'H': {'atomic_number': 1, 'valence': 1.0, 'metal_valence': 0},
            'C': {'atomic_number': 6, 'valence': 4.0, 'metal_valence': 0},
            'N': {'atomic_number': 7, 'valence': 3.0, 'metal_valence': 0},
            'O': {'atomic_number': 8, 'valence': 2.0, 'metal_valence': 0},
            'F': {'atomic_number': 9, 'valence': 1.0, 'metal_valence': 0},
            'P': {'atomic_number': 15, 'valence': 3.0, 'metal_valence': 0},
            'S': {'atomic_number': 16, 'valence': 2.0, 'metal_valence': 0},
            'Cl': {'atomic_number': 17, 'valence': 1.0, 'metal_valence': 0},
            'Br': {'atomic_number': 35, 'valence': 1.0, 'metal_valence': 0},
            'I': {'atomic_number': 53, 'valence': 1.0, 'metal_valence': 0},
            'default': {'atomic_number': 6, 'valence': 4.0, 'metal_valence': 0}
        }
        
        # Add nodes for each coordinate
        for i, (element, x, y, z) in enumerate(coordinates):
            # Use first letter for element symbol to avoid long names
            if len(element) > 1 and element[1:].isdigit():
                # Handle elements like 'Cl', 'Br', etc.
                symbol = element
            else:
                # Use first character only for simple elements
                symbol = element[0].upper() if element else 'C'
            
            # Get atomic data or use default (Carbon)
            element_data = atomic_data.get(symbol, atomic_data['default'])
            
            # Add node with xyzrender-compatible attributes
            graph.add_node(i, 
                symbol=symbol,
                atomic_number=element_data['atomic_number'],
                position=(float(x), float(y), float(z)),
                formal_charge=0,  # Default charge
                valence=element_data['valence'],
                metal_valence=element_data['metal_valence']
            )
        
        # Add edges based on the bonding pattern
        if center_to_cp_only and len(coordinates) > 1:
            # Only create edges from center (index 0) to each connecting point
            for i in range(1, len(coordinates)):
                graph.add_edge(0, i)
        else:
            # Add edges between consecutive nodes to create a connected structure
            # This helps xyzrender understand the molecular structure
            for i in range(len(coordinates) - 1):
                graph.add_edge(i, i + 1)
        
        return graph
        
    except Exception:
        return None


def _create_xyz_networkx_graph_with_gbu_structure(coordinates: List[Tuple[str, float, float, float]], coordinate_center_sizes: List[int]) -> Optional[Any]:
    """Create a networkx graph for AM visualization with proper coordinate center structure.
    
    For AssemblyModels, this creates bonds only from each center to its own connecting points,
    not between different coordinate centers or GBUs.
    
    Args:
        coordinates: List of coordinate tuples (element_label, x, y, z) from all coordinate centers concatenated
        coordinate_center_sizes: List of integers where each integer is the number of coordinates 
                   contributed by the corresponding coordinate center (1 center + N connecting points)
    
    Returns:
        networkx.Graph object ready for xyzrender.Molecule(), or None if creation failed
    """
    if not coordinates or not NETWORKX_AVAILABLE or not coordinate_center_sizes:
        return None
    
    try:
        import networkx as nx
        
        # Create a networkx graph
        graph = nx.Graph()
        
        # Define atomic properties for common elements
        atomic_data = {
            'H': {'atomic_number': 1, 'valence': 1.0, 'metal_valence': 0},
            'C': {'atomic_number': 6, 'valence': 4.0, 'metal_valence': 0},
            'N': {'atomic_number': 7, 'valence': 3.0, 'metal_valence': 0},
            'O': {'atomic_number': 8, 'valence': 2.0, 'metal_valence': 0},
            'F': {'atomic_number': 9, 'valence': 1.0, 'metal_valence': 0},
            'P': {'atomic_number': 15, 'valence': 3.0, 'metal_valence': 0},
            'S': {'atomic_number': 16, 'valence': 2.0, 'metal_valence': 0},
            'Cl': {'atomic_number': 17, 'valence': 1.0, 'metal_valence': 0},
            'Br': {'atomic_number': 35, 'valence': 1.0, 'metal_valence': 0},
            'I': {'atomic_number': 53, 'valence': 1.0, 'metal_valence': 0},
            'default': {'atomic_number': 6, 'valence': 4.0, 'metal_valence': 0}
        }
        
        # Add nodes for each coordinate
        for i, (element, x, y, z) in enumerate(coordinates):
            # Use first letter for element symbol to avoid long names
            if len(element) > 1 and element[1:].isdigit():
                symbol = element
            else:
                symbol = element[0].upper() if element else 'C'
            
            element_data = atomic_data.get(symbol, atomic_data['default'])
            
            graph.add_node(i, 
                symbol=symbol,
                atomic_number=element_data['atomic_number'],
                position=(float(x), float(y), float(z)),
                formal_charge=0,
                valence=element_data['valence'],
                metal_valence=element_data['metal_valence']
            )
        
        # Add edges: from each center to its connecting points
        offset = 0
        for cc_size in coordinate_center_sizes:
            if cc_size > 0:
                # Center is at offset, connecting points are offset+1 to offset+cc_size-1
                center_idx = offset
                for cp_idx in range(offset + 1, offset + cc_size):
                    graph.add_edge(center_idx, cp_idx)
                offset += cc_size
        
        return graph
        
    except Exception:
        return None


# ============================================================================
# Simple xyzrender Wrapper Functions
# ============================================================================

def _visualise_with_xyzrender(file_path: str, pore: bool = False, **kwargs) -> Any:
    """Simple wrapper around xyzrender.load() and xyzrender.render().
    
    Args:
        file_path: Path to XYZ file to load and render
        pore: Whether to enable pore detection (for MOPs)
        **kwargs: Additional arguments passed to xyzrender.render()
    
    Returns:
        xyzrender SVGResult object
    
    Raises:
        BackendNotAvailableError: If xyzrender is not available
        FileNotFoundError: If the XYZ file doesn't exist
    """
    if not XYZRENDER_AVAILABLE:
        raise BackendNotAvailableError(
            "xyzrender is not available. Please install it: pip install xyzrender"
        )
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"XYZ file not found: {file_path}")
    
    # Load the molecule directly from XYZ file
    mol = xyzrender.load(file_path)
    
    # Render with pore detection if requested
    return xyzrender.render(mol, pore=pore, **kwargs)


def _visualise_with_xyzrender_graph(graph: Any, pore: bool = False, **kwargs) -> Any:
    """Render a networkx graph directly using xyzrender.
    
    Args:
        graph: networkx.Graph object with xyzrender-compatible node attributes
        pore: Whether to enable pore detection (for MOPs)
        **kwargs: Additional arguments passed to xyzrender.render()
    
    Returns:
        xyzrender SVGResult object
    
    Raises:
        BackendNotAvailableError: If xyzrender or networkx is not available
    """
    if not XYZRENDER_AVAILABLE:
        raise BackendNotAvailableError(
            "xyzrender is not available. Please install it: pip install xyzrender"
        )
    
    if not NETWORKX_AVAILABLE or graph is None:
        raise BackendNotAvailableError(
            "networkx is not available. Please install it: pip install networkx"
        )
    
    # Create xyzrender Molecule from the graph
    mol = xyzrender.Molecule(graph)
    
    # Render with pore detection if requested
    return xyzrender.render(mol, pore=pore, **kwargs)


# ============================================================================
# Main Visualization Functions
# ============================================================================

def visualise_mop(mop, backend: str = 'auto', data_dir: Optional[str] = None, **kwargs) -> Any:
    """Visualise a MetalOrganicPolyhedron.
    
    Uses xyzrender if available (preferred), falls back to plotly.
    Pores are automatically detected for MOPs when using xyzrender.
    
    Args:
        mop: MetalOrganicPolyhedron object to visualise
        backend: Backend to use ('auto', 'xyzrender', 'plotly') (default: 'auto')
        data_dir: Data directory for geometry files (default: None)
        **kwargs: Additional arguments passed to the render function
    
    Returns:
        Visualisation object (xyzrender.SVGResult or plotly.Figure)
    
    Raises:
        BackendNotAvailableError: If no backend is available
        InvalidGeometryError: If geometry data is missing
    """
    if backend == 'auto':
        backend = 'xyzrender' if XYZRENDER_AVAILABLE else 'plotly'
    
    if backend == 'xyzrender':
        if not XYZRENDER_AVAILABLE:
            raise BackendNotAvailableError(
                "xyzrender is not available. Please install it: pip install xyzrender"
            )
        
        # Get XYZ file path
        xyz_file_path = _get_xyz_file_path_from_geometry(mop, data_dir=data_dir)
        
        if xyz_file_path and os.path.exists(xyz_file_path):
            # Use xyzrender with pore detection enabled for MOPs
            return _visualise_with_xyzrender(xyz_file_path, pore=True, **kwargs)
        else:
            # Fall back to plotly if file not found
            if PLOTLY_AVAILABLE:
                return visualise_mop_plotly(mop, **kwargs)
            else:
                raise BackendNotAvailableError(
                    "plotly is not available as fallback. Please install it: pip install plotly"
                )
    
    elif backend == 'plotly':
        if not PLOTLY_AVAILABLE:
            raise BackendNotAvailableError(
                "plotly is not available. Please install it: pip install plotly"
            )
        return visualise_mop_plotly(mop, **kwargs)
    
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'auto', 'xyzrender', or 'plotly'")


def visualise_cbu(cbu, backend: str = 'auto', data_dir: Optional[str] = None, **kwargs) -> Any:
    """Visualise a ChemicalBuildingUnit.
    
    Uses xyzrender if available (preferred), falls back to plotly.
    
    Args:
        cbu: ChemicalBuildingUnit object to visualise
        backend: Backend to use ('auto', 'xyzrender', 'plotly') (default: 'auto')
        data_dir: Data directory for geometry files (default: None)
        **kwargs: Additional arguments passed to the render function
    
    Returns:
        Visualisation object (xyzrender.SVGResult or plotly.Figure)
    
    Raises:
        BackendNotAvailableError: If no backend is available
        InvalidGeometryError: If geometry data is missing
    """
    if backend == 'auto':
        backend = 'xyzrender' if XYZRENDER_AVAILABLE else 'plotly'
    
    if backend == 'xyzrender':
        if not XYZRENDER_AVAILABLE:
            raise BackendNotAvailableError(
                "xyzrender is not available. Please install it: pip install xyzrender"
            )
        
        # Get XYZ file path
        xyz_file_path = _get_xyz_file_path_from_geometry(cbu, data_dir=data_dir)
        
        if xyz_file_path and os.path.exists(xyz_file_path):
            # CBUs don't need pore detection
            return _visualise_with_xyzrender(xyz_file_path, pore=False, **kwargs)
        else:
            # Fall back to plotly if file not found
            if PLOTLY_AVAILABLE:
                return visualise_cbu_plotly(cbu, **kwargs)
            else:
                raise BackendNotAvailableError(
                    "plotly is not available as fallback. Please install it: pip install plotly"
                )
    
    elif backend == 'plotly':
        if not PLOTLY_AVAILABLE:
            raise BackendNotAvailableError(
                "plotly is not available. Please install it: pip install plotly"
            )
        return visualise_cbu_plotly(cbu, **kwargs)
    
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'auto', 'xyzrender', or 'plotly'")


def visualise_gbu(gbu, backend: str = 'auto', data_dir: Optional[str] = None, debug: bool = False, use_barycenter: bool = False, use_first_only: bool = True, **kwargs) -> Any:
    """Visualise a GenericBuildingUnit.
    
    Uses xyzrender if available (preferred), falls back to plotly.
    GBUs are visualized using their coordinate center and connecting point data.
    
    Args:
        gbu: GenericBuildingUnit object to visualise
        backend: Backend to use ('auto', 'xyzrender', 'plotly') (default: 'auto')
        data_dir: Data directory for geometry files (default: None)
        debug: If True, print debug information about coordinate extraction (default: False)
        use_barycenter: If True, calculate the barycenter of connecting points instead of using the given coordinate center. This ensures the center point is the geometric center of the connecting points (default: False)
        use_first_only: If True, only use the first GBUCoordinateCenter for the GBU (default: True). Set to False to use all coordinate centers, which may be needed for GBUs that appear in multiple positions.
        **kwargs: Additional arguments passed to the render function
    
    Returns:
        Visualisation object (xyzrender.SVGResult or plotly.Figure)
    
    Raises:
        BackendNotAvailableError: If no backend is available
        InvalidGeometryError: If no coordinate data is available
    """
    if backend == 'auto':
        backend = 'xyzrender' if XYZRENDER_AVAILABLE else 'plotly'
    
    if backend == 'xyzrender':
        if not XYZRENDER_AVAILABLE:
            raise BackendNotAvailableError(
                "xyzrender is not available. Please install it: pip install xyzrender"
            )
        
        # Extract coordinates from GBU
        coordinates = _extract_gbu_coordinates(gbu, debug=debug, use_barycenter=use_barycenter, use_first_only=use_first_only)
        
        if debug:
            print(f"DEBUG: Extracted {len(coordinates)} coordinates for GBU visualization")
        
        if coordinates:
            # Create networkx graph directly for xyzrender (no temporary files needed!)
            # For GBUs, only show bonds from center to connecting points
            graph = _create_xyz_networkx_graph(coordinates, center_to_cp_only=True)
            if graph is not None:
                # Use xyzrender with the graph directly (no pore detection for GBUs)
                return _visualise_with_xyzrender_graph(graph, pore=False, **kwargs)
        
        # Fall back to plotly if no coordinates or graph creation failed
        if PLOTLY_AVAILABLE:
            return visualise_gbu_plotly(gbu, **kwargs)
        else:
            raise BackendNotAvailableError(
                "plotly is not available as fallback. Please install it: pip install plotly"
            )
    
    elif backend == 'plotly':
        if not PLOTLY_AVAILABLE:
            raise BackendNotAvailableError(
                "plotly is not available. Please install it: pip install plotly"
            )
        return visualise_gbu_plotly(gbu, **kwargs)
    
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'auto', 'xyzrender', or 'plotly'")


def visualise_am(am, backend: str = 'auto', data_dir: Optional[str] = None, debug: bool = False, use_barycenter: bool = False, use_first_only: bool = False, **kwargs) -> Any:
    """Visualise an AssemblyModel.
    
    Uses xyzrender if available (preferred), falls back to plotly.
    AssemblyModels are visualized using coordinate data from their constituent GBUs.
    
    Args:
        am: AssemblyModel object to visualise
        backend: Backend to use ('auto', 'xyzrender', 'plotly') (default: 'auto')
        data_dir: Data directory for geometry files (default: None)
        debug: If True, print debug information about coordinate extraction (default: False)
        use_barycenter: If True, calculate the barycenter of connecting points instead of using the given coordinate centers. This ensures each center point is the geometric center of its connecting points (default: False)
        use_first_only: If True, only use the first GBUCoordinateCenter for each GBU in the AM (default: False). Set to True to show only one instance per GBU type.
        **kwargs: Additional arguments passed to the render function
    
    Returns:
        Visualisation object (xyzrender.SVGResult or plotly.Figure)
    
    Raises:
        BackendNotAvailableError: If no backend is available
        InvalidGeometryError: If no coordinate data is available
    """
    if backend == 'auto':
        backend = 'xyzrender' if XYZRENDER_AVAILABLE else 'plotly'
    
    if backend == 'xyzrender':
        if not XYZRENDER_AVAILABLE:
            raise BackendNotAvailableError(
                "xyzrender is not available. Please install it: pip install xyzrender"
            )
        
        # Extract coordinates from AM (all constituent GBUs)
        coordinates = _extract_am_coordinates(am, debug=debug, use_barycenter=use_barycenter, use_first_only=use_first_only)
        
        if debug:
            print(f"DEBUG: Extracted {len(coordinates)} total coordinates for AM visualization")
        
        if coordinates:
            # For AMs, we need to handle multiple GBUs and multiple coordinate centers per GBU
            # Each coordinate center has its own center point + connecting points
            # We need to create center-to-CP bonds within each coordinate center grouping
            
            # The coordinates list is structured as:
            # [gbu1_gcc1_center, gbu1_gcc1_cp1, gbu1_gcc1_cp2, ..., gbu1_gcc2_center, gbu1_gcc2_cp1, ...,
            #  gbu2_gcc1_center, gbu2_gcc1_cp1, ...]
            
            # Calculate sizes by actually extracting the same way _extract_am_coordinates does
            gbus = list(am.hasGenericBuildingUnit)
            coordinate_center_sizes = []
            for gbu in gbus:
                gccs = list(gbu.hasGBUCoordinateCenter)
                gcc_list = [gccs[0]] if gccs and use_first_only else gccs
                for gcc in gcc_list:
                    cps = list(gcc.hasGBUConnectingPoint)
                    # Each coordinate center contributes 1 center + len(cps) connecting points
                    coordinate_center_sizes.append(1 + len(cps))
            
            # Create graph with proper bonding
            graph = _create_xyz_networkx_graph_with_gbu_structure(
                coordinates, coordinate_center_sizes
            )
            if graph is not None:
                # Use xyzrender with the graph directly (no pore detection for AMs)
                return _visualise_with_xyzrender_graph(graph, pore=False, **kwargs)
        
        # Fall back to plotly if no coordinates or graph creation failed
        if PLOTLY_AVAILABLE:
            return visualise_am_plotly(am, **kwargs)
        else:
            raise BackendNotAvailableError(
                "plotly is not available as fallback. Please install it: pip install plotly"
            )
    
    elif backend == 'plotly':
        if not PLOTLY_AVAILABLE:
            raise BackendNotAvailableError(
                "plotly is not available. Please install it: pip install plotly"
            )
        return visualise_am_plotly(am, **kwargs)
    
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'auto', 'xyzrender', or 'plotly'")


# ============================================================================
# Original Plotly Visualization Functions (Preserved as Fallback)
# ============================================================================

def _extract_atoms_data(obj) -> list:
    """Extract atom data from a MOP/CBU object for visualization."""
    try:
        geometry = list(obj.hasGeometry)[0]
    except (IndexError, AttributeError):
        raise InvalidGeometryError(f"Object {obj.instance_iri if hasattr(obj, 'instance_iri') else obj} has no geometry")
    
    if geometry.hasPoints is None:
        raise InvalidGeometryError(f"Geometry has no points loaded. Call load_geometry_from_fileserver() first.")
    
    atoms = []
    for pt in list(geometry.hasPoints):
        atoms.append({
            'label': pt.label,
            'x': pt.x,
            'y': pt.y,
            'z': pt.z
        })
    
    return atoms


def _extract_binding_sites_data(obj) -> list:
    """Extract binding site data from a MOP/CBU for visualization."""
    binding_sites = []
    
    try:
        for bs in list(obj.hasBindingSite):
            binding_sites.append({
                'label': 'BindingSite',
                'x': bs.binding_coordinates.x,
                'y': bs.binding_coordinates.y,
                'z': bs.binding_coordinates.z
            })
    except AttributeError:
        pass
    
    return binding_sites


def _extract_assembly_center(obj) -> Optional[dict]:
    """Extract assembly center from a MOP/CBU for visualization."""
    try:
        if hasattr(obj, 'assembly_center') and obj.assembly_center:
            return {
                'label': 'AssemblyCenter',
                'x': obj.assembly_center.x,
                'y': obj.assembly_center.y,
                'z': obj.assembly_center.z
            }
    except AttributeError:
        pass
    return None


def _extract_gbu_data(obj) -> list:
    """Extract GBU coordinate center and connecting point data from an AssemblyModel."""
    rows = []
    
    try:
        gbus = list(obj.hasGenericBuildingUnit)
        for gbu in gbus:
            # Handle case where gbu is a string IRI
            if isinstance(gbu, str):
                from twa.data_model.base_ontology import KnowledgeGraph
                gbu = KnowledgeGraph.get_object_from_lookup(gbu)
            
            # Handle case where hasGBUCoordinateCenter contains IRIs
            gccs = list(gbu.hasGBUCoordinateCenter)
            for gcc in gccs:
                if isinstance(gcc, str):
                    from twa.data_model.base_ontology import KnowledgeGraph
                    gcc = KnowledgeGraph.get_object_from_lookup(gcc)
                
                rows.append({
                    'label': gbu.gbu_type if hasattr(gbu, 'gbu_type') else 'GBU',
                    'iri': gcc.instance_iri,
                    'comment': str(gcc.rdfs_comment) if hasattr(gcc, 'rdfs_comment') else '',
                    'x': gcc.coordinates.x,
                    'y': gcc.coordinates.y,
                    'z': gcc.coordinates.z
                })
                
                # Handle connecting points
                cps = list(gcc.hasGBUConnectingPoint)
                for cp in cps:
                    if isinstance(cp, str):
                        from twa.data_model.base_ontology import KnowledgeGraph
                        cp = KnowledgeGraph.get_object_from_lookup(cp)
                    
                    rows.append({
                        'label': 'ConnectingPoint',
                        'iri': cp.instance_iri,
                        'comment': str(cp.rdfs_comment) if hasattr(cp, 'rdfs_comment') else '',
                        'x': cp.coordinates.x,
                        'y': cp.coordinates.y,
                        'z': cp.coordinates.z
                    })
    except AttributeError:
        pass
    
    return rows


def _extract_pore_data(obj) -> list:
    """Extract pore/cavity data from a MOP or AM for visualization."""
    pores = []
    
    try:
        # Check for hasCavity (MOP)
        if hasattr(obj, 'hasCavity') and obj.hasCavity:
            for cavity in list(obj.hasCavity):
                if hasattr(cavity, 'hasCenter'):
                    center = list(cavity.hasCenter)[0]
                    pores.append({
                        'label': 'Cavity',
                        'x': center.x if hasattr(center, 'x') else 0,
                        'y': center.y if hasattr(center, 'y') else 0,
                        'z': center.z if hasattr(center, 'z') else 0,
                        'radius': float(list(cavity.hasLargestInnerSphereDiameter)[0].hasValue.hasNumericalValue) / 2 if hasattr(cavity, 'hasLargestInnerSphereDiameter') else 1.0
                    })
        
        # Check for hasPoreRing (both MOP and AM)
        if hasattr(obj, 'hasPoreRing') and obj.hasPoreRing:
            for pore_ring in list(obj.hasPoreRing) or []:
                if hasattr(pore_ring, 'hasPoreRingCenter'):
                    center = list(pore_ring.hasPoreRingCenter)[0]
                    radius = 1.0
                    if hasattr(pore_ring, 'hasPoreDiameter'):
                        try:
                            diameter = list(pore_ring.hasPoreDiameter)[0]
                            if hasattr(diameter, 'hasValue'):
                                radius = float(list(diameter.hasValue)[0].hasNumericalValue) / 2
                        except (AttributeError, IndexError):
                            pass
                    pores.append({
                        'label': 'PoreRing',
                        'x': center.x if hasattr(center, 'x') else 0,
                        'y': center.y if hasattr(center, 'y') else 0,
                        'z': center.z if hasattr(center, 'z') else 0,
                        'radius': radius
                    })
    except (AttributeError, IndexError):
        pass
    
    return pores


def _calculate_barycenter(coordinates: List[Tuple[str, float, float, float]]) -> Tuple[float, float, float]:
    """Calculate the barycenter (geometric center) of a list of coordinates.
    
    Args:
        coordinates: List of coordinate tuples (element_label, x, y, z)
    
    Returns:
        Tuple of (x, y, z) representing the barycenter
    """
    if not coordinates:
        return (0.0, 0.0, 0.0)
    
    # Extract just the x, y, z values (ignore element labels)
    points = [(coord[1], coord[2], coord[3]) for coord in coordinates]
    
    # Calculate average of each dimension
    avg_x = sum(p[0] for p in points) / len(points)
    avg_y = sum(p[1] for p in points) / len(points)
    avg_z = sum(p[2] for p in points) / len(points)
    
    return (avg_x, avg_y, avg_z)


def _extract_gbu_coordinates(gbu, debug: bool = False, use_barycenter: bool = False, use_first_only: bool = True) -> List[Tuple[str, float, float, float]]:
    """Extract coordinate data from a GenericBuildingUnit for xyzrender visualization.
    
    Args:
        gbu: GenericBuildingUnit object
        debug: If True, print debug information about coordinate extraction
        use_barycenter: If True, calculate the barycenter of connecting points instead of using the given coordinate center
        use_first_only: If True, only use the first GBUCoordinateCenter (default: True). Set to False to use all coordinate centers.
    
    Returns:
        List of coordinate tuples (element_label, x, y, z)
    """
    coordinates = []
    
    try:
        # Add GBU coordinate center
        gccs = list(gbu.hasGBUCoordinateCenter)
        if debug:
            print(f"DEBUG: Found {len(gccs)} GBUCoordinateCenter(s) for GBU {getattr(gbu, 'instance_iri', 'unknown')}")
        
        # For GBU visualization, typically use only the first coordinate center
        # A GBU can have multiple coordinate centers if it appears in multiple positions in an assembly
        gcc_list = [gccs[0]] if gccs and use_first_only else gccs
        if debug and use_first_only and len(gccs) > 1:
            print(f"DEBUG: Using only first coordinate center (use_first_only=True)")
        
        for gcc in gcc_list:
            if isinstance(gcc, str):
                from twa.data_model.base_ontology import KnowledgeGraph
                gcc = KnowledgeGraph.get_object_from_lookup(gcc)
            
            # Extract connecting points first
            cps = list(gcc.hasGBUConnectingPoint)
            cp_coords = []
            if debug:
                print(f"DEBUG: Found {len(cps)} connecting point(s) for GCC {getattr(gcc, 'instance_iri', 'unknown')}")
            
            for cp in cps:
                if isinstance(cp, str):
                    from twa.data_model.base_ontology import KnowledgeGraph
                    cp = KnowledgeGraph.get_object_from_lookup(cp)
                
                cp_coords.append(('O', cp.coordinates.x, cp.coordinates.y, cp.coordinates.z))
            
            # Add coordinate center or barycenter
            if use_barycenter and cp_coords:
                # Calculate barycenter of connecting points
                barycenter = _calculate_barycenter(cp_coords)
                center_coord = ('C', barycenter[0], barycenter[1], barycenter[2])
                if debug:
                    original_center = (gcc.coordinates.x, gcc.coordinates.y, gcc.coordinates.z)
                    barycenter_only = barycenter
                    print(f"DEBUG: Original center: {original_center}")
                    print(f"DEBUG: Calculated barycenter of CPs: {barycenter_only}")
                    print(f"DEBUG: Distance between center and barycenter: {((original_center[0]-barycenter_only[0])**2 + (original_center[1]-barycenter_only[1])**2 + (original_center[2]-barycenter_only[2])**2)**0.5:.4f}")
            else:
                # Use the given coordinate center
                center_coord = ('C', gcc.coordinates.x, gcc.coordinates.y, gcc.coordinates.z)
            
            coordinates.append(center_coord)
            coordinates.extend(cp_coords)
                
        if debug:
            print(f"DEBUG: Total coordinates extracted: {len(coordinates)}")
            for i, coord in enumerate(coordinates):
                print(f"DEBUG:   {i}: {coord}")
    except AttributeError as e:
        if debug:
            print(f"DEBUG: AttributeError during coordinate extraction: {e}")
        pass
    
    return coordinates


def _extract_am_coordinates(am, debug: bool = False, use_barycenter: bool = False, use_first_only: bool = True) -> List[Tuple[str, float, float, float]]:
    """Extract coordinate data from an AssemblyModel for xyzrender visualization.
    
    Args:
        am: AssemblyModel object
        debug: If True, print debug information about coordinate extraction
        use_barycenter: If True, calculate the barycenter of connecting points instead of using the given coordinate centers
        use_first_only: If True, only use the first GBUCoordinateCenter for each GBU (default: True)
    
    Returns:
        List of coordinate tuples (element_label, x, y, z)
    """
    coordinates = []
    
    try:
        # Extract coordinates from all GBUs in the AM
        gbus = list(am.hasGenericBuildingUnit)
        if debug:
            print(f"DEBUG: Found {len(gbus)} GBU(s) in AM {getattr(am, 'instance_iri', 'unknown')}")
        
        for i, gbu in enumerate(gbus):
            if debug:
                print(f"DEBUG: Extracting coordinates from GBU {i}")
            gbu_coords = _extract_gbu_coordinates(gbu, debug=debug, use_barycenter=use_barycenter, use_first_only=use_first_only)
            coordinates.extend(gbu_coords)
        
        # Also add pore ring centers if available
        if hasattr(am, 'hasPoreRing') and am.hasPoreRing:
            pore_rings = list(am.hasPoreRing) or []
            if debug:
                print(f"DEBUG: Found {len(pore_rings)} pore ring(s)")
            for pore_ring in pore_rings:
                if hasattr(pore_ring, 'hasPoreRingCenter'):
                    center = list(pore_ring.hasPoreRingCenter)[0]
                    coordinates.append(('P', center.x, center.y, center.z))
                    if debug:
                        print(f"DEBUG: Added pore ring center at ({center.x}, {center.y}, {center.z})")
        
        if debug:
            print(f"DEBUG: Total AM coordinates extracted: {len(coordinates)}")
    except AttributeError as e:
        if debug:
            print(f"DEBUG: AttributeError during AM coordinate extraction: {e}")
        pass
    
    return coordinates


def visualise_mop_plotly(
    mop,
    show_atoms: bool = True,
    show_binding_sites: bool = True,
    show_assembly_center: bool = True,
    width: int = 1200,
    height: int = 800,
    **kwargs
) -> Any:
    """Visualize a MetalOrganicPolyhedron using Plotly (fallback).
    
    This function creates a 3D scatter plot of a MOP with:
    - Atoms (colored by element)
    - Binding sites
    - Assembly center
    
    Note: Pores are not shown in Plotly backend due to limitations.
    
    Args:
        mop: MetalOrganicPolyhedron object to visualize
        show_atoms: Whether to show atoms (default: True)
        show_binding_sites: Whether to show binding sites (default: True)
        show_assembly_center: Whether to show assembly center (default: True)
        width: Figure width in pixels (default: 1200)
        height: Figure height in pixels (default: 800)
        **kwargs: Additional arguments passed to px.scatter_3d
    
    Returns:
        plotly.graph_objects.Figure object
    
    Raises:
        BackendNotAvailableError: If plotly is not installed
        InvalidGeometryError: If geometry data is missing
    """
    if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
        raise BackendNotAvailableError(
            "plotly or pandas is not available. Please install: pip install plotly pandas"
        )
    
    rows = []
    
    # Extract atom data
    if show_atoms:
        atoms = _extract_atoms_data(mop)
        for atom in atoms:
            rows.append({
                'Label': atom['label'],
                'IRI': '',
                'Type': 'Atom',
                'X': atom['x'],
                'Y': atom['y'],
                'Z': atom['z']
            })
    
    # Extract binding sites
    if show_binding_sites:
        binding_sites = _extract_binding_sites_data(mop)
        for bs in binding_sites:
            rows.append({
                'Label': bs['label'],
                'IRI': '',
                'Type': 'BindingSite',
                'X': bs['x'],
                'Y': bs['y'],
                'Z': bs['z']
            })
    
    # Extract assembly center
    if show_assembly_center:
        center = _extract_assembly_center(mop)
        if center:
            rows.append({
                'Label': center['label'],
                'IRI': '',
                'Type': 'AssemblyCenter',
                'X': center['x'],
                'Y': center['y'],
                'Z': center['z']
            })
    
    if not rows:
        raise InvalidGeometryError("No data to visualize")
    
    df = pd.DataFrame(rows)
    
    # Create title
    try:
        title = f'MOP: {list(mop.hasMOPFormula)[0]}\n'
        title += f'AM: {list(mop.hasAssemblyModel)[0].instance_iri}'
    except (AttributeError, IndexError):
        title = 'MOP Visualization'
    
    fig = px.scatter_3d(
        df,
        x='X',
        y='Y',
        z='Z',
        color='Type',
        hover_data=['Label', 'IRI'],
        title=title,
        **kwargs
    )
    
    fig.update_traces(marker=dict(size=2))
    fig.update_layout(
        autosize=False,
        width=width,
        height=height,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        )
    )
    
    return fig


def visualise_cbu_plotly(
    cbu,
    show_atoms: bool = True,
    show_binding_sites: bool = True,
    show_assembly_center: bool = True,
    width: int = 1200,
    height: int = 400,
    **kwargs
) -> Any:
    """Visualize a ChemicalBuildingUnit using Plotly (fallback).
    
    Args:
        cbu: ChemicalBuildingUnit object to visualize
        show_atoms: Whether to show atoms (default: True)
        show_binding_sites: Whether to show binding sites (default: True)
        show_assembly_center: Whether to show assembly center (default: True)
        width: Figure width in pixels (default: 1200)
        height: Figure height in pixels (default: 400)
        **kwargs: Additional arguments passed to px.scatter_3d
    
    Returns:
        plotly.graph_objects.Figure object
    """
    if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
        raise BackendNotAvailableError(
            "plotly or pandas is not available. Please install: pip install plotly pandas"
        )
    
    rows = []
    
    # Extract atom data
    if show_atoms:
        atoms = _extract_atoms_data(cbu)
        for atom in atoms:
            rows.append({
                'Atom': atom['label'],
                'Type': 'Atom',
                'X': atom['x'],
                'Y': atom['y'],
                'Z': atom['z']
            })
    
    # Extract binding sites
    if show_binding_sites:
        binding_sites = _extract_binding_sites_data(cbu)
        for bs in binding_sites:
            rows.append({
                'Atom': bs['label'],
                'Type': 'BindingSite',
                'X': bs['x'],
                'Y': bs['y'],
                'Z': bs['z']
            })
    
    # Extract assembly center
    if show_assembly_center:
        center = _extract_assembly_center(cbu)
        if center:
            rows.append({
                'Atom': center['label'],
                'Type': 'AssemblyCenter',
                'X': center['x'],
                'Y': center['y'],
                'Z': center['z']
            })
    
    if not rows:
        raise InvalidGeometryError("No data to visualize")
    
    df = pd.DataFrame(rows)
    
    # Create title
    try:
        title = f'CBU: {list(cbu.hasCBUFormula)[0]}'
    except (AttributeError, IndexError):
        title = 'CBU Visualization'
    
    fig = px.scatter_3d(
        df,
        x='X',
        y='Y',
        z='Z',
        color='Type',
        hover_data=['Atom'],
        title=title,
        **kwargs
    )
    
    fig.update_traces(marker=dict(size=2))
    fig.update_layout(
        autosize=False,
        width=width,
        height=height,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        )
    )
    
    return fig


def visualise_am_plotly(
    am,
    width: int = 1200,
    height: int = 800,
    **kwargs
) -> Any:
    """Visualize an AssemblyModel using Plotly (fallback).
    
    Args:
        am: AssemblyModel object to visualize
        width: Figure width in pixels (default: 1200)
        height: Figure height in pixels (default: 800)
        **kwargs: Additional arguments passed to px.scatter_3d
    
    Returns:
        plotly.graph_objects.Figure object
    """
    if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
        raise BackendNotAvailableError(
            "plotly or pandas is not available. Please install: pip install plotly pandas"
        )
    
    # Extract GBU data
    gbu_data = _extract_gbu_data(am)
    
    if not gbu_data:
        raise InvalidGeometryError("No GBU data to visualize")
    
    rows = []
    for item in gbu_data:
        rows.append({
            'Label': item['label'],
            'IRI': item['iri'],
            'Comment': item['comment'],
            'Type': item['label'],
            'X': item['x'],
            'Y': item['y'],
            'Z': item['z']
        })
    
    df = pd.DataFrame(rows)
    
    # Create title
    try:
        title = f'AM: {am.instance_iri}'
    except AttributeError:
        title = 'AssemblyModel Visualization'
    
    fig = px.scatter_3d(
        df,
        x='X',
        y='Y',
        z='Z',
        color='Type',
        hover_data=['Label', 'IRI', 'Comment'],
        title=title,
        **kwargs
    )
    
    fig.update_traces(marker=dict(size=5))
    fig.update_layout(
        autosize=False,
        width=width,
        height=height,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        )
    )
    
    return fig


def visualise_gbu_plotly(
    gbu,
    width: int = 1200,
    height: int = 800,
    **kwargs
) -> Any:
    """Visualize a GenericBuildingUnit using Plotly (fallback).
    
    Args:
        gbu: GenericBuildingUnit object to visualize
        width: Figure width in pixels (default: 1200)
        height: Figure height in pixels (default: 800)
        **kwargs: Additional arguments passed to px.scatter_3d
    
    Returns:
        plotly.graph_objects.Figure object
    """
    if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
        raise BackendNotAvailableError(
            "plotly or pandas is not available. Please install: pip install plotly pandas"
        )
    
    # Extract coordinates from GBU
    coordinates = _extract_gbu_coordinates(gbu)
    
    if not coordinates:
        raise InvalidGeometryError("No GBU coordinate data to visualize")
    
    rows = []
    for element, x, y, z in coordinates:
        rows.append({
            'Label': element,
            'Type': 'CoordinateCenter' if element == 'C' else 'ConnectingPoint',
            'X': x,
            'Y': y,
            'Z': z
        })
    
    df = pd.DataFrame(rows)
    
    # Create title
    try:
        title = f'GBU: {gbu.instance_iri}'
    except AttributeError:
        title = 'GenericBuildingUnit Visualization'
    
    fig = px.scatter_3d(
        df,
        x='X',
        y='Y',
        z='Z',
        color='Type',
        hover_data=['Label'],
        title=title,
        **kwargs
    )
    
    fig.update_traces(marker=dict(size=8))
    fig.update_layout(
        autosize=False,
        width=width,
        height=height,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        )
    )
    
    return fig


# ============================================================================
# Module Exports
# ============================================================================

# Backend-specific functions for direct backend access
def visualise_gbu_xyzrender(gbu, data_dir: Optional[str] = None, **kwargs) -> Any:
    """Visualise a GenericBuildingUnit using xyzrender backend.
    
    Args:
        gbu: GenericBuildingUnit object to visualise
        data_dir: Data directory for geometry files (default: None)
        **kwargs: Additional arguments passed to xyzrender.render()
    
    Returns:
        xyzrender SVGResult object
    
    Raises:
        BackendNotAvailableError: If xyzrender is not available
        InvalidGeometryError: If no coordinate data is available
    """
    return visualise_gbu(gbu, backend='xyzrender', data_dir=data_dir, **kwargs)


def visualise_am_xyzrender(am, data_dir: Optional[str] = None, **kwargs) -> Any:
    """Visualise an AssemblyModel using xyzrender backend.
    
    Args:
        am: AssemblyModel object to visualise
        data_dir: Data directory for geometry files (default: None)
        **kwargs: Additional arguments passed to xyzrender.render()
    
    Returns:
        xyzrender SVGResult object
    
    Raises:
        BackendNotAvailableError: If xyzrender is not available
        InvalidGeometryError: If no coordinate data is available
    """
    return visualise_am(am, backend='xyzrender', data_dir=data_dir, **kwargs)


def visualise_mop_xyzrender(mop, data_dir: Optional[str] = None, **kwargs) -> Any:
    """Visualise a MetalOrganicPolyhedron using xyzrender backend.
    
    Args:
        mop: MetalOrganicPolyhedron object to visualise
        data_dir: Data directory for geometry files (default: None)
        **kwargs: Additional arguments passed to xyzrender.render()
    
    Returns:
        xyzrender SVGResult object
    
    Raises:
        BackendNotAvailableError: If xyzrender is not available
        InvalidGeometryError: If geometry data is missing
    """
    return visualise_mop(mop, backend='xyzrender', data_dir=data_dir, **kwargs)


def visualise_cbu_xyzrender(cbu, data_dir: Optional[str] = None, **kwargs) -> Any:
    """Visualise a ChemicalBuildingUnit using xyzrender backend.
    
    Args:
        cbu: ChemicalBuildingUnit object to visualise
        data_dir: Data directory for geometry files (default: None)
        **kwargs: Additional arguments passed to xyzrender.render()
    
    Returns:
        xyzrender SVGResult object
    
    Raises:
        BackendNotAvailableError: If xyzrender is not available
        InvalidGeometryError: If geometry data is missing
    """
    return visualise_cbu(cbu, backend='xyzrender', data_dir=data_dir, **kwargs)


def visualise_with_xyzrender(file_path: str, pore: bool = False, **kwargs) -> Any:
    """Visualise an XYZ file using xyzrender directly.
    
    Args:
        file_path: Path to XYZ file to visualise
        pore: Whether to enable pore detection (default: False)
        **kwargs: Additional arguments passed to xyzrender.render()
    
    Returns:
        xyzrender SVGResult object
    
    Raises:
        BackendNotAvailableError: If xyzrender is not available
        FileNotFoundError: If the XYZ file doesn't exist
    """
    return _visualise_with_xyzrender(file_path, pore=pore, **kwargs)


def visualise_with_plotly(obj, **kwargs) -> Any:
    """Visualise an object using plotly backend directly.
    
    Args:
        obj: Object to visualise (MOP, CBU, AM, or GBU)
        **kwargs: Additional arguments passed to the plotly visualization function
    
    Returns:
        plotly.graph_objects.Figure object
    
    Raises:
        BackendNotAvailableError: If plotly is not available
        InvalidGeometryError: If geometry data is missing
    """
    # Determine object type and call appropriate plotly function
    if hasattr(obj, 'hasGeometry') and hasattr(obj, 'hasChemicalBuildingUnit'):
        # MOP
        return visualise_mop_plotly(obj, **kwargs)
    elif hasattr(obj, 'hasGeometry') and hasattr(obj, 'hasCBUFormula'):
        # CBU
        return visualise_cbu_plotly(obj, **kwargs)
    elif hasattr(obj, 'hasGenericBuildingUnit'):
        # AM
        return visualise_am_plotly(obj, **kwargs)
    elif hasattr(obj, 'hasGBUCoordinateCenter'):
        # GBU
        return visualise_gbu_plotly(obj, **kwargs)
    else:
        raise ValueError(f"Unknown object type: {type(obj)}")


__all__ = [
    # Exceptions
    'VisualizationError',
    'BackendNotAvailableError',
    'InvalidGeometryError',
    
    # Main visualisation functions
    'visualise_mop',
    'visualise_cbu',
    'visualise_gbu',
    'visualise_am',
    
    # Backend-specific functions (xyzrender)
    'visualise_mop_xyzrender',
    'visualise_cbu_xyzrender',
    'visualise_gbu_xyzrender',
    'visualise_am_xyzrender',
    'visualise_with_xyzrender',
    
    # Backend-specific functions (plotly fallback)
    'visualise_mop_plotly',
    'visualise_cbu_plotly',
    'visualise_gbu_plotly',
    'visualise_am_plotly',
    'visualise_with_plotly',
    
    # Internal utilities
    '_get_xyz_file_path_from_geometry',
    '_visualise_with_xyzrender',
    '_visualise_with_xyzrender_graph',
    '_extract_gbu_coordinates',
    '_extract_am_coordinates',
    '_create_xyz_networkx_graph',
    '_create_xyz_networkx_graph_with_gbu_structure',
]
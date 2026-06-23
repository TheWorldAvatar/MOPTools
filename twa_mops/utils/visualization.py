"""Visualization utilities for MOPTools.

This module provides simple visualization functions that use xyzrender for
interactive 3D visualization with automatic pore detection for MOPs.
Plotly functions are preserved as fallback for when xyzrender is not available.

The xyzrender backend provides better performance and more features for
visualizing molecular structures and automatically detects pores in MOPs.
"""

from typing import Optional, Any
import os

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


def visualise_am(am, backend: str = 'auto', data_dir: Optional[str] = None, **kwargs) -> Any:
    """Visualise an AssemblyModel.
    
    Uses xyzrender if available (preferred), falls back to plotly.
    Note: AssemblyModels don't have XYZ files directly, so this uses the plotly fallback.
    
    Args:
        am: AssemblyModel object to visualise
        backend: Backend to use ('auto', 'xyzrender', 'plotly') (default: 'auto')
        data_dir: Data directory for geometry files (default: None)
        **kwargs: Additional arguments passed to the render function
    
    Returns:
        Visualisation object (xyzrender.SVGResult or plotly.Figure)
    
    Raises:
        BackendNotAvailableError: If no backend is available
    """
    # AssemblyModels don't have XYZ files, so use plotly
    if backend == 'auto':
        backend = 'plotly'  # AMs need special handling
    
    if backend == 'xyzrender':
        # For AMs, we could try to extract coordinates and create a networkx graph
        # but for now, just use plotly
        if PLOTLY_AVAILABLE:
            return visualise_am_plotly(am, **kwargs)
        else:
            raise BackendNotAvailableError(
                "plotly is not available. Please install it: pip install plotly"
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


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Exceptions
    'VisualizationError',
    'BackendNotAvailableError',
    'InvalidGeometryError',
    
    # Main visualisation functions
    'visualise_mop',
    'visualise_cbu',
    'visualise_am',
    
    # Backend-specific functions (plotly fallback)
    'visualise_mop_plotly',
    'visualise_cbu_plotly',
    'visualise_am_plotly',
    
    # Internal utilities
    '_get_xyz_file_path_from_geometry',
    '_visualise_with_xyzrender',
]
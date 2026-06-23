"""Visualization utilities for MOPTools.

This module provides visualization functions for Metal-Organic Polyhedrons,
Chemical Building Units, and Assembly Models using either:
1. xyzrender library (preferred) - for interactive 3D visualization
2. Plotly (fallback) - for basic 3D scatter plots

The xyzrender backend provides better performance and more features for
visualizing molecular structures and pores.
"""

from typing import Optional, List, Dict, Any, Union
import os
import warnings

# Try to import xyzrender and networkx
try:
    import xyzrender
    import networkx as nx
    XYZRENDER_AVAILABLE = True
except ImportError:
    XYZRENDER_AVAILABLE = False
    nx = None

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


def _check_backend_availability():
    """Check if at least one visualization backend is available."""
    if not XYZRENDER_AVAILABLE and not PLOTLY_AVAILABLE:
        raise BackendNotAvailableError(
            "Neither xyzrender nor plotly is available for visualization. "
            "Please install at least one: "
            "pip install xyzrender or pip install plotly"
        )


def _extract_atoms_data(obj) -> List[Dict[str, Any]]:
    """Extract atom data from a MOP/CBU/AM object for visualization.
    
    Args:
        obj: Object with hasGeometry property (ChemicalBuildingUnit or MetalOrganicPolyhedron)
    
    Returns:
        List of dictionaries with atom data: label, x, y, z
    
    Raises:
        InvalidGeometryError: If geometry data is missing or invalid
    """
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


def _extract_binding_sites_data(obj) -> List[Dict[str, Any]]:
    """Extract binding site data from a MOP/CBU for visualization.
    
    Args:
        obj: Object with hasBindingSite property
    
    Returns:
        List of dictionaries with binding site data: label, x, y, z
    """
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


def _extract_assembly_center(obj) -> Optional[Dict[str, Any]]:
    """Extract assembly center from a MOP/CBU for visualization.
    
    Args:
        obj: Object with assembly_center property
    
    Returns:
        Dictionary with assembly center data or None
    """
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


def _extract_gbu_data(obj) -> List[Dict[str, Any]]:
    """Extract GBU coordinate center and connecting point data from an AssemblyModel.
    
    Args:
        obj: AssemblyModel object
    
    Returns:
        List of dictionaries with GBU data: label, iri, comment, x, y, z
    """
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


def _extract_pore_data(obj) -> List[Dict[str, Any]]:
    """Extract pore/cavity data from a MOP or AM for visualization.
    
    Args:
        obj: MetalOrganicPolyhedron or AssemblyModel object
    
    Returns:
        List of dictionaries with pore data: label, x, y, z, radius
    """
    pores = []
    
    try:
        # Check for hasCavity (MOP)
        if hasattr(obj, 'hasCavity') and obj.hasCavity:
            for cavity in list(obj.hasCavity):
                # Try to get center coordinates from cavity
                # This is a placeholder - actual pore center calculation may vary
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
                # Extract pore ring center and radius
                if hasattr(pore_ring, 'hasPoreRingCenter'):
                    center = list(pore_ring.hasPoreRingCenter)[0]
                    # Try to get diameter if available
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


# ============================================================================
# Main Visualization Functions
# ============================================================================


def visualise_mop_xyzrender(
    mop,
    show_atoms: bool = True,
    show_binding_sites: bool = True,
    show_assembly_center: bool = True,
    show_pores: bool = True,
    color_scheme: str = 'default',
    atom_radius: float = 0.2,
    binding_site_radius: float = 0.3,
    pore_radius_scale: float = 1.0,
    **kwargs
) -> Any:
    """Visualise a MetalOrganicPolyhedron using xyzrender library.
    
    This function creates an interactive 3D visualization of a MOP with:
    - Atoms (colored by element)
    - Binding sites
    - Assembly center
    - Pores/cavities (as spheres)
    
    Note: Uses xyzrender's Molecule and render() API with networkx graphs.
    
    Args:
        mop: MetalOrganicPolyhedron object to visualize
        show_atoms: Whether to show atoms (default: True)
        show_binding_sites: Whether to show binding sites (default: True)
        show_assembly_center: Whether to show assembly center (default: True)
        show_pores: Whether to show pores/cavities (default: True)
        color_scheme: Color scheme for atoms (default: 'default')
        atom_radius: Radius of atom spheres (default: 0.2)
        binding_site_radius: Radius of binding site spheres (default: 0.3)
        pore_radius_scale: Scale factor for pore/cavity spheres (default: 1.0)
        **kwargs: Currently unused (reserved for future xyzrender API compatibility)
    
    Returns:
        xyzrender Molecule or render result (depends on environment)
    
    Raises:
        BackendNotAvailableError: If xyzrender or networkx is not installed
        InvalidGeometryError: If geometry data is missing
    """
    if not XYZRENDER_AVAILABLE or nx is None:
        raise BackendNotAvailableError(
            "xyzrender or networkx is not available. Please install: pip install xyzrender networkx"
        )
    
    # Create a networkx graph for all visualization data
    # xyzrender expects node attributes: 'symbol' (element) and 'position' ([x, y, z])
    G = nx.Graph()
    node_id = 0
    
    # Extract atom data
    if show_atoms:
        atoms = _extract_atoms_data(mop)
        for atom in atoms:
            G.add_node(node_id, 
                      symbol=atom['label'],
                      position=[atom['x'], atom['y'], atom['z']])
            node_id += 1
    
    # Extract binding sites
    if show_binding_sites:
        binding_sites = _extract_binding_sites_data(mop)
        for bs in binding_sites:
            G.add_node(node_id,
                       symbol='X',
                       position=[bs['x'], bs['y'], bs['z']])
            node_id += 1
    
    # Extract assembly center
    if show_assembly_center:
        center = _extract_assembly_center(mop)
        if center:
            G.add_node(node_id,
                       symbol='X',
                       position=[center['x'], center['y'], center['z']])
            node_id += 1
    
    # Extract and add pores as special nodes
    if show_pores:
        pores = _extract_pore_data(mop)
        for pore in pores:
            G.add_node(node_id,
                       symbol='X',
                       position=[pore['x'], pore['y'], pore['z']])
            node_id += 1
    
    if len(G.nodes()) == 0:
        raise InvalidGeometryError("No data to visualize")
    
    # Create Molecule from graph
    mol = xyzrender.Molecule(graph=G)
    
    # Render the molecule - in Jupyter this will display inline via SVGResult._repr_svg_()
    # In non-Jupyter environments, this returns an SVGResult that can be saved or displayed
    # Note: We don't pass our custom kwargs to xyzrender.render() as they are not part of the API
    return xyzrender.render(mol)


def visualise_mop_plotly(
    mop,
    show_atoms: bool = True,
    show_binding_sites: bool = True,
    show_assembly_center: bool = True,
    show_pores: bool = False,
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
        show_pores: Whether to show pores (not implemented in Plotly, default: False)
        width: Figure width in pixels (default: 1200)
        height: Figure height in pixels (default: 800)
        **kwargs: Additional arguments passed to px.scatter_3d
    
    Returns:
        plotly.graph_objects.Figure object (can be displayed with .show())
    
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


def visualise_cbu_xyzrender(
    cbu,
    show_atoms: bool = True,
    show_binding_sites: bool = True,
    show_assembly_center: bool = True,
    color_scheme: str = 'default',
    atom_radius: float = 0.2,
    binding_site_radius: float = 0.3,
    **kwargs
) -> Any:
    """Visualize a ChemicalBuildingUnit using xyzrender library.
    
    Note: Uses xyzrender's Molecule and render() API with networkx graphs.
    
    Args:
        cbu: ChemicalBuildingUnit object to visualize
        show_atoms: Whether to show atoms (default: True)
        show_binding_sites: Whether to show binding sites (default: True)
        show_assembly_center: Whether to show assembly center (default: True)
        color_scheme: Color scheme for atoms (default: 'default')
        atom_radius: Radius of atom spheres (default: 0.2)
        binding_site_radius: Radius of binding site spheres (default: 0.3)
        **kwargs: Currently unused (reserved for future xyzrender API compatibility)
    
    Returns:
        xyzrender Molecule object
    
    Raises:
        BackendNotAvailableError: If xyzrender or networkx is not installed
        InvalidGeometryError: If geometry data is missing
    """
    if not XYZRENDER_AVAILABLE or nx is None:
        raise BackendNotAvailableError(
            "xyzrender or networkx is not available. Please install: pip install xyzrender networkx"
        )
    
    # Create a networkx graph for all visualization data
    # xyzrender expects node attributes: 'symbol' (element) and 'position' ([x, y, z])
    G = nx.Graph()
    node_id = 0
    
    # Extract atom data
    if show_atoms:
        atoms = _extract_atoms_data(cbu)
        for atom in atoms:
            G.add_node(node_id, 
                      symbol=atom['label'],
                      position=[atom['x'], atom['y'], atom['z']])
            node_id += 1
    
    # Extract binding sites
    if show_binding_sites:
        binding_sites = _extract_binding_sites_data(cbu)
        for bs in binding_sites:
            G.add_node(node_id,
                       symbol='X',
                       position=[bs['x'], bs['y'], bs['z']])
            node_id += 1
    
    # Extract assembly center
    if show_assembly_center:
        center = _extract_assembly_center(cbu)
        if center:
            G.add_node(node_id,
                       symbol='X',
                       position=[center['x'], center['y'], center['z']])
            node_id += 1
    
    if len(G.nodes()) == 0:
        raise InvalidGeometryError("No data to visualize")
    
    # Create Molecule from graph
    mol = xyzrender.Molecule(graph=G)
    
    # Render the molecule - in Jupyter this will display inline via SVGResult._repr_svg_()
    # Note: We don't pass our custom kwargs to xyzrender.render() as they are not part of the API
    return xyzrender.render(mol)


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


def visualise_am_xyzrender(
    am,
    show_pores: bool = True,
    color_scheme: str = 'default',
    gbu_radius: float = 0.3,
    cp_radius: float = 0.2,
    pore_radius_scale: float = 1.0,
    **kwargs
) -> Any:
    """Visualize an AssemblyModel using xyzrender library.
    
    Shows GBU coordinate centers, connecting points, and optionally pores.
    
    Note: Uses xyzrender's Molecule and render() API with networkx graphs.
    
    Args:
        am: AssemblyModel object to visualize
        show_pores: Whether to show pores/pore rings (default: True)
        color_scheme: Color scheme (default: 'default')
        gbu_radius: Radius of GBU center spheres (default: 0.3)
        cp_radius: Radius of connecting point spheres (default: 0.2)
        pore_radius_scale: Scale factor for pore radii (default: 1.0)
        **kwargs: Currently unused (reserved for future xyzrender API compatibility)
    
    Returns:
        xyzrender Molecule object
    """
    if not XYZRENDER_AVAILABLE or nx is None:
        raise BackendNotAvailableError(
            "xyzrender or networkx is not available. Please install: pip install xyzrender networkx"
        )
    
    # Create a networkx graph for all visualization data
    # xyzrender expects node attributes: 'symbol' and 'position' ([x, y, z])
    G = nx.Graph()
    node_id = 0
    
    # Extract GBU data
    gbu_data = _extract_gbu_data(am)
    
    if gbu_data:
        for item in gbu_data:
            if 'ConnectingPoint' in item['label']:
                # Connecting points - use green color via symbol
                G.add_node(node_id,
                           symbol='Cl',  # Chlorine is green-ish, or use custom
                           position=[item['x'], item['y'], item['z']])
            else:
                # GBU centers - use a distinctive symbol
                G.add_node(node_id,
                           symbol='Br',  # Bromine is brown-ish
                           position=[item['x'], item['y'], item['z']])
            node_id += 1
    
    # Extract and show pores
    if show_pores:
        pores = _extract_pore_data(am)
        if pores:
            for pore in pores:
                # Use a distinctive symbol for pores
                G.add_node(node_id,
                           symbol='He',  # Helium is light
                           position=[pore['x'], pore['y'], pore['z']])
                node_id += 1
    
    if len(G.nodes()) == 0:
        raise InvalidGeometryError("No GBU data to visualize")
    
    # Create Molecule from graph
    mol = xyzrender.Molecule(graph=G)
    
    # Render the molecule - in Jupyter this will display inline via SVGResult._repr_svg_()
    # Note: We don't pass our custom kwargs to xyzrender.render() as they are not part of the API
    return xyzrender.render(mol)


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
# Unified Visualization Functions (Auto-select backend)
# ============================================================================


def visualise_mop(
    mop,
    show_pores: bool = True,
    backend: str = 'auto',
    **kwargs
) -> Any:
    """Visualise a MetalOrganicPolyhedron.
    
    Automatically selects the best available backend (xyzrender preferred, 
    plotly as fallback). Can also explicitly specify the backend.
    
    Args:
        mop: MetalOrganicPolyhedron object to visualise
        show_pores: Whether to show pores/cavities (default: True)
                    Note: Only works with xyzrender backend
        backend: Backend to use ('auto', 'xyzrender', 'plotly') (default: 'auto')
        **kwargs: Additional arguments passed to the specific backend function
    
    Returns:
        Visualisation object (xyzrender.SVGResult or plotly.Figure)
    
    Raises:
        BackendNotAvailableError: If no backend is available
    """
    _check_backend_availability()
    
    if backend == 'auto':
        # Prefer xyzrender if available
        if XYZRENDER_AVAILABLE:
            return visualise_mop_xyzrender(mop, show_pores=show_pores, **kwargs)
        else:
            return visualise_mop_plotly(mop, show_pores=False, **kwargs)
    elif backend == 'xyzrender':
        if not XYZRENDER_AVAILABLE:
            raise BackendNotAvailableError(
                "xyzrender is not available. Please install it: pip install xyzrender"
            )
        return visualise_mop_xyzrender(mop, show_pores=show_pores, **kwargs)
    elif backend == 'plotly':
        if not PLOTLY_AVAILABLE:
            raise BackendNotAvailableError(
                "plotly is not available. Please install it: pip install plotly"
            )
        return visualise_mop_plotly(mop, show_pores=False, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'auto', 'xyzrender', or 'plotly'")


def visualise_cbu(
    cbu,
    backend: str = 'auto',
    **kwargs
) -> Any:
    """Visualise a ChemicalBuildingUnit.
    
    Automatically selects the best available backend.
    
    Args:
        cbu: ChemicalBuildingUnit object to visualise
        backend: Backend to use ('auto', 'xyzrender', 'plotly') (default: 'auto')
        **kwargs: Additional arguments passed to the specific backend function
    
    Returns:
        Visualisation object (xyzrender.SVGResult or plotly.Figure)
    """
    _check_backend_availability()
    
    if backend == 'auto':
        if XYZRENDER_AVAILABLE:
            return visualise_cbu_xyzrender(cbu, **kwargs)
        else:
            return visualise_cbu_plotly(cbu, **kwargs)
    elif backend == 'xyzrender':
        if not XYZRENDER_AVAILABLE:
            raise BackendNotAvailableError(
                "xyzrender is not available. Please install it: pip install xyzrender"
            )
        return visualise_cbu_xyzrender(cbu, **kwargs)
    elif backend == 'plotly':
        if not PLOTLY_AVAILABLE:
            raise BackendNotAvailableError(
                "plotly is not available. Please install it: pip install plotly"
            )
        return visualise_cbu_plotly(cbu, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'auto', 'xyzrender', or 'plotly'")


def visualise_am(
    am,
    show_pores: bool = True,
    backend: str = 'auto',
    **kwargs
) -> Any:
    """Visualise an AssemblyModel.
    
    Automatically selects the best available backend.
    
    Args:
        am: AssemblyModel object to visualise
        show_pores: Whether to show pores/pore rings (default: True, only works with xyzrender)
        backend: Backend to use ('auto', 'xyzrender', 'plotly') (default: 'auto')
        **kwargs: Additional arguments passed to the specific backend function
    
    Returns:
        Visualisation object (xyzrender.SVGResult or plotly.Figure)
    """
    _check_backend_availability()
    
    if backend == 'auto':
        if XYZRENDER_AVAILABLE:
            return visualise_am_xyzrender(am, show_pores=show_pores, **kwargs)
        else:
            return visualise_am_plotly(am, **kwargs)
    elif backend == 'xyzrender':
        if not XYZRENDER_AVAILABLE:
            raise BackendNotAvailableError(
                "xyzrender is not available. Please install it: pip install xyzrender"
            )
        return visualise_am_xyzrender(am, show_pores=show_pores, **kwargs)
    elif backend == 'plotly':
        if not PLOTLY_AVAILABLE:
            raise BackendNotAvailableError(
                "plotly is not available. Please install it: pip install plotly"
            )
        return visualise_am_plotly(am, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'auto', 'xyzrender', or 'plotly'")


# ============================================================================
# Convenience Functions for Backward Compatibility
# ============================================================================


def visualise_with_xyzrender(obj, **kwargs) -> Any:
    """Visualise any object using xyzrender (preferred backend).
    
    This function automatically detects the object type and uses the
    appropriate xyzrender visualisation function.
    
    Args:
        obj: Object to visualise (MOP, CBU, or AM)
        **kwargs: Additional arguments passed to the specific visualisation function
    
    Returns:
        xyzrender SVGResult object
    
    Raises:
        BackendNotAvailableError: If xyzrender is not available
        ValueError: If object type is not recognized
    """
    from twa_mops.core.ontomops import MetalOrganicPolyhedron, ChemicalBuildingUnit, AssemblyModel
    
    if isinstance(obj, MetalOrganicPolyhedron):
        return visualise_mop_xyzrender(obj, **kwargs)
    elif isinstance(obj, ChemicalBuildingUnit):
        return visualise_cbu_xyzrender(obj, **kwargs)
    elif isinstance(obj, AssemblyModel):
        return visualise_am_xyzrender(obj, **kwargs)
    else:
        raise ValueError(f"Unsupported object type: {type(obj)}")


def visualise_with_plotly(obj, **kwargs) -> Any:
    """Visualise any object using Plotly (fallback backend).
    
    This function automatically detects the object type and uses the
    appropriate Plotly visualisation function.
    
    Args:
        obj: Object to visualise (MOP, CBU, or AM)
        **kwargs: Additional arguments passed to the specific visualisation function
    
    Returns:
        plotly Figure object
    
    Raises:
        BackendNotAvailableError: If plotly is not available
        ValueError: If object type is not recognized
    """
    from twa_mops.core.ontomops import MetalOrganicPolyhedron, ChemicalBuildingUnit, AssemblyModel
    
    if isinstance(obj, MetalOrganicPolyhedron):
        return visualise_mop_plotly(obj, **kwargs)
    elif isinstance(obj, ChemicalBuildingUnit):
        return visualise_cbu_plotly(obj, **kwargs)
    elif isinstance(obj, AssemblyModel):
        return visualise_am_plotly(obj, **kwargs)
    else:
        raise ValueError(f"Unsupported object type: {type(obj)}")


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
    
    # Backend-specific functions
    'visualise_mop_xyzrender',
    'visualise_mop_plotly',
    'visualise_cbu_xyzrender',
    'visualise_cbu_plotly',
    'visualise_am_xyzrender',
    'visualise_am_plotly',
    
    # Convenience functions
    'visualise_with_xyzrender',
    'visualise_with_plotly',
]

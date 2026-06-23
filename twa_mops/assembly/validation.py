"""Validation for MOP assembly components.

This module provides validation functions for Chemical Building Units (CBUs),
Assembly Models (AMs), and Metal-Organic Polyhedra (MOPs).
"""

from typing import List, Set, Optional
from twa_mops.core.ontomops import (
    ChemicalBuildingUnit,
    AssemblyModel,
    MetalOrganicPolyhedron,
    GenericBuildingUnit,
)


def validate_cbu(cbu: ChemicalBuildingUnit) -> bool:
    """Validate a Chemical Building Unit.
    
    Checks that the CBU has required properties and valid values.
    
    Args:
        cbu: The ChemicalBuildingUnit to validate
    
    Returns:
        True if the CBU is valid, False otherwise
    
    Raises:
        ValueError: If the CBU is missing required properties or has invalid values
    """
    if not cbu.instance_iri:
        raise ValueError("CBU must have an instance IRI")
    
    if not cbu.hasGeometry:
        raise ValueError(f"CBU {cbu.instance_iri} must have geometry")
    
    # Check that each geometry has required properties
    for geo in cbu.hasGeometry:
        if not geo.hasGeometryFile:
            raise ValueError(f"Geometry for CBU {cbu.instance_iri} must have a geometry file")
    
    # Check that CBU has at least one function (isFunctioningAs)
    if not cbu.isFunctioningAs:
        raise ValueError(f"CBU {cbu.instance_iri} must be functioning as at least one GBU type")
    
    return True


def validate_am(am: AssemblyModel) -> bool:
    """Validate an Assembly Model.
    
    Checks that the AM has required properties and valid structure.
    
    Args:
        am: The AssemblyModel to validate
    
    Returns:
        True if the AM is valid, False otherwise
    
    Raises:
        ValueError: If the AM is missing required properties or has invalid structure
    """
    if not am.instance_iri:
        raise ValueError("AM must have an instance IRI")
    
    if not am.hasGenericBuildingUnit:
        raise ValueError(f"AM {am.instance_iri} must have at least one GenericBuildingUnit")
    
    # Check that we have pairs of connected GBUs
    if not am.pairs_of_connected_gbus:
        raise ValueError(f"AM {am.instance_iri} must have pairs of connected GBUs")
    
    return True


def validate_cbu_am_compatibility(
    cbus: List[ChemicalBuildingUnit],
    am: AssemblyModel,
) -> bool:
    """Validate that a list of CBUs is compatible with an AM.
    
    Checks that each CBU can function as one of the GBU types required by the AM.
    
    Args:
        cbus: List of ChemicalBuildingUnits to validate
        am: The AssemblyModel to validate against
    
    Returns:
        True if all CBUs are compatible with the AM
    
    Raises:
        ValueError: If any CBU is not compatible with the AM
    """
    # Get all GBU types required by the AM
    required_gbu_types: Set[str] = set()
    for gbu in am.hasGenericBuildingUnit:
        if hasattr(gbu, 'gbu_type') and gbu.gbu_type:
            required_gbu_types.add(gbu.gbu_type)
    
    if not required_gbu_types:
        raise ValueError(f"AM {am.instance_iri} has no GBU types defined")
    
    # Check each CBU
    for cbu in cbus:
        if not cbu.isFunctioningAs:
            raise ValueError(f"CBU {cbu.instance_iri} is not functioning as any GBU type")
        
        # Check if this CBU can function as at least one required GBU type
        cbu_functions = set(str(gbu_type) for gbu_type in cbu.isFunctioningAs)
        if not cbu_functions.intersection(required_gbu_types):
            raise ValueError(
                f"CBU {cbu.instance_iri} functions as {cbu_functions}, "
                f"but AM {am.instance_iri} requires {required_gbu_types}"
            )
    
    return True


def validate_mop(mop: MetalOrganicPolyhedron) -> bool:
    """Validate a Metal-Organic Polyhedron.
    
    Checks that the MOP has required properties and valid structure.
    
    Args:
        mop: The MetalOrganicPolyhedron to validate
    
    Returns:
        True if the MOP is valid, False otherwise
    
    Raises:
        ValueError: If the MOP is missing required properties or has invalid structure
    """
    if not mop.instance_iri:
        raise ValueError("MOP must have an instance IRI")
    
    if not mop.hasAssemblyModel:
        raise ValueError(f"MOP {mop.instance_iri} must have an AssemblyModel")
    
    if not mop.hasChemicalBuildingUnit:
        raise ValueError(f"MOP {mop.instance_iri} must have at least one ChemicalBuildingUnit")
    
    # Check that MOP has calculated properties
    if mop.hasMolecularWeight is None:
        raise ValueError(f"MOP {mop.instance_iri} must have molecular weight")
    
    if mop.hasCharge is None:
        raise ValueError(f"MOP {mop.instance_iri} must have charge")
    
    return True

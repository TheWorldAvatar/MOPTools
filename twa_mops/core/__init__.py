"""Core ontology and data models for MOPTools."""

# Import and re-export main classes from ontomops and ontospecies
from .ontomops import (
    OntoMOPs,
    MetalOrganicPolyhedron,
    AssemblyModel,
    ChemicalBuildingUnit,
    Provenance,
    HasAssemblyModel,
    HasChemicalBuildingUnit,
    IsFunctioningAs,
    HasCBUFormula,
    HasMOPFormula,
    HasReferenceDOI,
)

from .geo import Point, Vector, Line, Plane, RotationMatrix, Quaternion

__all__ = [
    # OntoMOPs classes
    'OntoMOPs', 'MetalOrganicPolyhedron', 'AssemblyModel', 'ChemicalBuildingUnit',
    'Provenance',
    # Properties
    'HasAssemblyModel', 'HasChemicalBuildingUnit', 'IsFunctioningAs',
    'HasCBUFormula', 'HasMOPFormula', 'HasReferenceDOI',
    # Geometry utilities
    'Point', 'Vector', 'Line', 'Plane', 'RotationMatrix', 'Quaternion',
]

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

from .ontospecies import (
    OntoSpecies,
    HasMolecularWeight,
    HasCharge,
    HasGeometry,
    HasGeometryFile,
    Charge,
    MolecularWeight,
    Geometry,
)

from .geo import Point, Vector, Line, Plane, RotationMatrix, Quaternion

__all__ = [
    # OntoMOPs classes
    'OntoMOPs', 'MetalOrganicPolyhedron', 'AssemblyModel', 'ChemicalBuildingUnit',
    'Provenance',
    # OntoMOPs properties
    'HasAssemblyModel', 'HasChemicalBuildingUnit', 'IsFunctioningAs',
    'HasCBUFormula', 'HasMOPFormula', 'HasReferenceDOI',
    # OntoSpecies classes and properties
    'OntoSpecies', 'HasMolecularWeight', 'HasCharge', 'HasGeometry', 'HasGeometryFile',
    'Charge', 'MolecularWeight', 'Geometry',
    # Geometry utilities
    'Point', 'Vector', 'Line', 'Plane', 'RotationMatrix', 'Quaternion',
]

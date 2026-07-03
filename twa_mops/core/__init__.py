"""Core ontology and data models for MOPTools."""

# Monkey-patch fix for Pydantic v2 ForwardRef handling in twa package
# The twa package's get_object_properties() doesn't handle ForwardRef properly
# This causes pull_from_kg to return incomplete data (only instance_iri)

def _fixed_get_object_properties(cls):
    """Fixed version that resolves ForwardRef annotations."""
    from typing import ForwardRef, get_args, get_origin, _UnionGenericAlias, Union
    from twa.data_model.base_ontology import ObjectProperty
    import sys
    import types
    
    dct_op = {}
    
    # Get the module where the class is defined
    module_name = cls.__module__
    module = sys.modules.get(module_name)
    
    for f, field_info in cls.model_fields.items():
        annotation = field_info.annotation
        
        # Handle ForwardRef by evaluating it in the class's module context
        if isinstance(annotation, ForwardRef):
            if module is None:
                # Module not loaded, try to import it
                import importlib
                module = importlib.import_module(module_name)
            
            if module is None:
                # Still can't get module, skip
                continue
                
            try:
                # Evaluate the forward reference string in the module's namespace
                annotation = eval(annotation.__forward_arg__, module.__dict__, None)
            except Exception:
                # If evaluation fails, skip this field
                continue
        
        # Get the actual type from the annotation
        # For GenericAlias (e.g., HasPolyhedralShape[PolyhedralShape]), we need to keep it as-is
        # For Union types (e.g., Optional[T]), we need to extract the inner type
        op = annotation
        
        # Check if it's a types.GenericAlias (Python 3.9+)
        # We need to keep the full annotation for compatibility with twa's pull_from_kg
        # which does get_args(op_dct['type'])[0] to extract the target class
        if isinstance(annotation, (types.GenericAlias, _UnionGenericAlias)):
            # For Union types (like Optional[T]), we need to extract the non-None type
            # and check if that's an ObjectProperty
            if type(annotation) == _UnionGenericAlias:
                # This is likely Optional[T] or Union[T1, T2, ...]
                # Check if it's Optional by looking at args
                args = get_args(annotation)
                # Filter out NoneType
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    # Check the first non-None arg
                    inner_type = non_none_args[0]
                    # Check if inner_type is a GenericAlias (e.g., HasBindingSite[BindingSite])
                    if isinstance(inner_type, (types.GenericAlias, _UnionGenericAlias)):
                        inner_origin = get_origin(inner_type)
                        if isinstance(inner_origin, type) and ObjectProperty._is_inherited(inner_origin):
                            # This is Optional[ObjectProperty[T]], store the inner GenericAlias
                            dct_op[inner_origin.predicate_iri] = {'field': f, 'type': inner_type}
                            continue
            # Keep the annotation as-is
            pass
        elif isinstance(annotation, ForwardRef):
            # We've already evaluated it above, so it should be a GenericAlias now
            # If not, skip
            if not isinstance(annotation, (types.GenericAlias, _UnionGenericAlias)):
                continue
        else:
            # For plain types, keep as-is
            pass
        
        # Now check if the annotation (or its origin) is an ObjectProperty
        # We need to extract the origin to check if it's an ObjectProperty
        op_origin = annotation
        if isinstance(annotation, (types.GenericAlias, _UnionGenericAlias)):
            op_origin = get_origin(annotation)
        
        if isinstance(op_origin, type) and ObjectProperty._is_inherited(op_origin):
            dct_op[op_origin.predicate_iri] = {'field': f, 'type': annotation}
    
    return dct_op


def _fixed_get_data_properties(cls):
    """Fixed version that resolves ForwardRef annotations for data properties."""
    from typing import ForwardRef, get_args, get_origin, _UnionGenericAlias
    from twa.data_model.base_ontology import DatatypeProperty
    import sys
    import types
    
    dct_dp = {}
    
    # Get the module where the class is defined
    module_name = cls.__module__
    module = sys.modules.get(module_name)
    
    for f, field_info in cls.model_fields.items():
        annotation = field_info.annotation
        
        # Handle ForwardRef by evaluating it in the class's module context
        if isinstance(annotation, ForwardRef):
            if module is None:
                # Module not loaded, try to import it
                import importlib
                module = importlib.import_module(module_name)
            
            if module is None:
                # Still can't get module, skip
                continue
                
            try:
                # Evaluate the forward reference string in the module's namespace
                annotation = eval(annotation.__forward_arg__, module.__dict__, None)
            except Exception:
                # If evaluation fails, skip this field
                continue
        
        # Get the actual type from the annotation
        # For GenericAlias (e.g., HasSymmetryPointGroup[str]), we need to keep it as-is
        # For Union types (e.g., Optional[T]), we need to extract the inner type
        dp = annotation
        
        # Check if it's a types.GenericAlias (Python 3.9+)
        # We need to keep the full annotation for compatibility with twa's pull_from_kg
        if isinstance(annotation, (types.GenericAlias, _UnionGenericAlias)):
            # For Union types (like Optional[T]), we need to extract the non-None type
            # and check if that's a DatatypeProperty
            if type(annotation) == _UnionGenericAlias:
                # This is likely Optional[T] or Union[T1, T2, ...]
                # Check if it's Optional by looking at args
                args = get_args(annotation)
                # Filter out NoneType
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    # Check the first non-None arg
                    inner_type = non_none_args[0]
                    # Check if inner_type is a GenericAlias (e.g., HasSymmetryPointGroup[str])
                    if isinstance(inner_type, (types.GenericAlias, _UnionGenericAlias)):
                        inner_origin = get_origin(inner_type)
                        if isinstance(inner_origin, type) and DatatypeProperty._is_inherited(inner_origin):
                            # This is Optional[DatatypeProperty[T]], store the inner GenericAlias
                            dct_dp[inner_origin.predicate_iri] = {'field': f, 'type': inner_type}
                            continue
            # Keep the annotation as-is
            pass
        elif isinstance(annotation, ForwardRef):
            # We've already evaluated it above, so it should be a GenericAlias now
            # If not, skip
            if not isinstance(annotation, (types.GenericAlias, _UnionGenericAlias)):
                continue
        else:
            # For plain types, keep as-is
            pass
        
        # Now check if the annotation (or its origin) is a DatatypeProperty
        # We need to extract the origin to check if it's a DatatypeProperty
        dp_origin = annotation
        if isinstance(annotation, (types.GenericAlias, _UnionGenericAlias)):
            dp_origin = get_origin(annotation)
        
        if isinstance(dp_origin, type) and DatatypeProperty._is_inherited(dp_origin):
            dct_dp[dp_origin.predicate_iri] = {'field': f, 'type': annotation}
    
    return dct_dp


# Apply the monkey patches
try:
    from twa.data_model.base_ontology import BaseClass, DatatypeProperty
    BaseClass.get_object_properties = classmethod(_fixed_get_object_properties)
    BaseClass.get_data_properties = classmethod(_fixed_get_data_properties)
except Exception:
    # If patching fails, continue without it
    pass


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

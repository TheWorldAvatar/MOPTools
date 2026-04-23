from __future__ import annotations
from typing import Optional, Dict, List, Tuple, Set
from scipy.optimize import fsolve
from datetime import datetime
import plotly.express as px
import pandas as pd
import numpy as np
import math
import json
import os

from twa.data_model.base_ontology import BaseOntology, BaseClass, ObjectProperty, DatatypeProperty, KnowledgeGraph
import ontospecies
import om
import cavity_and_pore_size as cap

from geo import Point, Vector, Line, Plane, RotationMatrix, Quaternion

BINDING_FRAGMENT_METAL = 'Metal'
BINDING_FRAGMENT_CO2 = 'CO2'
BINDING_FRAGMENT_O3 = 'O3'
BINDING_FRAGMENT_N2 = 'N2'
GBU_TYPE_2_BENT = '2-bent'
GBU_TYPE_2_LINEAR = '2-linear'
GBU_TYPE_3_PLANAR = '3-planar'
GBU_TYPE_3_PYRAMIDAL = '3-pyramidal'
GBU_TYPE_4_PLANAR = '4-planar'
GBU_TYPE_4_PYRAMIDAL = '4-pyramidal'
GBU_TYPE_5_PYRAMIDAL = '5-pyramidal'


class OntoMOPs(BaseOntology):
    base_url = 'https://www.theworldavatar.com/kg'
    namespace = 'ontomops'
    owl_versionInfo = '1.1-ogm'
    rdfs_comment = 'An ontology developed for representing Metal-Organic Polyhedra (MOPs). This is object graph mapper (OGM) version.'


# object properties
HasAssemblyModel = ObjectProperty.create_from_base('HasAssemblyModel', OntoMOPs)
HasBindingDirection = ObjectProperty.create_from_base('HasBindingDirection', OntoMOPs)
HasBindingSite = ObjectProperty.create_from_base('HasBindingSite', OntoMOPs)
HasCavity = ObjectProperty.create_from_base('HasCavity', OntoMOPs)
HasChemicalBuildingUnit = ObjectProperty.create_from_base('HasChemicalBuildingUnit', OntoMOPs)
HasGenericBuildingUnit = ObjectProperty.create_from_base('HasGenericBuildingUnit', OntoMOPs)
HasGenericBuildingUnitNumber = ObjectProperty.create_from_base('HasGenericBuildingUnitNumber', OntoMOPs)
HasPolyhedralShape = ObjectProperty.create_from_base('HasPolyhedralShape', OntoMOPs)
HasProvenance = ObjectProperty.create_from_base('HasProvenance', OntoMOPs)
IsFunctioningAs = ObjectProperty.create_from_base('IsFunctioningAs', OntoMOPs)
IsNumberOf = ObjectProperty.create_from_base('IsNumberOf', OntoMOPs)
# additions for assembler
HasGBUConnectingPoint = ObjectProperty.create_from_base('HasGBUConnectingPoint', OntoMOPs)
HasGBUCoordinateCenter = ObjectProperty.create_from_base('HasGBUCoordinateCenter', OntoMOPs)
HasCBUAssemblyCenter = ObjectProperty.create_from_base('HasCBUAssemblyCenter', OntoMOPs)
HasBindingPoint = ObjectProperty.create_from_base('HasBindingPoint', OntoMOPs)
HasGBUType = ObjectProperty.create_from_base('HasGBUType', OntoMOPs)
HasCBUAssemblyTransformation = ObjectProperty.create_from_base('HasCBUAssemblyTransformation', OntoMOPs)
Transforms = ObjectProperty.create_from_base('Transforms', OntoMOPs)
AlignsTo = ObjectProperty.create_from_base('AlignsTo', OntoMOPs)
# for pore ring
HasPoreRing = ObjectProperty.create_from_base('HasPoreRing', OntoMOPs)
IsFormedBy = ObjectProperty.create_from_base('IsFormedBy', OntoMOPs)
MeasuresPoreRing = ObjectProperty.create_from_base('MeasuresRing', OntoMOPs)
HasPoreSize = ObjectProperty.create_from_base('HasPoreSize', OntoMOPs)
HasPoreDiameter = ObjectProperty.create_from_base('HasPoreDiameter', OntoMOPs)
# for cavity
HasLargestInnerSphereDiameter = ObjectProperty.create_from_base('HasLargestInnerSphereDiameter', OntoMOPs)
HasOuterDiameter = ObjectProperty.create_from_base('HasOuterDiameter', OntoMOPs)


# data properties
HasCBUFormula = DatatypeProperty.create_from_base('HasCBUFormula', OntoMOPs)
HasCCDCNumber = DatatypeProperty.create_from_base('HasCCDCNumber', OntoMOPs)
HasMOPFormula = DatatypeProperty.create_from_base('HasMOPFormula', OntoMOPs)
HasModularity = DatatypeProperty.create_from_base('HasModularity', OntoMOPs)
HasOuterCoordinationNumber = DatatypeProperty.create_from_base('HasOuterCoordinationNumber', OntoMOPs)
HasPlanarity = DatatypeProperty.create_from_base('HasPlanarity', OntoMOPs)
HasReferenceDOI = DatatypeProperty.create_from_base('HasReferenceDOI', OntoMOPs)
HasSymbol = DatatypeProperty.create_from_base('HasSymbol', OntoMOPs)
HasSymmetryPointGroup = DatatypeProperty.create_from_base('HasSymmetryPointGroup', OntoMOPs)
HasUnitNumberValue = DatatypeProperty.create_from_base('HasUnitNumberValue', OntoMOPs)
# additions for assembler
HasBindingFragment = DatatypeProperty.create_from_base('HasBindingFragment', OntoMOPs)
HasX = DatatypeProperty.create_from_base('HasX', OntoMOPs)
HasY = DatatypeProperty.create_from_base('HasY', OntoMOPs)
HasZ = DatatypeProperty.create_from_base('HasZ', OntoMOPs)
QuaternionToRotate = DatatypeProperty.create_from_base('QuaternionToRotate', OntoMOPs)
ScaleFactorToAlignCoordinateCenter = DatatypeProperty.create_from_base('ScaleFactorToAlignCoordinateCenter', OntoMOPs)
TranslationVectorToAlignOrigin = DatatypeProperty.create_from_base('TranslationVectorToAlignOrigin', OntoMOPs)
# for pore ring
HasProbingVector = DatatypeProperty.create_from_base('HasProbingVector', OntoMOPs)


# classes
class MolecularCage(BaseClass):
    rdfs_isDefinedBy = OntoMOPs

class CoordinationCage(MolecularCage):
    pass

class GenericBuildingUnitType(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasModularity: HasModularity[int]
    hasPlanarity: HasPlanarity[str]

    @property
    def label(self):
        return f"{list(self.hasModularity)[0]}-{list(self.hasPlanarity)[0]}"

class CoordinatePoint(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasX: HasX[float]
    hasY: HasY[float]
    hasZ: HasZ[float]

    @property
    def coordinates(self):
        return Point(x=list(self.hasX)[0], y=list(self.hasY)[0], z=list(self.hasZ)[0])

class GenericBuildingUnit(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasGBUType: HasGBUType[GenericBuildingUnitType]
    hasGBUCoordinateCenter: HasGBUCoordinateCenter[GBUCoordinateCenter]

    @property
    def gbu_type(self):
        return list(self.hasGBUType)[0].label

    @property
    def is_4_planar(self):
        return list(self.hasGBUType)[0].label == '4-planar'

    @property
    def is_2_bent(self):
        return list(self.hasGBUType)[0].label == GBU_TYPE_2_BENT

    @property
    def is_2_linear(self):
        return list(self.hasGBUType)[0].label == GBU_TYPE_2_LINEAR

    @property
    def modularity(self):
        return list(list(self.hasGBUType)[0].hasModularity)[0]

class GenericBuildingUnitNumber(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    isNumberOf: IsNumberOf[GenericBuildingUnit]
    hasUnitNumberValue: HasUnitNumberValue[int]

class PoreRing(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    isFormedBy: IsFormedBy[GBUCoordinateCenter]
    hasProbingVector: HasProbingVector[str]

    @property
    def probing_vector(self):
        vec = list(self.hasProbingVector)[0].split('#')
        return Vector(x=float(vec[0]), y=float(vec[1]), z=float(vec[2]))

    @property
    def pair_of_ring_forming_gbus(self):
        _pairs = {}
        for cc in self.isFormedBy:
            cc: GBUCoordinateCenter
            cps = list(cc.hasGBUConnectingPoint)
            for cp in cps:
                if cp.instance_iri not in _pairs:
                    _pairs[cp.instance_iri] = [cc]
                else:
                    _pairs[cp.instance_iri].append(cc)
        pairs = {k: v for k, v in _pairs.items() if len(v) == 2}
        return pairs

class PoreSize(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    measuresPoreRing: MeasuresPoreRing[PoreRing]
    hasProbingVector: HasProbingVector[str]
    hasPoreDiameter: HasPoreDiameter[om.Diameter]

class AssemblyModel(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasGenericBuildingUnit: HasGenericBuildingUnit[GenericBuildingUnit]
    hasGenericBuildingUnitNumber: HasGenericBuildingUnitNumber[GenericBuildingUnitNumber]
    hasPolyhedralShape: HasPolyhedralShape[PolyhedralShape]
    hasSymmetryPointGroup: HasSymmetryPointGroup[str]
    hasGBUCoordinateCenter: HasGBUCoordinateCenter[GBUCoordinateCenter]
    hasGBUConnectingPoint: HasGBUConnectingPoint[GBUConnectingPoint]
    hasPoreRing: Optional[HasPoreRing[PoreRing]] = None

    def visualise(self):
        rows = []
        for gbu in self.hasGenericBuildingUnit:
            gbu: GenericBuildingUnit
            for gcc in gbu.hasGBUCoordinateCenter:
                gcc: GBUCoordinateCenter
                rows.append([gbu.gbu_type, gcc.instance_iri, str(gcc.rdfs_comment), gcc.coordinates.x, gcc.coordinates.y, gcc.coordinates.z])
                for cp in gcc.hasGBUConnectingPoint:
                    cp: GBUConnectingPoint
                    rows.append(['ConnectingPoint', cp.instance_iri, str(cp.rdfs_comment), cp.coordinates.x, cp.coordinates.y, cp.coordinates.z])
        df = pd.DataFrame(rows, columns=['Label', 'IRI', 'Position', 'X', 'Y', 'Z'])

        fig = px.scatter_3d(df, x='X', y='Y', z='Z', color='Label', hover_data=['IRI', 'Position'])
        fig.update_traces(marker=dict(size=2))

        return fig

    @staticmethod
    def process_geometry_json(am_json, gbu_type_1_label, gbu_type_2_label):
        """
        Example JSON for AM (the `am_json` will be the list of dictionaries within the key of the AM label in the JSON file):
        {
            "(5-pyramidal)x12(2-linear)x30_Ih": [
                {
                    "Key": "Position_1",
                    "Label": "5-pyramidal",
                    "X": 2.6368,
                    "Y": 2.7551,
                    "Z": 1.2068,
                    "Neighbors": [
                        {
                            "Key": "Position_13",
                            "Label": "2-linear",
                            "Distance": 2.1029
                        },
                        {
                            "Key": "Position_15",
                            "Label": "2-linear",
                            "Distance": 2.1029
                        },
                        ...
                    ],
                    "ClosestDummies": ["Dummy_1", "Dummy_2", "Dummy_3", ...]
                },
                ...
                {
                    "Key": "Dummy_1",
                    "Label": "Dummy",
                    "X": 2.8490,
                    "Y": 1.7266,
                    "Z": 1.2590,
                    "Positions": ["Position_13", "Position_1"]
                },
                ...
                {
                    "Key": "Center",
                    "Label": "Center",
                    "X": 0.0,
                    "Y": 0.0,
                    "Z": 0.0
                }
            ]
        }
        """
        coordinate_point_dict = {}
        connecting_point_dict = {}
        # handle dummy blocks `{"Label": "Dummy", ...}`
        for i in range(len(am_json)):
            if am_json[i]['Label'] == 'Dummy':
                dummy = GBUConnectingPoint(hasX=am_json[i]['X'], hasY=am_json[i]['Y'], hasZ=am_json[i]['Z'])
                connecting_point_dict[am_json[i]['Key']] = dummy

        # handle position blocks `{"Label": "5-pyramidal", ...}`
        # TODO the part that getting the gbu_type_1 and gbu_type_2 can be optimised
        for i in range(len(am_json)):
            if am_json[i]['Label'] in [gbu_type_1_label, gbu_type_2_label]:
                coord = GBUCoordinateCenter(
                    hasX=am_json[i]['X'],
                    hasY=am_json[i]['Y'],
                    hasZ=am_json[i]['Z'],
                    hasGBUConnectingPoint=[connecting_point_dict[d] for d in am_json[i]['ClosestDummies']] # gbu_type_label=am_json[i]['Label']
                )
                if am_json[i]['Label'] in coordinate_point_dict:
                    coordinate_point_dict[am_json[i]['Label']].append(coord)
                else:
                    coordinate_point_dict[am_json[i]['Label']] = [coord]

        return coordinate_point_dict, connecting_point_dict

    def add_coordinates_from_json(self, am_json):
        gbus = list(self.hasGenericBuildingUnit)
        gbu1 = gbus[0]
        gbu2 = gbus[1]
        coordinate_point_dict, connecting_point_dict = self.__class__.process_geometry_json(am_json, gbu1.gbu_type, gbu2.gbu_type)
        gbu1.hasGBUCoordinateCenter = coordinate_point_dict[gbu1.gbu_type]
        gbu2.hasGBUCoordinateCenter = coordinate_point_dict[gbu2.gbu_type]
        self.hasGBUCoordinateCenter = [c for g in list(coordinate_point_dict.values()) for c in g]
        self.hasGBUConnectingPoint = list(connecting_point_dict.values())

    @classmethod
    def from_geometry_json(
        cls,
        am_json,
        gbu_type_1: GenericBuildingUnitType,
        gbu_type_2: GenericBuildingUnitType,
        gbu_number_1: int,
        gbu_number_2: int,
        am_symmetry: str,
        polyhedral_shape: str = None,
    ):

        # process the AM geometry JSON
        coordinate_point_dict, connecting_point_dict = cls.process_geometry_json(am_json, gbu_type_1.label, gbu_type_2.label)

        # instantiate the GBUs
        gbu1 = GenericBuildingUnit(hasGBUType=gbu_type_1, hasGBUCoordinateCenter=coordinate_point_dict[gbu_type_1.label])
        gbu2 = GenericBuildingUnit(hasGBUType=gbu_type_2, hasGBUCoordinateCenter=coordinate_point_dict[gbu_type_2.label])

        # assign GBU type to each GBU coordinate center so can determine how to calculate connecting point plane later
        for _gcc in gbu1.hasGBUCoordinateCenter:
            _gcc.hasGBUType = gbu1.hasGBUType
        for _gcc in gbu2.hasGBUCoordinateCenter:
            _gcc.hasGBUType = gbu2.hasGBUType

        return cls(
            hasGenericBuildingUnit=[gbu1, gbu2],
            hasGenericBuildingUnitNumber=[
                GenericBuildingUnitNumber(isNumberOf=gbu1, hasUnitNumberValue=gbu_number_1),
                GenericBuildingUnitNumber(isNumberOf=gbu2, hasUnitNumberValue=gbu_number_2)],
            hasPolyhedralShape=polyhedral_shape if polyhedral_shape is not None else set(),
            hasSymmetryPointGroup=am_symmetry,
            hasGBUCoordinateCenter=[c for g in list(coordinate_point_dict.values()) for c in g],
            hasGBUConnectingPoint=list(connecting_point_dict.values())
        )

    def gbu_of_type(self, gbu_type):
        return [gbu for gbu in self.hasGenericBuildingUnit if gbu_type == gbu.gbu_type]

    @property
    def pairs_of_connected_gbus(self) -> Dict:
        # sort so always use the same when calculating the scaling factor since otherwise in cases where not equal will get varying scaling factor
        pairs = {}
        for cc in sorted(self.hasGBUCoordinateCenter, key=lambda x: x.instance_iri):
            cc: GBUCoordinateCenter
            cps = sorted(list(cc.hasGBUConnectingPoint), key=lambda x: x.instance_iri)
            for cp in cps:
                if cp.instance_iri not in pairs:
                    pairs[cp.instance_iri] = [cc]
                else:
                    pairs[cp.instance_iri].append(cc)
        return pairs

class Provenance(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasReferenceDOI: HasReferenceDOI[str]

class Volume(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasValue: om.HasValue[om.Measure]

class Cavity(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasLargestInnerSphereDiameter: HasLargestInnerSphereDiameter[om.Diameter]

class PolyhedralShape(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasSymbol: HasSymbol[str]

class BindingPoint(CoordinatePoint):
    pass

class BindingSite(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasOuterCoordinationNumber: HasOuterCoordinationNumber[int]
    hasBindingPoint: HasBindingPoint[BindingPoint]
    hasBindingFragment: HasBindingFragment[str]
    temporarily_blocked: Optional[bool] = False

    @property
    def binding_coordinates(self) -> Point:
        return list(self.hasBindingPoint)[0].coordinates

    def binding_atoms(self, atoms: List[Point]) -> List[Point]:
        # count the atoms
        def get_atom_count(s):
            atom_counts = {}
            i = 0
            while i < len(s):
                if s[i].isupper():
                    name = s[i]
                    i += 1
                    # collect lowercase characters to form the full name
                    while i < len(s) and s[i].islower():
                        name += s[i]
                        i += 1
                    # collect digits to count the atoms (if any)
                    count = 1
                    num = ''
                    while i < len(s) and s[i].isdigit():
                        num += s[i]
                        i += 1
                    count = int(num) if num else 1
                    # store the count of atoms
                    atom_counts[name] = atom_counts.get(name, 0) + count
                else:
                    i += 1
            return atom_counts

        counts = get_atom_count(list(self.hasBindingFragment)[0])
        # binding fragments situations: CO2, O, N2, single metal, multiple metals
        # find the centroid of the relevant atoms that are close
        sorted_atoms = self.binding_coordinates.rank_distance_to_points(atoms)
        all_binding_atoms = []
        for atom, num in counts.items():
            all_binding_atoms.extend([a for a in sorted_atoms if a.label == atom][:num]) # assuming that the binding fragment atoms will be first in the atoms sorted by distance from the dummy atom
        return all_binding_atoms # list of points objects

    @staticmethod
    def compute_assembly_center_from_binding_sites(
        lst_binding_sites: List['BindingSite'],
        atom_points: List['Point'],
        gbu_type: str,
        binding_fragment: str,
    ) -> 'CBUAssemblyCenter':
        # compute the CBU assembly center, which is the geometry (coordinates) center point of the CBU structure (average of all atoms)
        # projected on the normal vector of the plane formed by the binding sites (dummy atoms) that pass through the circumcenter point of all binding sites
        lst_binding_points = [bs.binding_coordinates for bs in lst_binding_sites]
        if len(lst_binding_points) > 2:
            # when the number of binding sites are greater than 2
            # find the plane from the binding sites and the circumcenter of the binding sites
            # then project the center of the CBU on the normal vector of the plane
            # to find the assembly center of the CBU
            # even the assembly center is overshooting from the molecule
            # the sin/cos calculations will make sure its coordinates is transformed correctly
            cbu_geo_center = Point.centroid(atom_points)
            #cbu_binding_sites_plane = Plane.fit_from_points(lst_binding_points)# positive_ref_point=cbu_geo_center)
            cbu_binding_sites_plane = Plane.fit_from_points(lst_binding_points, positive_ref_point=cbu_geo_center)
            cbu_binding_sites_circumcenter = Point.fit_circle_2d(lst_binding_points)[0]

            line = Line(point=cbu_binding_sites_circumcenter, direction=cbu_binding_sites_plane.normal)
            cbu_assemb_center = line.project_point(cbu_geo_center)
        else:
            bindingsite_mid_point = Point.mid_point(*lst_binding_points)
            if 'linear' in gbu_type.lower():
                # if the CBU is expected to function as 2-linear, take the average of the two binding sites
                cbu_assemb_center = bindingsite_mid_point
            else:
                # if the CBU is expected to function as 2-bent, then compute the intersection of the two vectors
                # to be used as the third point to fit a plane with the two binding sites
                if binding_fragment == BINDING_FRAGMENT_CO2:
                    # first find the closest two O atoms and the C atoms for each binding sites
                    v_dct = {}
                    lst_pts_for_plane = []
                    for bs in lst_binding_sites:
                        bp: Point = bs.binding_coordinates
                        ranked_atoms = bp.rank_distance_to_points(atom_points)
                        closest_two_O = [a for a in ranked_atoms if a.label == 'O'][:2]
                        closest_C = [a for a in ranked_atoms if a.label == 'C'][0]
                        # find the average of the O atoms and use it to form line with the closest C atom
                        avg_O = Point.mid_point(*closest_two_O)
                        v_dct[bs.instance_iri] = {'avg_O': avg_O, 'closest_C': closest_C, 'line': Line.from_two_points(start=avg_O, end=closest_C)}
                        lst_pts_for_plane.extend([closest_C, avg_O])
                    # find the plane from these points
                    plane = Plane.fit_from_points(lst_pts_for_plane)
                    # find the intersection of these lines when they are projected on the plane
                    proj_lines = [v['line'] for v in v_dct.values()]
                    intersection = plane.find_intersection_of_lines_projected(*proj_lines)
                    # use the intersection and two binding site to form the plane
                    plane_of_bs = Plane.from_three_points(pt1=intersection, pt2=lst_binding_points[0], pt3=lst_binding_points[1])
                    perpendicular_bisector = plane_of_bs.find_perpendicular_bisector_on_plane(*lst_binding_points)
                    cbu_assemb_center = perpendicular_bisector.project_point(intersection)
                elif binding_fragment == BINDING_FRAGMENT_N2:
                    # first find the closest two O atoms and the C atoms for each binding sites
                    v_dct = {}
                    lst_pts_for_plane = []
                    for bs in lst_binding_sites:
                        bp: Point = bs.binding_coordinates
                        ranked_atoms = bp.rank_distance_to_points(atom_points)
                        closest_two_N = [a for a in ranked_atoms if a.label == 'N'][:2]
                        third_C = [a for a in ranked_atoms if a.label == 'C'][2]
                        # find the average of the O atoms and use it to form line with the closest C atom
                        avg_N = Point.mid_point(*closest_two_N)
                        v_dct[bs.instance_iri] = {'avg_N': avg_N, 'third_C': third_C, 'line': Line.from_two_points(start=avg_N, end=third_C)}
                        lst_pts_for_plane.extend([third_C, avg_N])
                    # find the plane from these points
                    plane = Plane.fit_from_points(lst_pts_for_plane)
                    # find the intersection of these lines when they are projected on the plane
                    proj_lines = [v['line'] for v in v_dct.values()]
                    intersection = plane.find_intersection_of_lines_projected(*proj_lines)
                    # use the intersection and two binding site to form the plane
                    plane_of_bs = Plane.from_three_points(pt1=intersection, pt2=lst_binding_points[0], pt3=lst_binding_points[1])
                    perpendicular_bisector = plane_of_bs.find_perpendicular_bisector_on_plane(*lst_binding_points)
                    cbu_assemb_center = perpendicular_bisector.project_point(intersection)
                else:
                    raise NotImplementedError(f'CBUs functioning as a {gbu_type} with binding fragment {binding_fragment} is not yet supported.')
        return CBUAssemblyCenter(hasX=cbu_assemb_center.x, hasY=cbu_assemb_center.y, hasZ=cbu_assemb_center.z)

class MetalSite(BindingSite):
    pass

class OrganicSite(BindingSite):
    pass

class BindingDirection(BaseClass):
    rdfs_isDefinedBy = OntoMOPs

class DirectBinding(BindingDirection):
    pass

class SidewayBinding(BindingDirection):
    pass


DIRECT_BINDING = DirectBinding(
    instance_iri=OntoMOPs.namespace_iri + '/DirectBinding_f3716525-0a8d-430f-ae24-0a043ec0c93a'
)

class GBUConnectingPoint(CoordinatePoint):
    pass

class GBUCoordinateCenter(CoordinatePoint):
    hasGBUConnectingPoint: HasGBUConnectingPoint[GBUConnectingPoint]
    hasGBUType: Optional[HasGBUType[GenericBuildingUnitType]] = None

    @property
    def vector_from_am_center(self) -> Vector:
        # NOTE TODO this assumes that the center of the AM is the (0, 0, 0) point
        return Vector.from_two_points(start=Point(x=0, y=0, z=0), end=self.coordinates)

    @property
    def distance_to_am_center(self):
        return self.coordinates.get_distance_to(Point(x=0, y=0, z=0))
    
    @property
    def vector_to_connecting_point_plane(self):
        """
        Normal vector for the connecting-point geometry.
        Uses the parent's GBU type via a back-reference (_parent_gbu) set during AM construction.
        Falls back gracefully if the back-ref is missing.
        """
        gbu_type = list(self.hasGBUType)[0].label if self.hasGBUType else ""

        _cps = sorted(list(self.hasGBUConnectingPoint), key=lambda x: x.coordinates.x)
        connecting_points = [p.coordinates for p in _cps]

        if len(connecting_points) < 3:
            line = Line.from_two_points(start=connecting_points[0], end=connecting_points[1])

            if "2-linear" in gbu_type:
                # 2-linear: use normal at AM center
                _v = line.normal_vector_from_point_to_line(Point(x=0, y=0, z=0))
                v = Vector.from_array(_v.as_array)
            elif "2-bent" in gbu_type:
                # 2-bent (default if unknown): use normal at this coordinate center
                v = line.normal_vector_from_point_to_line(self.coordinates)
            else:
                raise ValueError(f"Cannot determine GBU type for GBUCoordinateCenter; "
                                 f"required to decide between 2-linear and 2-bent. "
                                 f"Found: '{gbu_type}'")
        else:
            plane = Plane.fit_from_points(connecting_points, Point(x=0, y=0, z=0))
            v = plane.normal
        return v



    @property
    def vector_to_farthest_connecting_point(self):
        # find the plane perpendicular to the vector to the average connecting point
        plane = Plane.from_point_and_normal(self.coordinates, self.vector_to_connecting_point_plane)
        # project all connecting points onto the plane
        projected_points = [plane.project_point(p.coordinates) for p in self.hasGBUConnectingPoint]
        # find the farthest connecting point and construct a vector from center to it
        farthest_projected_point = self.coordinates.farthest_point(projected_points)
        vector = Vector.from_two_points(start=self.coordinates, end=farthest_projected_point)
        return vector

    @property
    def vector_to_shortest_side(self):
        # find the plane perpendicular to the vector to the average connecting point
        plane = Plane.from_point_and_normal(self.coordinates, self.vector_to_connecting_point_plane)
        # project all connecting points onto the plane
        projected_points = [plane.project_point(p.coordinates) for p in self.hasGBUConnectingPoint]
        # find the closest pair of connecting points and construct a vector connecting the center to the line connecting them
        closest_pair = Point.closest_pair(projected_points)
        line = Line.from_two_points(start=closest_pair[0], end=closest_pair[1])
        v = line.normal_vector_from_point_to_line(self.coordinates)
        return v

class CBUAssemblyCenter(CoordinatePoint):
    pass


################# Molecular Fragments #################
## Object properties
HasFragmentType = ObjectProperty.create_from_base('HasFragmentType', OntoMOPs)
HasMolecularFragment = ObjectProperty.create_from_base('HasMolecularFragment', OntoMOPs)
HasSideChainFragment = ObjectProperty.create_from_base('HasSideChainFragment', OntoMOPs)
IsIsomerOf = ObjectProperty.create_from_base('IsIsomerOf', OntoMOPs)


## Data properties
HasSmiles = DatatypeProperty.create_from_base('HasSmiles', OntoMOPs)
HasDummyAtomicNumber = DatatypeProperty.create_from_base('HasDummyAtomicNumber', OntoMOPs)
HasMolBlock = DatatypeProperty.create_from_base('HasMolBlock', OntoMOPs)
HasMolecularFormula = DatatypeProperty.create_from_base('HasMolecularFormula', OntoMOPs)
HasLinkerFragmentOrder = DatatypeProperty.create_from_base('HasLinkerFragmentOrder', OntoMOPs)
IsLinearFragment = DatatypeProperty.create_from_base('IsLinearFragment', OntoMOPs)
IsCyclicFragment = DatatypeProperty.create_from_base('IsCyclicFragment', OntoMOPs)
HasNumDummyAtoms = DatatypeProperty.create_from_base('HasNumDummyAtoms', OntoMOPs)
HasFragmentOrder = DatatypeProperty.create_from_base('HasFragmentOrder', OntoMOPs)


class FragmentType(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasNumDummyAtoms: HasNumDummyAtoms[int] = None

    @property
    def num_dummy_atoms(self) -> int:
        return list(self.hasNumDummyAtoms)[0]

class BindingFragment(FragmentType):
    hasOuterCoordinationNumber: HasOuterCoordinationNumber[int]
    hasBindingFragment: HasBindingFragment[str]
    hasNumDummyAtoms: HasNumDummyAtoms[int] = 1
    hasBindingDirection: HasBindingDirection[BindingDirection]

class NodeFragment(FragmentType):
    hasNumDummyAtoms: HasNumDummyAtoms[int]
    
class LinkerFragment(FragmentType):
    # Indicates whether the linker fragment is cyclic (True) or acyclic (False).
    isCyclic: Optional[IsLinearFragment[bool]] = None
    isLinear: Optional[IsCyclicFragment[bool]] = None
    hasNumDummyAtoms: HasNumDummyAtoms[int] = 2
    isIsomerOf: Optional[IsIsomerOf[LinkerFragment]] = None

    @property
    def is_linear(self) -> bool:
        return list(self.isLinear)[0] if self.isLinear else False

    @property
    def is_cyclic(self) -> bool:
        return list(self.isCyclic)[0] if self.isCyclic else False

class SideChainFragment(FragmentType):
    hasNumDummyAtoms: HasNumDummyAtoms[int] = 1

class MolecularFragment(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasCharge: ontospecies.HasCharge[ontospecies.Charge]
    hasMolecularWeight: ontospecies.HasMolecularWeight[ontospecies.MolecularWeight]
    hasMolecularFormula: HasMolecularFormula[str]
    hasGeometry: ontospecies.HasGeometry[ontospecies.Geometry]
    hasFragmentType: HasFragmentType[FragmentType]
    hasSmiles: HasSmiles[str]
    hasDummyAtomicNumber: HasDummyAtomicNumber[int]
    hasSideChainFragments: Optional[HasSideChainFragment[MolecularFragment]] = None

    @property
    def charge(self):
        return list(list(list(self.hasCharge)[0].hasValue)[0].hasNumericalValue)[0]

    @property
    def molecular_weight(self):
        return list(list(list(self.hasMolecularWeight)[0].hasValue)[0].hasNumericalValue)[0]
    
    @property
    def molecular_formula(self):
        return list(self.hasMolecularFormula)[0]
    
    @property
    def smiles(self):
        return list(self.hasSmiles)[0]
    
    @property
    def is_node_fragment(self):
        return isinstance(list(self.hasFragmentType)[0], NodeFragment)
    
    @property
    def is_linker_fragment(self):
        return isinstance(list(self.hasFragmentType)[0], LinkerFragment)
    
    @property
    def is_binding_fragment(self):
        return isinstance(list(self.hasFragmentType)[0], BindingFragment)   
    
    @property
    def fragment_type(self) -> FragmentType:
        """
        Returns the fragment type of the molecular fragment.
        """
        return list(self.hasFragmentType)[0]
    
    def get_mol_block(self, sparql_client) -> str:
        """
        Returns the mol file contents of the molecular fragment.
        """
        if hasattr(self, "_mol_block"):
            return self._mol_block
        
        geometry_fpath = list(self.hasGeometry)[0].geometry_file
        download_fpath = geometry_fpath.split('/')[-1]

        if os.path.exists(geometry_fpath):
            with open(geometry_fpath, 'r') as f:
                self._mol_block = f.read()
        elif os.path.exists(download_fpath):
            with open(download_fpath, 'r') as f:
                self._mol_block = f.read()
        else:
            sparql_client.download_file(geometry_fpath, download_fpath)
            with open(download_fpath, 'r') as f:
                self._mol_block = f.read()
        
        return self._mol_block
    
    @property
    def is_asymmetric(self) -> bool:
        """
        Returns True if the fragment is asymmetric, False otherwise.
        This is determined by the number of dummy atoms in the fragment type.
        """

        if hasattr(self, '_is_asymmetric'):
            return self._is_asymmetric
        
        from molecular_fragment_utils import is_asymmetric_dummy_atoms

        self._is_asymmetric = is_asymmetric_dummy_atoms(
            self.smiles,
            list(self.hasDummyAtomicNumber)[0],
        )

        return self._is_asymmetric
    
    @classmethod
    def from_mol_file(
        cls, 
        mol_file_path: str, 
        fragment_type: FragmentType,
        dummy_atomic_number: int = 0,
        **kwargs
    ) -> 'MolecularFragment':
        """
        Create a MolecularFragment instance from a .mol file.
        This method assumes that the .mol file contains the necessary geometry and properties.
        """
        from molecular_fragment_utils import load_molecular_fragment_from_mol_file

        # Load data including charge, molecular weight, molecular formula, atom_data, and smiles from the mol file
        data = load_molecular_fragment_from_mol_file(
            mol_file_path,
            dummy_atomic_number=dummy_atomic_number,
            **kwargs
        )

        charge = kwargs.get('charge', data["charge"])
        
        # Create a geometry object
        pts = []
        for atom in data["atoms"]:
            pt = Point(
                x=atom["coordinate_x"],
                y=atom["coordinate_y"], 
                z=atom["coordinate_z"],
                label=atom["label"]
            )
            pts.append(pt)

        geo = ontospecies.Geometry(
            hasPoints=pts,
            hasGeometryFile=mol_file_path,
        )

        # Create a MolecularFragment instance
        return cls(
            instance_iri=cls.init_instance_iri(),
            hasCharge=ontospecies.Charge(hasValue=om.Measure(hasNumericalValue=charge, hasUnit=om.elementaryCharge)),
            hasMolecularWeight=ontospecies.MolecularWeight(hasValue=om.Measure(hasNumericalValue=data["molecular_weight"], hasUnit=om.gramPerMole)),
            hasMolecularFormula=data["molecular_formula"],
            hasGeometry=geo,
            hasFragmentType=fragment_type,
            hasSmiles=data["smiles"],
            hasDummyAtomicNumber=dummy_atomic_number,
        )
    

############## ChemicalBuildingUnit Template ##############
## Object properties
HasFragmentConstraint = ObjectProperty.create_from_base('HasFragmentConstraint', OntoMOPs)
HasCBUFragmentTemplate = ObjectProperty.create_from_base('HasCBUFragmentTemplate', OntoMOPs)
HasChemicalBuildingUnitTemplate = ObjectProperty.create_from_base('HasChemicalBuildingUnitTemplate', OntoMOPs)
HasChemicalBuildingUnitFragment = ObjectProperty.create_from_base('HasChemicalBuildingUnitFragment', OntoMOPs)

## Data properties
HasFragmentPositions = DatatypeProperty.create_from_base('HasFragmentPositions', OntoMOPs)
HasFragmentOrientation = DatatypeProperty.create_from_base('HasFragmentOrientation', OntoMOPs)

class CBUFragmentTemplate(BaseClass): #TODO rename to CBUFragmentSlot
    rdfs_isDefinedBy = OntoMOPs
    hasFragmentType: HasFragmentType[FragmentType]
    hasFragmentPositions: HasFragmentPositions[int] # really only required for linkers
    
    @property
    def allowed_types(self) -> tuple[FragmentType, ...]:
        """All fragment classes that fulfil this slot."""
        return tuple(self.hasFragmentType)
    
    def accepts(self, frag: "MolecularFragment") -> bool:
        # return frag.hasFragmentType in self.allowed_types
        if frag.hasFragmentType & self.hasFragmentType:
            return True
        else:
            return False

    @property
    def is_linker_slot(self) -> bool:
        return any(isinstance(t, LinkerFragment) for t in self.allowed_types)

    @property
    def is_binding_slot(self) -> bool:
        return any(isinstance(t, BindingFragment) for t in self.allowed_types)
    
    @property
    def is_node_slot(self) -> bool:
        return any(isinstance(t, NodeFragment) for t in self.allowed_types)


class ChemicalBuildingUnitTemplate(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasGenericBuildingUnitType: HasGBUType[GenericBuildingUnitType]
    hasCBUFragmentTemplate: HasCBUFragmentTemplate[CBUFragmentTemplate]

    @property
    def gbu_type(self):
        return list(self.hasGenericBuildingUnitType)[0].label

    @property
    def all_allowed_types(self) -> Set[FragmentType]:
        """
        Returns a set of all fragment types that are allowed in this template.
        This includes all types from all CBUFragmentTemplates.
        """
        return {ft for slot in self.hasCBUFragmentTemplate for ft in slot.allowed_types}

    @property
    def linker_fragment_order(self) -> Dict:
        """
        Returns a mapping of fragment positions to allowed fragment types for linker slots.

        Returns:
            Dict[int, Set[FragmentType]]: A dictionary where keys are fragment positions (int)
            and values are sets of allowed FragmentType instances for those positions.
        """
        from collections import defaultdict
        pos2types = defaultdict(set)

        for slot in self.hasCBUFragmentTemplate:
            if slot.is_linker_slot:
                for pos in slot.hasFragmentPositions:
                    pos2types[pos].update(slot.allowed_types)

        # sort for determinism
        return dict(sorted(pos2types.items()))
    
    @classmethod
    def validate_template(cls, template):
        """
        check that has one binding group required and the positions of different fragments are not overlapping
        """
        if not template.hasCBUFragmentTemplate:
            raise ValueError("ChemicalBuildingUnitTemplate must have at least one CBUFragmentTemplate.")
        
        # Check that there is at least one binding fragment
        binding_fragments = [f for f in template.hasCBUFragmentTemplate if f.is_binding_slot]
        if not binding_fragments:
            raise ValueError("ChemicalBuildingUnitTemplate must have at least one binding fragment.")

        # Check that positions are unique
        all_positions = [pos for f in template.hasCBUFragmentTemplate for pos in f.hasFragmentPositions]
        if len(all_positions) != len(set(all_positions)):
            raise ValueError("ChemicalBuildingUnitTemplate has overlapping fragment positions.")
        
        return True

        

    def validate_fragment_list(self, fragments: List[MolecularFragment]) -> bool:
        """
        Validate the template against the provided fragments.
        This method checks if the fragments match the required types and positions defined in the template.
        """

        # every template slot is satisfied by at least one fragment
        # and every fragment matches at least one template slot
        for slot in self.hasCBUFragmentTemplate:
            if not any(slot.accepts(f) for f in fragments):
                return False
        if not all(any(slot.accepts(f) for slot in self.hasCBUFragmentTemplate)
                   for f in fragments):
            return False
        
        # for the linker fragments, check that the fragment types at each position/index match
        # only need to check these as the other slots are not strictly ordered
        linker_sets = self.linker_fragment_order
        for pos, allowed in linker_sets.items():
            if pos >= len(fragments):
                return False
            frag = fragments[pos]
            if not frag.is_linker_fragment:
                return False
            if not frag.hasFragmentType & allowed:
                return False

        return True

        


class ChemicalBuildingUnitFragment(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasMolecularFragment: HasMolecularFragment[MolecularFragment]
    hasFragmentPositions: HasFragmentPositions[int]
    hasFragmentOrientation: Optional[HasFragmentOrientation[int]] = None
    
####################################################


class ChemicalBuildingUnit(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    hasBindingDirection: HasBindingDirection[BindingDirection]
    hasBindingSite: Optional[HasBindingSite[BindingSite]]
    isFunctioningAs: IsFunctioningAs[GenericBuildingUnit]
    hasCharge: ontospecies.HasCharge[ontospecies.Charge]
    hasMolecularWeight: ontospecies.HasMolecularWeight[ontospecies.MolecularWeight]
    hasGeometry: Optional[ontospecies.HasGeometry[ontospecies.Geometry]]
    hasCBUFormula: HasCBUFormula[str]
    hasCBUAssemblyCenter: Optional[HasCBUAssemblyCenter[CBUAssemblyCenter]]

    hasChemicalBuildingUnitFragment: Optional[HasChemicalBuildingUnitFragment[ChemicalBuildingUnitFragment]] = None
    hasChemicalBuildingUnitTemplate: Optional[HasChemicalBuildingUnitTemplate[ChemicalBuildingUnitTemplate]] = None
    hasSmiles: Optional[HasSmiles[str]] = None

    @property
    def charge(self):
        return list(list(list(self.hasCharge)[0].hasValue)[0].hasNumericalValue)[0]

    @property
    def molecular_weight(self):
        return list(list(list(self.hasMolecularWeight)[0].hasValue)[0].hasNumericalValue)[0]

    @property
    def cbu_formula(self):
        return f"[{list(self.hasCBUFormula)[0].rstrip(']').lstrip('[')}]"

    @property
    def assembly_center(self):
        return list(self.hasCBUAssemblyCenter)[0].coordinates

    @property
    def highest_modularity_gbu(self):
        return max([gbu for gbu in list(self.isFunctioningAs)], key=lambda x: x.modularity)

    @property
    def is_metal_cbu(self):
        return all([isinstance(bs, MetalSite) for bs in list(self.hasBindingSite)])

    @property
    def active_binding_sites(self):
        return [bs for bs in list(self.hasBindingSite) if not bs.temporarily_blocked]

    def allocate_active_binding_sites(self, num: int):
        for bs in list(self.hasBindingSite)[num:]:
            bs.temporarily_blocked = True

    def release_blocked_binding_sites(self):
        for bs in self.hasBindingSite:
            bs.temporarily_blocked = False

    def load_geometry_from_fileserver(self, sparql_client):
        print("loading xyz from file server")
        return list(self.hasGeometry)[0].load_xyz_from_geometry_file(sparql_client)

    def add_binding_site_and_assembly_center_from_json(
        self, cbu_json_fpath, ocn, binding_fragment: str, gbu_type: str, metal_site: bool = False
    ):
        with open(cbu_json_fpath, "r") as file:
            cbu_json = json.load(file)
        binding_sites, assemb_center, atom_points = self.__class__.process_geometry_json(
            cbu_json, ocn, binding_fragment, gbu_type, metal_site)
        self.hasBindingSite = binding_sites
        self.hasCBUAssemblyCenter = assemb_center

    @staticmethod
    def process_geometry_json(cbu_json, ocn: int, binding_fragment: str, gbu_type: str, metal_site: bool = False):
        """
        Example of CBU json consisting of real atoms, dummy atoms as binding sites, and an optional "CENTER" point.
        Note that below coordinates are just for demonstration purpose, they do not represent any actual molecules.
        {
            "atom_uuid": {"atom": "C", "coordinate_x": 0.0, "coordinate_y": 0.0, "coordinate_z": 0.0},
            ...
            "dummy_uuid": {"atom": "X", "coordinate_x": -0.1, "coordinate_y": 2.1, "coordinate_z": 5.3},
            "CENTER": {"atom": "CENTER", "coordinate_x": 0.0, "coordinate_y": 0.0, "coordinate_z": 0.0}
        }
        """
        cbu_binding_points = {}
        lst_binding_sites = []
        cbu_atoms = {}
        atom_points = []
        cbu_atoms_acc_x = 0.0
        cbu_atoms_acc_y = 0.0
        cbu_atoms_acc_z = 0.0

        # iterate through the json file and process the coordinates
        _bs_clz = MetalSite if metal_site else OrganicSite
        for k, v in cbu_json.items():
            if v['atom'] == 'X':
                pt = _bs_clz(
                    hasOuterCoordinationNumber=ocn,
                    hasBindingPoint=BindingPoint(hasX=v['coordinate_x'], hasY=v['coordinate_y'], hasZ=v['coordinate_z']),
                    hasBindingFragment=binding_fragment,
                )
                cbu_binding_points[k] = pt
                lst_binding_sites.append(pt)
            elif str(v['atom']).lower() == 'center':
                print('NOTE!!! Center point is not used in the current implementation.')
            else:
                pt = Point(x=v['coordinate_x'], y=v['coordinate_y'], z=v['coordinate_z'], label=v['atom'])
                cbu_atoms_acc_x += v['coordinate_x']
                cbu_atoms_acc_y += v['coordinate_y']
                cbu_atoms_acc_z += v['coordinate_z']
                cbu_atoms[k] = pt
                atom_points.append(pt)

        assemb_center = BindingSite.compute_assembly_center_from_binding_sites(lst_binding_sites, atom_points, gbu_type, binding_fragment)

        return lst_binding_sites, assemb_center, atom_points

    @classmethod
    def from_geometry_json(cls, cbu_formula, cbu_json, charge, ocn, binding_fragment, gbu_type, gbu: str = None, direct_binding: bool = True, metal_site: bool = False):
        """
        Example of CBU json consisting of real atoms, dummy atoms as binding sites, and an optional "CENTER" point.
        Note that below coordinates are just for demonstration purpose, they do not represent any actual molecules.
        {
            "atom_uuid": {"atom": "C", "coordinate_x": 0.0, "coordinate_y": 0.0, "coordinate_z": 0.0},
            ...
            "dummy_uuid": {"atom": "X", "coordinate_x": -0.1, "coordinate_y": 2.1, "coordinate_z": 5.3},
            "CENTER": {"atom": "CENTER", "coordinate_x": 0.0, "coordinate_y": 0.0, "coordinate_z": 0.0}
        }
        """

        if not direct_binding:
            raise NotImplementedError("Non-direct binding, e.g. side binding, is not yet supported.")

        binding_sides, assemb_center, atom_points = cls.process_geometry_json(cbu_json, ocn, binding_fragment, gbu_type, metal_site)
        # prepare the geometry of the CBU
        cbu_iri = cls.init_instance_iri()
        cbu_xyz_file = f"{cbu_iri.split('/')[-1]}.xyz"
        cbu_geo = ontospecies.Geometry.from_points(atom_points, cbu_xyz_file)

        # instantiate actual CBU
        return cls(
            instance_iri=cbu_iri,
            # TODO hasBindingDirection should be modified once side-binding is implemented
            hasBindingDirection=DIRECT_BINDING,#'https://www.theworldavatar.com/kg/ontomops/DirectBinding_f3716525-0a8d-430f-ae24-0a043ec0c93a',
            hasBindingSite=binding_sides,
            isFunctioningAs=gbu if gbu is not None else set(),
            hasCharge=ontospecies.Charge(hasValue=om.Measure(hasNumericalValue=charge, hasUnit=om.elementaryCharge)),
            hasMolecularWeight=ontospecies.MolecularWeight.from_xyz_file(cbu_xyz_file),
            hasGeometry=cbu_geo,
            hasCBUFormula=cbu_formula,
            hasCBUAssemblyCenter=assemb_center
        )

    def create_cbu_from_ordered_fragments_and_template(
        template: ChemicalBuildingUnitTemplate,
        fragments: List[MolecularFragment],
        linker_first_dummy_idxs: List[int] = None,
        gbu: Optional[object] = None,
        # gbu_type: Optional[str] = None,
        sanitize: bool = True,
        optimize: bool = False,
        symmetric_linker_orientations: bool = False,
        **kwargs
    ) -> ChemicalBuildingUnit:
        """
        Assemble a single CBU from a fragment list whose order matches the template's
        slot order (sorted by min(hasFragmentPositions)). Fragments are duplicated and
        ordered by the global hasFragmentPositions, and linker orientation bits passed
        per-linker-slot are expanded to per-linker-position.

        Parameters
        ----------
        template : ChemicalBuildingUnitTemplate
        fragments : List[MolecularFragment]
            One fragment per slot, in the same order as the
            template's fragment slots when sorted by hasFragmentPositions.
        linker_first_dummy_idxs : List[int]
            One 0/1 orientation bit per linker slot (before expansion).
        symmetric_linker_orientations : bool
            If True, for an asymmetric linker occupying multiple positions in a
            single slot, the expanded bits will alternate (0,1,0,...) starting from
            the provided slot bit.

        TODO: change to providing the entire linker_first_dummy_idxs 
        """

        # canonical slot order
        frag_templates = sorted(
            template.hasCBUFragmentTemplate,
            key=lambda ft: min(ft.hasFragmentPositions)
        )

        if len(fragments) != len(frag_templates):
            raise ValueError(f"Expected {len(frag_templates)} fragments, got {len(fragments)}.")

        # validate fragments against template slots
        for frag, ft in zip(fragments, frag_templates):
            if not ft.accepts(frag):
                raise ValueError(f"Fragment {frag} does not match template slot {ft}.")

        # get position map and produce ordered frags and slots
        position_map = {}
        for frag, ft in zip(fragments, frag_templates):
            for pos in ft.hasFragmentPositions:
                position_map[pos] = (frag, ft)

        ordered_positions = sorted(position_map)
        ordered_pairs = [position_map[p] for p in ordered_positions]
        frags = [f for (f, _) in ordered_pairs]
        fts   = [t for (_, t) in ordered_pairs]

        # identify linker fragments and their positions in the ordered list
        linker_info = [
            (i, frags[i], fts[i]) for i in range(len(frags)) if frags[i].is_linker_fragment
        ]

        # map each slot to the indices it occupies within linker_info
        slot_positions_map = {}
        for idx_in_li, (_, frag_i, ft_i) in enumerate(linker_info):
            slot_positions_map.setdefault(ft_i, []).append(idx_in_li)

        # validate and expand the per-slot bits to per-linker-position bits
        linker_slot_pairs = [(frag, ft) for frag, ft in zip(fragments, frag_templates) if frag.is_linker_fragment]

        if linker_first_dummy_idxs is None: 
            linker_first_dummy_idxs = [0] * len(linker_info)

        if len(linker_first_dummy_idxs) != len(linker_slot_pairs):
            raise ValueError(
                f"Expected {len(linker_slot_pairs)} orientation bits (one per linker slot), "
                f"got {len(linker_first_dummy_idxs)}."
            )

        for b in linker_first_dummy_idxs:
            if b not in (0, 1):
                raise ValueError("Orientation bits must be 0 or 1.")

        # Prepare the final per-position orientation bits
        expanded_bits = [0] * len(linker_info)

        for slot_bit, (slot_frag, slot_ft) in zip(linker_first_dummy_idxs, linker_slot_pairs):
            li_indices = slot_positions_map.get(slot_ft)

            if symmetric_linker_orientations and slot_frag.is_asymmetric and len(li_indices) > 1:
                # Alternate 0/1 starting from the provided slot_bit
                for j, li_idx in enumerate(li_indices):
                    expanded_bits[li_idx] = slot_bit if (j % 2 == 0) else (1 - slot_bit)
            else:
                # Same bit for all positions belonging to this slot
                for li_idx in li_indices:
                    expanded_bits[li_idx] = slot_bit

        # assemble
        cbu = ChemicalBuildingUnit.from_molecular_fragments(
            fragments=frags,                         # one fragment per *position* in global order
            gbu_type=template.gbu_type,
            gbu=gbu,
            sanitize=sanitize,
            optimize=optimize,
            linker_first_dummy_idxs=expanded_bits,   # one bit per *linker position* in linker_info order
            **kwargs
        )
        cbu.hasChemicalBuildingUnitTemplate = {template}
        return cbu


    
    @classmethod
    def from_molecular_fragments(
        cls,
        fragments: List[MolecularFragment],
        gbu_type: str,
        gbu: Optional[GenericBuildingUnit] = None,
        direct_binding: bool = True,
        metal_site: bool = False,
        linker_first_dummy_idxs = None,
        **kwargs
    ) -> 'ChemicalBuildingUnit':
        from molecular_fragment_utils import assemble_fragments_to_cbu

        binding_fragments = [f for f in fragments if f.is_binding_fragment]
        linker_fragments = [f for f in fragments if f.is_linker_fragment]
        node_fragments = [f for f in fragments if f.is_node_fragment]

        cbu_frags = [ # TODO add direction
            ChemicalBuildingUnitFragment(
                hasMolecularFragment=frag,
                hasFragmentPositions=[i for i in range(len(fragments)) if fragments[i] == frag]
            ) for frag in set(fragments)
        ]

        if not direct_binding:
            raise NotImplementedError("Non-direct binding, e.g. side binding, is not yet supported.")
        if not binding_fragments: # what if wanted to assemble only linker and node fragments e.g. 4-planar cores? could use the frag util functions, same for substituting frags
            raise ValueError("The list of binding fragments is empty.")

        # TODO: reset all fragments to have the same dummy atomic number (maybe when load from mol file)
        dummy_atomic_number = {list(x.hasDummyAtomicNumber)[0] for x in fragments}
        if len(dummy_atomic_number) != 1:
            raise ValueError("Currently all fragments must have the same dummy atomic number.")
        
        dummy_atomic_number = list(dummy_atomic_number)[0]
        
        binding_group = binding_fragments[0]
        ocn = list(binding_group.fragment_type.hasOuterCoordinationNumber)[0]
        binding_atoms = list(binding_group.fragment_type.hasBindingFragment)[0]

        cbu_json, cbu_smiles, cbu_formula, cbu_mol_block = assemble_fragments_to_cbu(
            linker_mol_files=[list(x.hasGeometry)[0].geometry_file for x in linker_fragments],
            binding_group_mol_files = [list(x.hasGeometry)[0].geometry_file for x in binding_fragments][0],
            node_mol_files = [list(x.hasGeometry)[0].geometry_file for x in node_fragments][0] if node_fragments else None,
            dummy_atomic_number=dummy_atomic_number,
            linker_first_dummy_idxs=linker_first_dummy_idxs,
            **kwargs
        )

        cbu_charge = 0
        cbu_mw = 0
        
        for frag in fragments:
            cbu_charge += frag.charge
            cbu_mw += frag.molecular_weight

        binding_sites, assemb_center, atom_points = cls.process_geometry_json(
            cbu_json, 
            ocn, 
            binding_atoms,
            gbu_type, 
            metal_site
        )
        
        # prepare the geometry of the CBU   
        cbu_iri = cls.init_instance_iri()
        cbu_xyz_file = f"./new_cbus/{cbu_iri.split('/')[-1]}.xyz" # TODO: change to relative path to the kg
        cbu_geo = ontospecies.Geometry.from_points(atom_points, cbu_xyz_file)
            
        # instantiate actual CBU
        return cls(
            instance_iri=cls.init_instance_iri(),
            # TODO hasBindingDirection should be modified once side-binding is implemented
            hasBindingDirection=DIRECT_BINDING,#'https://www.theworldavatar.com/kg/ontomops/DirectBinding_f3716525-0a8d-430f-ae24-0a043ec0c93a',
            hasBindingSite=binding_sites,
            isFunctioningAs=gbu if gbu is not None else set(),
            hasCharge=ontospecies.Charge(hasValue=om.Measure(hasNumericalValue=cbu_charge, hasUnit=om.elementaryCharge)),
            hasMolecularWeight=ontospecies.MolecularWeight(hasValue=om.Measure(hasNumericalValue=cbu_mw, hasUnit=om.gramPerMole)),
            hasGeometry=cbu_geo,
            hasCBUFormula=cbu_formula,
            hasCBUAssemblyCenter=assemb_center,
            hasChemicalBuildingUnitFragment=cbu_frags,
            hasSmiles=cbu_smiles,
        )
    
    @classmethod
    def from_molecular_fragments_smiles(
        cls,
        fragments: List[MolecularFragment],
        gbu_type: str,
        gbu: Optional[GenericBuildingUnit] = None,
        direct_binding: bool = True,
        metal_site: bool = False,
        linker_first_dummy_idxs = None,
        **kwargs
    ) -> 'ChemicalBuildingUnit':
        from molecular_fragment_utils import smiles_assemble_fragments_to_cbu

        binding_fragments = [f for f in fragments if f.is_binding_fragment]
        linker_fragments = [f for f in fragments if f.is_linker_fragment]
        node_fragments = [f for f in fragments if f.is_node_fragment]

        cbu_frags = [
            ChemicalBuildingUnitFragment(
                hasMolecularFragment=frag,
                hasFragmentPositions=[i for i in range(len(fragments)) if fragments[i] == frag]
            ) for frag in set(fragments)
        ]

        if not direct_binding:
            raise NotImplementedError("Non-direct binding, e.g. side binding, is not yet supported.")
        if not binding_fragments: # what if wanted to assemble only linker and node fragments e.g. 4-planar cores? wouldnt' be a cbu, use the frag util functions, same for substituting frags
            raise ValueError("The list of binding fragments is empty.")

        # TODO: reset all fragments to have the same dummy atomic number (maybe when load from mol file)
        dummy_atomic_number = {list(x.hasDummyAtomicNumber)[0] for x in fragments}
        if len(dummy_atomic_number) != 1:
            raise ValueError("Currently all fragments must have the same dummy atomic number.")
        
        dummy_atomic_number = list(dummy_atomic_number)[0]
        
        binding_group = binding_fragments[0]
        ocn = list(binding_group.fragment_type.hasOuterCoordinationNumber)[0]
        binding_atoms = list(binding_group.fragment_type.hasBindingFragment)[0]

        cbu_smiles, cbu_formula = smiles_assemble_fragments_to_cbu(
            linker_smiles=[x.smiles for x in linker_fragments],
            binding_smiles = [x.smiles for x in binding_fragments][0],
            node_smiles = [x.smiles for x in node_fragments][0] if node_fragments else None,
            dummy_atomic_number=dummy_atomic_number,
            linker_first_dummy_idxs=linker_first_dummy_idxs,
            **kwargs
        )

        cbu_charge = 0
        cbu_mw = 0
        
        for frag in fragments:
            cbu_charge += frag.charge
            cbu_mw += frag.molecular_weight
            
        # instantiate actual CBU
        return cls(
            instance_iri=cls.init_instance_iri(),
            # TODO hasBindingDirection should be modified once side-binding is implemented
            hasBindingDirection=DIRECT_BINDING,#'https://www.theworldavatar.com/kg/ontomops/DirectBinding_f3716525-0a8d-430f-ae24-0a043ec0c93a',
            hasBindingSite=None,
            isFunctioningAs=gbu if gbu is not None else set(),
            hasCharge=ontospecies.Charge(hasValue=om.Measure(hasNumericalValue=cbu_charge, hasUnit=om.elementaryCharge)),
            hasMolecularWeight=ontospecies.MolecularWeight(hasValue=om.Measure(hasNumericalValue=cbu_mw, hasUnit=om.gramPerMole)),
            hasGeometry=None,
            hasCBUFormula=cbu_formula,
            hasCBUAssemblyCenter=None,
            hasChemicalBuildingUnitFragment=cbu_frags,
            hasSmiles=cbu_smiles,
            # hasMolecularFragment= linker_fragments + binding_fragments + node_fragments, # [*linker_fragments, *binding_fragments, *node_fragments],
        )


    @classmethod
    def combinations_from_template_and_fragments(
        cls,
        template: ChemicalBuildingUnitTemplate,
        fragments: List[MolecularFragment],
        unique_only=True,
        constraint_fn=None,
        assemble_smiles=False,
        max_cbus=None,
        symmetric_linker_orientations: bool = False, 
        **kwargs
    ) -> List[ChemicalBuildingUnit]:
        """
        Create all ChemicalBuildingUnit instances from the given fragments.

        Parameters
        ----------
        symmetric_linker_orientations : bool, optional
            If True, then for every *individual* fragment template that is an
            asymmetric linker AND has multiple positions, the first_dummy_index
            values of the fragments occupying those positions will be forced to
            alternate (e.g. only 0,1,0,1 or 1,0,1,0). This ensures only 
            symmetric metal environments are generated
            # TODO could just make sure the first and last are the same frag 
            # and opposite orientation, but this is more general
        """
        from itertools import product

        assemble_cbu_fn = (
            ChemicalBuildingUnit.from_molecular_fragments_smiles
            if assemble_smiles else
            ChemicalBuildingUnit.from_molecular_fragments
        )

        cbus = []
        unique_smiles = set()

        frag_templates = sorted(
            template.hasCBUFragmentTemplate,
            key=lambda ft: min(ft.hasFragmentPositions)
        )
        fragment_lists = [
            [f for f in fragments if ft.accepts(f)]
            for ft in frag_templates
        ]
        if any(len(lst) == 0 for lst in fragment_lists):
            raise ValueError("unfulfilled template positions, fragments do not match all required types.")

        total_combinations = 0
        for combo in product(*fragment_lists):
            # Map template position → (fragment, fragment_template)
            position_map = {}
            for frag, ft in zip(combo, frag_templates):
                for pos in ft.hasFragmentPositions:
                    position_map[pos] = (frag, ft)
            ordered = [position_map[p] for p in sorted(position_map)]

            frags = [f for f, _ in ordered]
            fts   = [t for _, t in ordered]

            if constraint_fn and not constraint_fn(frags, fts):
                continue

            # gather only linker fragments
            linker_info = [
                (i, frags[i], fts[i])
                for i in range(len(frags))
                if frags[i].is_linker_fragment
            ]
            # positions (inside linker_info) that are asymmetric
            asymm_slots = [
                idx for idx, (_, frag, _) in enumerate(linker_info)
                if frag.is_asymmetric
            ]

            # group asymmetric linker positions by their template 
            template_slot_map = {}
            for pos in asymm_slots:
                _, _, ft = linker_info[pos]
                template_slot_map.setdefault(ft, []).append(pos)

            # keep only those templates with >1 positions
            multi_pos_groups = {
                ft: slot_list
                for ft, slot_list in template_slot_map.items()
                if len(ft.hasFragmentPositions) > 1
            }

            # generate unique orientation bit combinations
            unique = []
            for bits in product([0, 1], repeat=len(asymm_slots)):
                # TODO does this work for nodes with one linker?
                # skip mirrored duplicates
                rev = bits[::-1]
                inv = tuple(1 - b for b in rev)
                if inv in unique:
                    continue

                if symmetric_linker_orientations and multi_pos_groups:
                    valid = True
                    for slot_list in multi_pos_groups.values():
                        # indices of bits that correspond to this template
                        sub = tuple(
                            bits[asymm_slots.index(sl)]
                            for sl in slot_list
                        )
                        if len(sub) > 1:
                            # require the bits alternate to be (psuedo)symmetric
                            if not all(sub[i] != sub[i+1] for i in range(len(sub)-1)):
                                valid = False
                                break
                    if not valid:
                        continue
                unique.append(bits)

            for bits in unique:
                linker_first_dummy = [0] * len(linker_info)
                for bit_idx, slot in enumerate(asymm_slots):
                    linker_first_dummy[slot] = bits[bit_idx]

                try:
                    cbu = assemble_cbu_fn(
                        fragments=frags,
                        gbu_type=template.gbu_type,
                        linker_first_dummy_idxs=linker_first_dummy,
                        **kwargs
                    )
                except Exception as e:
                    print(f"Skipping CBU due to assembly error: {e}")
                    continue

                smiles = next(iter(cbu.hasSmiles))
                if unique_only and smiles in unique_smiles:
                    if cbu.hasGeometry is not None:
                        os.remove(list(cbu.hasGeometry)[0].geometry_file)
                    continue
                unique_smiles.add(smiles)
                cbu.hasChemicalBuildingUnitTemplate = {template}
                cbus.append(cbu)
                total_combinations += 1

                if max_cbus is not None and total_combinations > max_cbus:
                    break
            if max_cbus is not None and total_combinations > max_cbus:
                break

        print("total CBU combinations assembled =", total_combinations)
        return cbus

    @property
    def vector_to_binding_site_plane(self):
        # get the center of the CBU
        center = list(self.hasCBUAssemblyCenter)[0].coordinates
        # get the line or plane of the binding sites
        binding_sites: List[BindingSite] = self.active_binding_sites
        if len(binding_sites) < 3:
            line = Line.from_two_points(start=binding_sites[0].binding_coordinates, end=binding_sites[1].binding_coordinates)
            if line.is_point_on_line(center):
                # if the center point is on the line then we approximate the plane fitted by the binding fragments of CBU
                # to each binding site and we take the normal vector of the plane
                lst_binding_atoms = []
                for bs in binding_sites:
                    lst_binding_atoms.extend(bs.binding_atoms(list(self.hasGeometry)[0].hasPoints))
                plane = Plane.fit_from_points(lst_binding_atoms)
                v = plane.normal_vector_from_point_to_plane(center)
            else:
                v = line.normal_vector_from_point_to_line(center)
        else:
            plane = Plane.fit_from_points([bs.binding_coordinates for bs in binding_sites])
            v = plane.normal_vector_from_point_to_plane(center)
        return v

    @property
    def vector_to_farthest_binding_site(self):
        # NOTE this needs to be after the rotation
        # find the plane perpendicular to the vector to the average connecting point
        center = list(self.hasCBUAssemblyCenter)[0].coordinates
        plane = Plane.from_point_and_normal(center, self.vector_to_binding_site_plane)
        # project all connecting points onto the plane
        projected_points = [plane.project_point(bs.binding_coordinates) for bs in self.active_binding_sites]
        # find the farthest binding site and construct a vector connecting the center to it
        farthest_projected_point = center.farthest_point(projected_points)
        vector = Vector.from_two_points(start=center, end=farthest_projected_point)
        return vector

    @property
    def vector_to_shortest_side(self):
        # NOTE this needs to be after the rotation
        # find the plane perpendicular to the vector to the average connecting point
        center = list(self.hasCBUAssemblyCenter)[0].coordinates
        plane = Plane.from_point_and_normal(center, self.vector_to_binding_site_plane)
        # project all connecting points onto the plane
        projected_points = [plane.project_point(bs.binding_coordinates) for bs in self.active_binding_sites]
        # find the closest pair of binding sites and construct a vector connecting the center to the line connecting them
        closest_pair = Point.closest_pair(projected_points)
        line = Line.from_two_points(start=closest_pair[0], end=closest_pair[1])
        v = line.normal_vector_from_point_to_line(center)
        return v

    def vector_of_most_possible_binding_site(self, gbu_plane: Plane, rotation_matrices: List[RotationMatrix] = [RotationMatrix.identity()]):
        # find the binding site that is most likely to bind with the other GBU
        # this is the one that has the smallest angle to the plane of the two GBU coordinate centers
        center: Point = list(self.hasCBUAssemblyCenter)[0].coordinates
        # rotate the binding sites with the rotation matrix
        most_possible_binding_site_angle = 90 # in degrees
        rotated_binding_vector = None
        length_center_to_binding = None
        for bs in self.active_binding_sites:
            bs: BindingSite
            v = Vector.from_two_points(start=center, end=bs.binding_coordinates)
            # rotate the vector to align with the GBU coordinate center
            for r in rotation_matrices:
                v = Vector.from_array(r.apply(v.as_array))
            angle = abs(90 - v.get_deg_angle_to(gbu_plane.normal))
            if angle < most_possible_binding_site_angle:
                rotated_binding_vector = v
                most_possible_binding_site_angle = angle
                # NOTE we are not rotating atoms here as we are computing the distance which are not changed before/after rotation
                # and we are using the original coordinates of the binding site, therefore the original coordinates of atoms would work
                binding_atoms = bs.binding_atoms(list(self.hasGeometry)[0].hasPoints)
                length_center_to_binding_atoms = center.get_distance_to(Point.centroid(binding_atoms))

                # NOTE here we are adjusting the length from center to binding fragment (atoms) to account for the half bond length (covalent radius)
                # although some of the binding site in the initial data already has additional length
                # i.e. the dummy atom already away from the actually binding atoms
                # we will compute on-the-fly to determine the suitable side length to be added
                # beyond the distance between assembly center to the binding atoms
                # NOTE TODO here we take the shortcut that we take the minimal covalent radius of the binding atoms as the half bond length
                # NOTE TODO to improve it, one might want to also consider the angle between the two sets of binding sites
                # NOTE TODO as the actual bond formed will be a projection of such added length
                # NOTE it's generally easier to optimise the geometry if the molecules are too far compared to overlapping (see SI of 10.1021/jp507643v)
                # NOTE so one could potentially add more distance to it to ensure there's no overlapping
                length_center_to_binding = length_center_to_binding_atoms + min([cap.PERIODIC_TABLE.GetRcovalent(a.label) for a in binding_atoms])
        return rotated_binding_vector, most_possible_binding_site_angle, length_center_to_binding

    def visualise(self, sparql_client = None):
        rows = []
        if list(self.hasGeometry)[0].hasPoints is None:
            if sparql_client is None:
                raise ValueError('SPARQL client is required to visualise/load the geometry')
            self.load_geometry_from_fileserver(sparql_client)
        # atoms
        for pt in list(self.hasGeometry)[0].hasPoints:
            rows.append([pt.label, pt.x, pt.y, pt.z])
        # binding sites
        for pt in list(self.hasBindingSite):
            rows.append(['BindingSite', pt.binding_coordinates.x, pt.binding_coordinates.y, pt.binding_coordinates.z])
        # assembly center
        rows.append(['AssemblyCenter', self.assembly_center.x, self.assembly_center.y, self.assembly_center.z])
        df = pd.DataFrame(rows, columns=['Atom', 'X', 'Y', 'Z',])
        fig = px.scatter_3d(df, x='X', y='Y', z='Z', color='Atom', title=f'CBU: {list(self.hasCBUFormula)[0]}')
        fig.update_traces(marker=dict(size=2))
        fig.update_layout(autosize=False, width=1200, height=400)
        fig.show()
        return fig


class CBUAssemblyTransformation(BaseClass):
    rdfs_isDefinedBy = OntoMOPs
    transforms: Transforms[ChemicalBuildingUnit]
    alignsTo: AlignsTo[GBUCoordinateCenter]
    quaternionToRotate: QuaternionToRotate[str]
    scaleFactorToAlignCoordinateCenter: ScaleFactorToAlignCoordinateCenter[float]
    translationVectorToAlignOrigin: TranslationVectorToAlignOrigin[str]

    @property
    def transformed_binding_sites(self):
        cbu = list(self.transforms)[0]
        if isinstance(cbu, str):
            cbu: ChemicalBuildingUnit = KnowledgeGraph.get_object_from_lookup(cbu)
        gcc = list(self.alignsTo)[0]
        if isinstance(gcc, str):
            gcc: GBUCoordinateCenter = KnowledgeGraph.get_object_from_lookup(gcc)
        # retrieve the active binding sites
        bs_points = [bs.binding_coordinates for bs in cbu.active_binding_sites]
        # rotate according to the quaternion
        rotation_matrix = Quaternion.from_string(list(self.quaternionToRotate)[0]).as_rotation_matrix()
        rotated_bs_points = [Point.from_array(rotation_matrix.apply(bs.as_array)) for bs in bs_points]
        # scale the rotated binding sites
        scaling_factor = list(self.scaleFactorToAlignCoordinateCenter)[0]
        translate_vector_for_scaling = Point.from_array(
            rotation_matrix.apply(list(cbu.hasCBUAssemblyCenter)[0].coordinates.as_array)
        ).get_translation_vector_to(Point.scale(gcc.coordinates, scaling_factor))
        scaled_bs_points = [Point.translate(bs, translate_vector_for_scaling) for bs in rotated_bs_points]
        # translation for the final alignment to minimise numerical errors
        translation_vector = Vector.from_string(list(self.translationVectorToAlignOrigin)[0])
        translated_bs_points = [Point.translate(bs, translation_vector) for bs in scaled_bs_points]
        return {gcc: translated_bs_points}


class MetalOrganicPolyhedron(CoordinationCage):
    hasAssemblyModel: HasAssemblyModel[AssemblyModel]
    hasCavity: Optional[HasCavity[Cavity]] = None
    hasChemicalBuildingUnit: HasChemicalBuildingUnit[ChemicalBuildingUnit]
    hasProvenance: HasProvenance[Provenance]
    hasCharge: ontospecies.HasCharge[ontospecies.Charge]
    hasMolecularWeight: ontospecies.HasMolecularWeight[ontospecies.MolecularWeight]
    hasGeometry: Optional[ontospecies.HasGeometry[ontospecies.Geometry]] = None
    hasCCDCNumber: Optional[HasCCDCNumber[str]] = None
    hasCBUAssemblyTransformation: Optional[HasCBUAssemblyTransformation[CBUAssemblyTransformation]] = None
    hasMOPFormula: HasMOPFormula[str]
    hasPoreSize: Optional[HasPoreSize[PoreSize]] = None
    hasOuterDiameter: Optional[HasOuterDiameter[om.Diameter]] = None
    hasCalculationResult: Optional[HasCalculationResult[CalculationResult]] = None

    @classmethod
    def from_assemble(
        cls,
        am: AssemblyModel,
        lst_cbu: List[ChemicalBuildingUnit],
        prov: Provenance = set(),
        ccdc: str = set(),
        sparql_client = None,
        upload_geometry: bool = False,
        data_dir: str = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            f'xyz_mops_{datetime.now().year}_{datetime.now().month}_{datetime.now().day}'
        ),
    ):
        # prepare the variables
        mop_charge = 0
        mop_mw = 0
        mop_formula = ''

        # locate the GBUs to build the AM
        gbus = list(am.hasGenericBuildingUnit)
        # place the CBUs according to the GBUs
        cbu_rotation_matrix = {}
        for cbu in lst_cbu:
            cbu: ChemicalBuildingUnit
            if list(cbu.hasGeometry)[0].hasPoints is None:
                if sparql_client is None:
                    raise ValueError('SPARQL client is required to visualise/load the geometry')
                list(cbu.hasGeometry)[0].load_xyz_from_geometry_file(sparql_client)
            gbu = cbu.isFunctioningAs.intersection(gbus)
            if len(gbu) == 0:
                raise ValueError(f'No GBU found for CBU {cbu.instance_iri} in AM {am.instance_iri}')
            elif len(gbu) > 1:
                raise ValueError(f'Multiple GBUs found for CBU {cbu.instance_iri} in AM {am.instance_iri}: {gbu}')
            else:
                gbu = gbu.pop()
            if type(gbu) is not GenericBuildingUnit:
                gbu: GenericBuildingUnit = KnowledgeGraph.get_object_from_lookup(gbu)
            # NOTE here we need to block the binding sites based on the GBU
            cbu.allocate_active_binding_sites(gbu.modularity)
            # TODO optimise below
            # rotate the CBU to match the GBU
            # rotate the vector from center to binding site plane of CBU to the vector from center to connecting point plane of GBU
            rotation_matrix_1 = {
                gbu_center.instance_iri: cbu.vector_to_binding_site_plane.get_rotation_matrix_to_parallel(
                    gbu_center.vector_to_connecting_point_plane, flip_if_180=True) for gbu_center in gbu.hasGBUCoordinateCenter
            }
            # rotate the normal vector of the line connecting the farthest pair of binding sites of CBU to the same vector of GBU
            # NOTE that here we are getting the rotation matrix for the vector that is already rotated
            rotation_matrix_2 = {}
            for gbu_center in gbu.hasGBUCoordinateCenter:
                gbu_center: GBUCoordinateCenter
                if gbu.is_4_planar:
                    second_vector_for_alignment_cbu = cbu.vector_to_shortest_side
                    second_vector_for_alignment_gbu = gbu_center.vector_to_shortest_side
                else:
                    second_vector_for_alignment_cbu = cbu.vector_to_farthest_binding_site
                    second_vector_for_alignment_gbu = gbu_center.vector_to_farthest_connecting_point
                rotated = rotation_matrix_1[gbu_center.instance_iri].apply(second_vector_for_alignment_cbu.as_array)
                rotated_cbu_center_to_binding_site_plane = Vector.from_array(rotation_matrix_1[gbu_center.instance_iri].apply(cbu.vector_to_binding_site_plane.as_array))
                rotation_matrix_2[gbu_center.instance_iri] = Vector.from_array(rotated).get_rotation_matrix_to_parallel(
                    second_vector_for_alignment_gbu, flip_if_180=True, base_axis_if_180=rotated_cbu_center_to_binding_site_plane)
            # put the two rotation matrix together
            cbu_rotation_matrix[cbu.instance_iri] = {
                gbu_center.instance_iri: [
                    rotation_matrix_1[gbu_center.instance_iri], rotation_matrix_2[gbu_center.instance_iri]
                ] for gbu_center in gbu.hasGBUCoordinateCenter
            }
            # calculate the charge and molecular weight of the MOP
            mop_charge += cbu.charge * len(gbu.hasGBUCoordinateCenter)
            mop_mw += cbu.molecular_weight * len(gbu.hasGBUCoordinateCenter)
            # prepare the mop_formula
            mop_formula += f'{cbu.cbu_formula}{len(gbu.hasGBUCoordinateCenter)}'

        # find any connecting point and its two ends of GBUs
        pair_gbu_center = list(am.pairs_of_connected_gbus.values())[0]
        gc1: GBUCoordinateCenter = pair_gbu_center[0]
        gc2: GBUCoordinateCenter = pair_gbu_center[1]
        v_gbu1: Vector = gc1.vector_from_am_center
        v_gbu2: Vector = gc2.vector_from_am_center
        # calculate the degree between the two GBUs vectors and the plane these two vectors form
        theta_rad = v_gbu1.get_rad_angle_to(v_gbu2)
        plane = Plane.from_two_vectors(v_gbu1, v_gbu2)
        # get the projection of the rotated CBU vectors (from coordinate center to binding site) onto the plane
        for cbu_iri, rm_to_gbu in cbu_rotation_matrix.items():
            # TODO optimise the below
            cbu = KnowledgeGraph.get_object_from_lookup(cbu_iri)
            if gc1.instance_iri in rm_to_gbu:
                # get the rotation matrix for the CBU, for the first GBU
                rm = rm_to_gbu[gc1.instance_iri]
                rotated_binding_vector_cbu1, vector_plane_angle_cbu1, adjusted_side_length_cbu1 = cbu.vector_of_most_possible_binding_site(plane, rm)
                projected_adjusted_side_length_cbu1 = adjusted_side_length_cbu1 * np.cos(np.deg2rad(vector_plane_angle_cbu1))
                projected_binding_vector_cbu1 = plane.get_projected_vector(rotated_binding_vector_cbu1)
                _gbu_projected_cbu_angle_cbu1 = projected_binding_vector_cbu1.get_rad_angle_to(v_gbu1)
                # NOTE the projected angle is the outer angle so we need to subtract it from pi
                gbu_projected_cbu_angle_cbu1 = np.pi - _gbu_projected_cbu_angle_cbu1
                l_vertical_cbu1 = projected_adjusted_side_length_cbu1 * np.sin(gbu_projected_cbu_angle_cbu1)
                distance_to_am_center_gbu1 = gc1.distance_to_am_center
            elif gc2.instance_iri in rm_to_gbu:
                # get the rotation matrix for the CBU, for the second GBU
                rm = rm_to_gbu[gc2.instance_iri]
                rotated_binding_vector_cbu2, vector_plane_angle_cbu2, adjusted_side_length_cbu2 = cbu.vector_of_most_possible_binding_site(plane, rm)
                projected_adjusted_side_length_cbu2 = adjusted_side_length_cbu2 * np.cos(np.deg2rad(vector_plane_angle_cbu2))
                projected_binding_vector_cbu2 = plane.get_projected_vector(rotated_binding_vector_cbu2)
                _gbu_projected_cbu_angle_cbu2 = projected_binding_vector_cbu2.get_rad_angle_to(v_gbu2)
                # NOTE the projected angle is the outer angle so we need to subtract it from pi
                gbu_projected_cbu_angle_cbu2 = np.pi - _gbu_projected_cbu_angle_cbu2
                l_vertical_cbu2 = projected_adjusted_side_length_cbu2 * np.sin(gbu_projected_cbu_angle_cbu2)
                distance_to_am_center_gbu2 = gc2.distance_to_am_center
            else:
                raise ValueError(f'No rotation matrix found for CBU {cbu.instance_iri} in AM {am.instance_iri}')
        # equation to solve: sin(omega)/l_vertical_cbu1 = sin(theta-omega)/l_vertical_cbu2
        initial_guess = theta_rad / 2
        omega = fsolve(lambda x: np.sin(x)/l_vertical_cbu1 - np.sin(theta_rad - x)/l_vertical_cbu2, initial_guess)
        shared_side = l_vertical_cbu1 / np.sin(omega)
        scaled_cbu1 = math.sqrt(projected_adjusted_side_length_cbu1**2 + shared_side**2 - 2*projected_adjusted_side_length_cbu1*shared_side*np.cos(np.pi - gbu_projected_cbu_angle_cbu1 - omega))
        scaled_cbu2 = math.sqrt(projected_adjusted_side_length_cbu2**2 + shared_side**2 - 2*projected_adjusted_side_length_cbu2*shared_side*np.cos(np.pi - gbu_projected_cbu_angle_cbu2 - (theta_rad - omega)))
        # calculate the scaling factor for the CBU
        scaling_factor_cbu1 = scaled_cbu1 / distance_to_am_center_gbu1
        scaling_factor_cbu2 = scaled_cbu2 / distance_to_am_center_gbu2

        # apply all rotation to the cbu
        # rotate the cbu to be parallel to the gbu
        cbu_translated = {}
        cbu_translation_vector = {}
        for cbu_iri, rm_to_gbu in cbu_rotation_matrix.items():
            # TODO optimise the below
            cbu = KnowledgeGraph.get_object_from_lookup(cbu_iri)
            if list(cbu.hasGeometry)[0].hasPoints is None:
                if sparql_client is None:
                    raise ValueError('SPARQL client is required to load the geometry')
                cbu.load_geometry_from_fileserver(sparql_client)
            dct_rotated = {
                gc: [Point.from_array(rm_to_gbu[gc][1].apply(rm_to_gbu[gc][0].apply(pt.as_array)), label=pt.label) for pt in list(cbu.hasGeometry)[0].hasPoints] for gc in rm_to_gbu
            }
            # find the translation vector of the cbu center to the gbu center
            # note that the gbu center need to be the scaled version of the gbu center
            dct_translation_vector = {
                gc: Point.from_array(
                        rm_to_gbu[gc][1].apply(rm_to_gbu[gc][0].apply(list(cbu.hasCBUAssemblyCenter)[0].coordinates.as_array))
                    ).get_translation_vector_to(
                        Point.scale(
                            KnowledgeGraph.get_object_from_lookup(gc).coordinates,
                            scaling_factor_cbu1 if gc1.instance_iri in rm_to_gbu else scaling_factor_cbu2
                        )
                    ) for gc in rm_to_gbu
            }
            # translate the cbu to the gbu
            dct_translated = {
                gc: [Point.translate(pt, dct_translation_vector[gc]) for pt in dct_rotated[gc]] for gc in rm_to_gbu
            }
            cbu_translated[cbu_iri] = dct_translated
            cbu_translation_vector[cbu_iri] = dct_translation_vector

        # shift all atoms to have center at (0, 0, 0)
        # this makes sure the numerical error is minimised
        _lst_points = []
        for cbu, gcc_pts in cbu_translated.items():
            for gcc, pts in gcc_pts.items():
                _lst_points.extend(pts)
        _atoms = [p for p in _lst_points if p.label.lower() not in ['x', 'center']]
        adjusted_atoms, translation_vector_to_origin = Point.translate_points_to_target_centroid(_atoms, Point.from_array([0, 0, 0]))

        # collect information on the CBU transformation
        cbu_assembly_transformation_lst = []
        cbu_binding_sites_transformation_dct = {}
        for cbu_iri, rm_to_gbu in cbu_rotation_matrix.items():
            for gc in rm_to_gbu:
                cbu_transformation = CBUAssemblyTransformation(
                    transforms=cbu_iri,
                    alignsTo=gc,
                    quaternionToRotate=rm_to_gbu[gc][1].combine(rm_to_gbu[gc][0]).as_quaternion_str(),
                    scaleFactorToAlignCoordinateCenter=scaling_factor_cbu1 if gc1.instance_iri in rm_to_gbu else scaling_factor_cbu2,
                    translationVectorToAlignOrigin=translation_vector_to_origin.as_str()
                )
                cbu_assembly_transformation_lst.append(cbu_transformation)
                cbu_binding_sites_transformation_dct.update(cbu_transformation.transformed_binding_sites)

        # calculate cavity (in terms of largest inner sphere diameter), outer diameter, and pore size diameter
        inner_diameter_atom, inner_diameter, inner_volume = cap.largest_inner_sphere_diameter(adjusted_atoms)
        outer_diameter = cap.outer_diameter(adjusted_atoms)
        pore_sizes = []
        for pr in am.hasPoreRing:
            pr: PoreRing
            lst_of_points_for_probing_vector = []
            pair_gbus = pr.pair_of_ring_forming_gbus
            for pair in pair_gbus.values():
                pair_of_binding_sites = Point.closest_pair_across_lists(cbu_binding_sites_transformation_dct[pair[0]], cbu_binding_sites_transformation_dct[pair[1]])
                lst_of_points_for_probing_vector.extend(pair_of_binding_sites)
            probing_vector: Vector = Vector.from_two_points(start=Point(x=0, y=0, z=0), end=Point.centroid(lst_of_points_for_probing_vector))
            ps_val = cap.pore_size_diameter(adjusted_atoms, probing_vector)
            pore_sizes.append(
                PoreSize(
                    measuresPoreRing=pr,
                    hasProbingVector=probing_vector.as_str(),
                    hasPoreDiameter=om.Diameter(hasValue=om.Measure(hasNumericalValue=ps_val, hasUnit=om.angstrom)),
                )
            )

        # prepare the geometry file and upload
        mop_iri = cls.init_instance_iri()
        local_file_path = os.path.join(data_dir, f"{list(am.rdfs_label)[0]}_{list(am.hasSymmetryPointGroup)[0]}___{mop_formula}___{mop_iri.split('/')[-1] if not bool(ccdc) else ccdc}.xyz")
        mop_geo = ontospecies.Geometry.from_points(adjusted_atoms, local_file_path)
        if upload_geometry:
            # upload the geometry to the KG
            if sparql_client is None:
                raise ValueError('SPARQL client is required to upload the geometry')
            else:
                remote_file_path, timestamp_upload = sparql_client.upload_file(local_file_path)
                mop_geo.hasGeometryFile = {remote_file_path}

        # release the blocked binding sites
        for cbu in lst_cbu:
            cbu.release_blocked_binding_sites()

        return cls(
            instance_iri=mop_iri,
            hasAssemblyModel=am,
            hasChemicalBuildingUnit=lst_cbu,
            hasProvenance=prov,
            hasCharge=ontospecies.Charge(hasValue=om.Measure(hasNumericalValue=mop_charge, hasUnit=om.elementaryCharge)),
            hasMolecularWeight=ontospecies.MolecularWeight(hasValue=om.Measure(hasNumericalValue=mop_mw, hasUnit=om.gramPerMole)),
            hasMOPFormula=mop_formula,
            hasCCDCNumber=ccdc,
            hasGeometry=mop_geo,
            hasCavity=Cavity(hasLargestInnerSphereDiameter=om.Diameter(hasValue=om.Measure(hasNumericalValue=inner_diameter, hasUnit=om.angstrom))),
            hasOuterDiameter=om.Diameter(hasValue=om.Measure(hasNumericalValue=outer_diameter, hasUnit=om.angstrom)),
            hasPoreSize=pore_sizes,
            hasCBUAssemblyTransformation=cbu_assembly_transformation_lst
        )

    def visualise(self, sparql_client = None):
        rows = []
        if list(self.hasGeometry)[0].hasPoints is None:
            if sparql_client is None:
                raise ValueError('SPARQL client is required to visualise/load the geometry')
            list(self.hasGeometry)[0].load_xyz_from_geometry_file(sparql_client)
        for pt in list(self.hasGeometry)[0].hasPoints:
            rows.append([pt.label, pt.x, pt.y, pt.z])
        df = pd.DataFrame(rows, columns=['Atom', 'X', 'Y', 'Z',])
        fig = px.scatter_3d(df, x='X', y='Y', z='Z', color='Atom', title=f'MOP: {list(self.hasMOPFormula)[0]}\n AM: {list(self.hasAssemblyModel)[0].instance_iri}')
        fig.update_traces(marker=dict(size=2))
        fig.update_layout(autosize=False, width=1200, height=400)
        fig.show()
        return fig


    def has_cbu_overlaps(self, threshold_factor: float = 1.2) -> bool:
        """
        Check for any atom–atom overlaps between distinct organic CBUs.

        An overlap is flagged if any inter-CBU distance <
        threshold_factor * (r_cov_i + r_cov_j),
        where r_cov is the covalent radius from cap.PERIODIC_TABLE.

        Returns
        -------
        overlap_detected : bool
        """
        from scipy.spatial import distance_matrix
        import itertools

        cbu_coords = []
        cbu_radii  = []

        for t in self.hasCBUAssemblyTransformation:
            cbu_iri = next(iter(t.transforms))
            cbu = KnowledgeGraph.get_object_from_lookup(cbu_iri)
            if cbu.is_metal_cbu:
                continue

            geo = next(iter(cbu.hasGeometry))
            if geo.hasPoints is None:
                raise ValueError(f"Geometry for CBU {cbu_iri} not loaded.")
            binding_atoms = [
                atom for atom in geo.hasPoints
                if atom.label.lower() not in ('x', 'center')
            ]

            pts = np.array([atom.as_array for atom in binding_atoms])
            radii = np.array([
                cap.PERIODIC_TABLE.GetRcovalent(atom.label)
                for atom in binding_atoms
            ])

            quat = next(iter(t.quaternionToRotate))
            R = Quaternion.from_string(quat).as_rotation_matrix()
            pts = np.array([R.apply(p) for p in pts])

            s = next(iter(t.scaleFactorToAlignCoordinateCenter))
            cbu_ctr = next(iter(cbu.hasCBUAssemblyCenter)).coordinates.as_array
            gcc_iri = next(iter(t.alignsTo))
            gcc = KnowledgeGraph.get_object_from_lookup(gcc_iri)
            gcc_pts = gcc.coordinates.as_array * s
            pts += (gcc_pts - R.apply(cbu_ctr))
            vec = Vector.from_string(
                next(iter(t.translationVectorToAlignOrigin))
            ).as_array
            pts += vec

            cbu_coords.append(pts)
            cbu_radii.append(radii)

        for i, j in itertools.combinations(range(len(cbu_coords)), 2):
            A, B = cbu_coords[i], cbu_coords[j]
            ra, rb = cbu_radii[i], cbu_radii[j]
            D = distance_matrix(A, B)
            T = threshold_factor * (ra[:, None] + rb[None, :])
            if np.any(D < T):
                return True

        return False
# =============================== #
#         calculations            #
# =============================== #


# === object properties ===
HasCalculationMethod    = ObjectProperty.create_from_base('HasCalculationMethod', OntoMOPs)
HasCalculatedProperty   = ObjectProperty.create_from_base('HasCalculatedProperty', OntoMOPs)
HasCalculationParameter = ObjectProperty.create_from_base('HasCalculationParameter', OntoMOPs)
HasCalculationResult = ObjectProperty.create_from_base('HasCalculationResult', OntoMOPs)
HasOutputGeometry = ObjectProperty.create_from_base('HasOutputGeometry', OntoMOPs)
HasSoftware = ObjectProperty.create_from_base('HasSoftware', OntoMOPs)


# === Data properties ===
HasName = DatatypeProperty.create_from_base("HasName", OntoMOPs) # could alternatively use rdfs:label but this would then be implicit and not ideal for filter queries
HasLiteralValue = DatatypeProperty.create_from_base("HasLiteralValue", OntoMOPs)
HasSoftwareVersion = DatatypeProperty.create_from_base("HasSoftwareVersion", OntoMOPs)
HasNumericValue = DatatypeProperty.create_from_base("HasNumericValue", OntoMOPs)
HasLiteralUnit = DatatypeProperty.create_from_base("HasLiteralUnit", OntoMOPs)

# === classes ===
class Software(BaseClass):
    """The software package used to run a calculation."""
    rdfs_isDefinedBy = OntoMOPs
    hasName: HasName[str] # e.g. "Gaussian16", "LAMMPS"
    hasSoftwareVersion: HasSoftwareVersion[str]

class CalculationParameter(BaseClass):
    """One parameter used in a calculation (value + unit)."""
    rdfs_isDefinedBy = OntoMOPs
    hasName: HasName[str] # e.g. "cutoff energy"

class NumericCalculationParameter(CalculationParameter):
    rdfs_isDefinedBy = OntoMOPs
    hasNumericValue:  HasNumericValue[float]
    hasLiteralUnit: HasLiteralUnit[str]

class StringCalculationParameter(CalculationParameter):
    rdfs_isDefinedBy = OntoMOPs
    hasLiteralValue: HasLiteralValue[str]

class CalculationMethod(BaseClass):
    """How the calculation was performed."""
    rdfs_isDefinedBy = OntoMOPs
    hasCalculationParameter: HasCalculationParameter[CalculationParameter]
    hasSoftware: HasSoftware[Software]

class CalculatedProperty(BaseClass):
    """A computed result from the calculation."""
    rdfs_isDefinedBy = OntoMOPs
    hasNumericValue:  HasNumericValue[float]
    hasLiteralUnit: HasLiteralUnit[str]
    hasName: HasName[str] # e.g. "total energy", "HOMO-LUMO gap"

class CalculationResult(BaseClass):
    """
    The result of a calculation
    """
    rdfs_isDefinedBy = OntoMOPs
    hasOutputGeometry: HasOutputGeometry[ontospecies.Geometry]
    hasCalculationMethod:  HasCalculationMethod[CalculationMethod]
    hasCalculatedProperty: HasCalculatedProperty[CalculatedProperty]

    @classmethod
    def from_software_parameters_properties(
        cls,
        software: dict,
        parameters: list,
        properties: list,
        output_geometry: ontospecies.Geometry
    ):
        """
        Construct a CalculationResult from raw software metadata, calculation parameters,
        computed properties, and an output geometry.

        This factory method wraps the given software info in a Software object, converts
        each entry in `parameters` into either a StringCalculationParameter or
        NumericCalculationParameter, groups them into a CalculationMethod, then does the
        same for each entry in `properties` to produce a set of CalculatedProperty objects.
        Finally it returns a new CalculationResult bundling the geometry, properties, and method.

        Args:
            software (dict):
                A dict containing:
                - "name" (str): the software package name (e.g. "Gaussian").
                - "version" (str): the software version (e.g. "16").
            parameters (List[Tuple]):
                A list of 2- or 3-tuples describing calculation parameters:
                - (name: str, literal_value: str) for string parameters, or
                - (name: str, numeric_value: Union[int,float], unit: str) for numeric parameters.
            properties (List[Tuple]):
                A list of 3-tuples describing computed properties:
                - (name: str, numeric_value: Union[int,float], unit: str).
            output_geometry (ontospecies.Geometry):
                The geometry object produced by the calculation.

        Returns:
            CalculationResult:
                An object containing:
                - hasOutputGeometry: the provided `output_geometry`
                - hasCalculatedProperty: a set of CalculatedProperty objects
                - hasCalculationMethod: a CalculationMethod wrapping the software and its parameters

        Example:
            >>> geom = ontospecies.Geometry(...)
            >>> result = CalculationResult.from_software_parameters_properties(
            ...     software={"name": "Gaussian", "version": "16"},
            ...     parameters=[
            ...         ("method", "HF"),
            ...         ("basis", "6-31G*"),
            ...         ("thresh", 1e-6, "unitless")
            ...     ],
            ...     properties=[
            ...         ("energy", -75.0234, "hartree"),
            ...         ("dipole", 1.23, "Debye")
            ...     ],
            ...     output_geometry=geom
            ... )
        """

        software = Software(
            hasName=software["name"],
            hasSoftwareVersion=software["version"],
        )
        calc_params=[]

        for param in parameters:
            if len(param) == 2:
                calc_params.append(
                    StringCalculationParameter(hasName=param[0], hasLiteralValue=param[1])
                )
            else:
                calc_params.append(
                    NumericCalculationParameter(hasName=param[0], hasNumericValue=float(param[1]), hasLiteralUnit=param[2]),
                )

        calc_method = CalculationMethod(
            hasSoftware=software,
            hasCalculationParameter=set(calc_params),
        )

        properties = []
        for prop in properties:
            properties.append(CalculatedProperty(
                hasName=prop[0],
                hasNumericValue=prop[1],
                hasLiteralUnit=prop[2],
            ))


        return CalculationResult(
            hasOutputGeometry=output_geometry,
            hasCalculatedProperty=set(properties),
            hasCalculationMethod=calc_method,
        )

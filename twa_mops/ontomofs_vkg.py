from twa.data_model.base_ontology import BaseOntology, BaseClass, ObjectProperty, DatatypeProperty, KnowledgeGraph
import os
from typing import Optional, Dict, List, ClassVar
from om import *

class OntoMOFs_vkg(BaseOntology): 
    base_url = 'https://www.theworldavatar.com/kg'
    namespace = 'ontomofs_vkg'
    owl_versionInfo = '1.1-ogm'
    rdfs_comment = 'An (vkg) ontology developed for representing Metal-Organic Frameworks (MOFs). This is object graph mapper (OGM) version.'

HasTopology = ObjectProperty.create_from_base('HasTopology',OntoMOFs_vkg)
HasPoreDiameter = ObjectProperty.create_from_base('HasPore',OntoMOFs_vkg)
HasSurfaceArea = ObjectProperty.create_from_base('HasSurfaceArea',OntoMOFs_vkg)
HasPoreVolume = ObjectProperty.create_from_base('HasPoreVolume',OntoMOFs_vkg)
HasCrystalStructure = ObjectProperty.create_from_base('HasCrystalStructure',OntoMOFs_vkg)
HasSynthesis = ObjectProperty.create_from_base('HasSynthesis',OntoMOFs_vkg)
HasStability = ObjectProperty.create_from_base('HasStability',OntoMOFs_vkg)
HasProperty = ObjectProperty.create_from_base('HasProperty', OntoMOFs_vkg)
HasChemicalIdentity = ObjectProperty.create_from_base('HasChemicalIdentity', OntoMOFs_vkg)
HasProvenance = ObjectProperty.create_from_base('HasProvenance', OntoMOFs_vkg)
HasIdentifiers = ObjectProperty.create_from_base('HasIdentifiers', OntoMOFs_vkg)
HasElectronicStructure = ObjectProperty.create_from_base('HasElectronicStructure', OntoMOFs_vkg)
HasHeatCapacity = ObjectProperty.create_from_base('HasHeatCapacity',OntoMOFs_vkg)

HasRoutetype = DatatypeProperty.create_from_base('HasRoutetype',OntoMOFs_vkg)
HasNodeSmile = DatatypeProperty.create_from_base('HasNode',OntoMOFs_vkg)
HasLinkerSmile = DatatypeProperty.create_from_base('HasLinker',OntoMOFs_vkg)
HasRCSRSym = DatatypeProperty.create_from_base('HasRCSRSym',OntoMOFs_vkg)
HasCatenation = DatatypeProperty.create_from_base('HasCatenation',OntoMOFs_vkg)
HasDimension = DatatypeProperty.create_from_base('HasDimension',OntoMOFs_vkg)
Hasmofid_v1 = DatatypeProperty.create_from_base('Hasmofid_v1',OntoMOFs_vkg)
Hasmofid_v2 = DatatypeProperty.create_from_base('Hasmofid_v2',OntoMOFs_vkg)
Hascsd_refcode = DatatypeProperty.create_from_base('Hascsd_refcode',OntoMOFs_vkg)
Hashypo_id = DatatypeProperty.create_from_base('Hashypo_id',OntoMOFs_vkg)
HasSourcedb = DatatypeProperty.create_from_base('HasSourcedb',OntoMOFs_vkg)
Hasdb_id = DatatypeProperty.create_from_base('Hasdb_id',OntoMOFs_vkg)
IsExperimental = DatatypeProperty.create_from_base('IsExperimental',OntoMOFs_vkg)
IsHypothetical = DatatypeProperty.create_from_base('IsHypothetical', OntoMOFs_vkg)
IsSimulated = DatatypeProperty.create_from_base('IsSimulated',OntoMOFs_vkg)
HasReportedScale = DatatypeProperty.create_from_base('HasReportedScale',OntoMOFs_vkg)
HasTemperature = DatatypeProperty.create_from_base('HasTemperature',OntoMOFs_vkg)
HasPressure = DatatypeProperty.create_from_base('HasPressure',OntoMOFs_vkg)
HasSpaceGroupNumber = DatatypeProperty.create_from_base('HasSpaceGroupNumber', OntoMOFs_vkg)
HasLCD = DatatypeProperty.create_from_base('HasLCD',OntoMOFs_vkg)
HasPLD = DatatypeProperty.create_from_base('HasPLD',OntoMOFs_vkg)
HasLFPD = DatatypeProperty.create_from_base('HasLFPD',OntoMOFs_vkg)
HasNames = DatatypeProperty.create_from_base('HasNames',OntoMOFs_vkg)
HasPV = DatatypeProperty.create_from_base('HasPV',OntoMOFs_vkg)
HasNPV = DatatypeProperty.create_from_base('HasNPV',OntoMOFs_vkg)
HasVF = DatatypeProperty.create_from_base('HasVF',OntoMOFs_vkg)
HasNVF = DatatypeProperty.create_from_base('HasNVF',OntoMOFs_vkg)
HasNGPV = DatatypeProperty.create_from_base('HasNGPV',OntoMOFs_vkg)
HasGPV = DatatypeProperty.create_from_base('HasGPV',OntoMOFs_vkg)
HasThermalStability = DatatypeProperty.create_from_base('HasThermalStability',OntoMOFs_vkg)
HasKHwater = DatatypeProperty.create_from_base('HasKHwater',OntoMOFs_vkg)
HasSolventStability = DatatypeProperty.create_from_base('HasSolventStability',OntoMOFs_vkg)
HasASA = DatatypeProperty.create_from_base('HasASA',OntoMOFs_vkg)
HasNASA = DatatypeProperty.create_from_base('HasNASA',OntoMOFs_vkg)
HasGSA = DatatypeProperty.create_from_base('HasGSA',OntoMOFs_vkg)
HasNGSA = DatatypeProperty.create_from_base('HasNGSA',OntoMOFs_vkg)
HasVSA = DatatypeProperty.create_from_base('HasVSA',OntoMOFs_vkg)
HasNVSA = DatatypeProperty.create_from_base('HasNVSA',OntoMOFs_vkg)
HasDensity = DatatypeProperty.create_from_base('HasDensity',OntoMOFs_vkg)
HasMetal = DatatypeProperty.create_from_base('HasMetal',OntoMOFs_vkg)
HasOpenMetalSite = DatatypeProperty.create_from_base('HasOpenMetalSite',OntoMOFs_vkg)
HasMass = DatatypeProperty.create_from_base('HasMass',OntoMOFs_vkg)
HasUnitCellFormula = DatatypeProperty.create_from_base('HasUnitCellFormula',OntoMOFs_vkg) 
HasEmpiricalFormula = DatatypeProperty.create_from_base('HasEmpiricalFormula',OntoMOFs_vkg)
HasYearPublished = DatatypeProperty.create_from_base('HasYearPublished', OntoMOFs_vkg)
HasReferenceDOI = DatatypeProperty.create_from_base('HasReferenceDOI', OntoMOFs_vkg)
HasSymmetryPointGroup = DatatypeProperty.create_from_base('HasSymmetryPointGroup', OntoMOFs_vkg)
HasUnitCellVolume = DatatypeProperty.create_from_base('HasUnitCellVolume', OntoMOFs_vkg)
HasPropertyType = DatatypeProperty.create_from_base('HasPropertyType',OntoMOFs_vkg)
HasPropertyMethod = DatatypeProperty.create_from_base('HasPropertyMethod', OntoMOFs_vkg)
HasUncertainty = DatatypeProperty.create_from_base('HasUncertainty', OntoMOFs_vkg)
HasWaterStability = DatatypeProperty.create_from_base('HasWaterStability', OntoMOFs_vkg)
HasSolvent = DatatypeProperty.create_from_base('HasSolvent',OntoMOFs_vkg)

#Hasciffile = ????

class Provenance(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasReferenceDOI: HasReferenceDOI[str]
    hasYearPublished: HasYearPublished[str] # hasOriginalPublicationYear???????

class Topology(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasRCSRSym: HasRCSRSym[str]
    hasCatenation: HasCatenation[int]
    hasDimension: HasDimension[int]

class PoreDiameter(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasPLD: HasPLD[float] #Pore-Limiting Diameter by Zeo++ in Angstroms
    hasLCD: HasLCD[float] #Largest Cavity Diameter by Zeo++ in Angstroms
    hasLFPD: Optional[HasLFPD[float]] = None #Largest Free Pore Diameter by Zeo++ in Angstroms
    
class SurfaceArea(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasASA: Optional[HasASA[float]] = None
    hasNASA: Optional[HasNASA[float]] = None
    hasGSA: Optional[HasGSA[float]] = None
    hasNGSA: Optional[HasNGSA[float]] = None
    hasVSA: Optional[HasVSA[float]] = None
    hasNVSA: Optional[HasNVSA[float]] = None

class PoreVolume(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasPV: HasPV[float]
    hasNPV: HasNPV[float]
    hasGPV: Optional[HasGPV[float]] = None
    hasNGPV: Optional[HasNGPV[float]] = None
    hasVF: HasVF[float]
    hasNVF: HasNVF[float]

class CrystalStructure(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasSpaceGroupNumber: HasSpaceGroupNumber[int]
    hasSymmetryPointGroup: Optional[HasSymmetryPointGroup[str]] = None
    hasDensity: Optional[HasDensity[float]] = None 
    hasUnitCellVolume: Optional[HasUnitCellVolume[float]] = None

class Stability(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasThermalStability: Optional[HasThermalStability[float]] = None #in C
    hasSolventStability: Optional[HasSolventStability[float]] = None #0-1
    hasWaterStability: Optional[HasWaterStability[float]] = None #0-1
    hasKHwater: Optional[HasKHwater[str]] = None #Weak,Strong etc

class HeatCapacity(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasNumericalValue: HasNumericalValue[float]
    hasTemperature: HasTemperature[float]
    hasUncertainty: Optional[HasUncertainty[float]] = None

class Property(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasPropertyType: HasPropertyType[str] #This would just be like 'CO2 uptake','Selectivity_CO"/N2' etc
    hasValue: HasValue[Measure]
    hasUnits: HasUnit[Unit]
    isExperimental: IsExperimental[bool]
    isSimulated: IsSimulated[bool]
    hasMethod: HasPropertyMethod[str]
    hasTemperature: Optional[HasTemperature[float]] #in K 
    hasPressure: Optional[HasPressure[float]] #in bar??? 

class Synthesis(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasRoutetype: HasRoutetype[str] #This would be like solvothermal, mecahnochemical etc 
    hasTemperature: HasTemperature[float]
    hasPressure: HasPressure[float]
    hasReportedScale: Optional[HasReportedScale[float]] = None
    hasSolvent: Optional[HasSolvent[str]] = None 

class Identifiers(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasmofid_v1: Hasmofid_v1[str]
    hasmofid_v2: Optional[Hasmofid_v2[str]] = None
    hascsd_refcode: Optional[Hascsd_refcode[str]] = None
    hasdb_id: Optional[Hasdb_id[str]] = None
    hashypo_id: Optional[Hashypo_id[str]] = None
    hasNames: Optional[HasNames[str]] = None #.............???????????

class ChemicalIdentity(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasUnitCellFormula: Optional[HasUnitCellFormula[str]] = None
    hasEmpiricalFormula: Optional[HasEmpiricalFormula[str]] = None 
    hasMetal: Optional[HasMetal[str]] = None
    hasOpenMetalSite: Optional[HasOpenMetalSite[str]] = None
    hasMass: Optional[HasMass[float]] = None

class ElectronicStructure(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    pass 

class MetalOrganicFramework(BaseClass):
    rdfs_isDefinedBy = OntoMOFs_vkg
    hasIdentifiers: HasIdentifiers[Identifiers]
    hasNodeSmile: Optional[HasNodeSmile[str]] = None
    hasLinkerSmile: Optional[HasLinkerSmile[str]] = None
    hasTopology: HasTopology[Topology]
    hasSourcedb: HasSourcedb[str]
    hasProvenance: HasProvenance[Provenance]
    hasPoreDiameter: HasPoreDiameter[PoreDiameter]
    hasSurfaceArea: HasSurfaceArea[SurfaceArea]
    hasPoreVolume: HasPoreVolume[PoreVolume]
    isExperimental: IsExperimental[bool]
    isHypothetical: IsHypothetical[bool]
    hasSynthesis: Optional[HasSynthesis[Synthesis]] = None
    hasStability: Optional[HasStability[Stability]] = None
    hasHeatCapacity: Optional[HasHeatCapacity[HeatCapacity]] = None
    hasChemicalIdentity: Optional[HasChemicalIdentity[ChemicalIdentity]] = None
    hasProperty: Optional[HasProperty[Property]] = None
    hasElectronicStructure: Optional[HasElectronicStructure[ElectronicStructure]] = None
    hasCrystalStructure: HasCrystalStructure[CrystalStructure]





            

    




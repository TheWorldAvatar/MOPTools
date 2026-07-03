from __future__ import annotations
from typing import List, Optional
from twa.data_model.base_ontology import BaseOntology, BaseClass, ObjectProperty, DatatypeProperty
from twa_mops.utils import om
from twa_mops.core import geo
import os

from rdkit.Chem import GetPeriodicTable
from rdkit.Chem.rdmolfiles import MolFromXYZFile

# NOTE TODO this script is incomplete as it only contains necessary classes and properties for the MOPs project
# NOTE TODO a complete OGM representation for OntoSpecies is yet to be implemented
# NOTE TODO it should also be moved to a place that accessible to all other ontologies
class OntoSpecies(BaseOntology):
    base_url = 'http://www.theworldavatar.com/ontology/ontospecies/OntoSpecies.owl#'


# object properties
HasMolecularWeight = ObjectProperty.create_from_base('HasMolecularWeight', OntoSpecies)
HasCharge = ObjectProperty.create_from_base('HasCharge', OntoSpecies)
HasGeometry = ObjectProperty.create_from_base('HasGeometry', OntoSpecies)

# data properties
HasGeometryFile = DatatypeProperty.create_from_base('HasGeometryFile', OntoSpecies)


# classes
class Charge(BaseClass):
    rdfs_isDefinedBy = OntoSpecies
    hasValue: om.HasValue[om.Measure]

class MolecularWeight(BaseClass):
    rdfs_isDefinedBy = OntoSpecies
    hasValue: om.HasValue[om.Measure]

    @classmethod
    def from_xyz_file(cls, xyz_file: str) -> MolecularWeight:
        periodic_table = GetPeriodicTable()
        mol = MolFromXYZFile(xyz_file)
        atoms = [a.GetSymbol() for a in mol.GetAtoms()]
        molecular_weight = sum(periodic_table.GetAtomicWeight(atom) for atom in atoms)
        return cls(hasValue=om.Measure(hasNumericalValue=molecular_weight, hasUnit=om.gramPerMole))

class Geometry(BaseClass):
    rdfs_isDefinedBy = OntoSpecies
    hasGeometryFile: HasGeometryFile[str]
    hasPoints: Optional[List[geo.Point]] = None

    @property
    def geometry_file(self) -> str:
        return list(self.hasGeometryFile)[0]

    @classmethod
    def from_points(cls, points: List[geo.Point], file_name: str) -> Geometry:
        file_name = file_name + '.xyz' if not file_name.endswith('.xyz') else file_name
        pts = [p for p in points if p.label.lower() not in ['x', 'center']]
        with open(file_name, 'w') as f:
            f.write(f'{len(pts)}\n\n')
            for pt in pts:
                # enforce normal decimal numbers to avoid scientific notation which breaks reading the xyz file using rdkit
                f.write(f'{pt.label} {pt.x:.20f} {pt.y:.20f} {pt.z:.20f}\n')
        return cls(hasGeometryFile=file_name, hasPoints=points)

    def load_xyz_from_geometry_file(self, sparql_client, data_dir=None):
        import logging
        logger = logging.getLogger(__name__)
        
        lst_pt = []
        remote_file_path = list(self.hasGeometryFile)[0]
        downloaded_file_path = remote_file_path.split('/')[-1]
        
        logger.info(f"Loading geometry file: {remote_file_path}")
        
        # Get file server URL from the client for constructing full URLs
        fs_url = getattr(sparql_client, 'fs_url', None)
        if fs_url is None and hasattr(sparql_client, 'sparql_client'):
            fs_url = getattr(sparql_client.sparql_client, 'fs_url', None)
        
        logger.info(f"File server URL: {fs_url}")
        
        # Get data_dir from settings if not provided
        if data_dir is None:
            from twa_mops.config import settings
            data_dir = settings.data_dir
        
        # Ensure data_dir exists
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)
        
        # If the path is local, use it directly
        if not remote_file_path.startswith(('http://', 'https://')):
            # Check if it's already a local path
            if os.path.exists(remote_file_path):
                downloaded_file_path = remote_file_path
            else:
                # Try to find the file in data_dir or tutorials
                search_paths = []
                if data_dir:
                    search_paths.append(data_dir)
                # Also check tutorials directory for CBU files created there
                search_paths.extend(['tutorials', os.path.join('tutorials', 'data')])
                
                found = False
                for search_path in search_paths:
                    test_path = os.path.join(search_path, downloaded_file_path)
                    if os.path.exists(test_path):
                        downloaded_file_path = test_path
                        found = True
                        break
                
                if not found:
                    # Try to download from file server if available
                    if fs_url:
                        # It's a filename that needs to be downloaded from the file server
                        # For Hybrid option: handle paths like "data/cbu/file.xyz" or just "file.xyz"
                        # Extract just the filename if path contains directory components
                        if '/' in remote_file_path:
                            actual_filename = remote_file_path.split('/')[-1]
                            full_remote_path = f"{fs_url.rstrip('/')}/{actual_filename}"
                        else:
                            full_remote_path = f"{fs_url.rstrip('/')}/{remote_file_path}"
                        logger.info(f"Attempting to download from: {full_remote_path}")
                        try:
                            sparql_client.download_file(full_remote_path, downloaded_file_path)
                            logger.info(f"Successfully downloaded to: {downloaded_file_path}")
                        except Exception as e:
                            logger.error(f"Failed to download {full_remote_path}: {e}")
                            raise FileNotFoundError(
                                f"File not found: {downloaded_file_path}. "
                                f"Remote path: {remote_file_path}. "
                                f"File server URL: {fs_url}. "
                                f"Download error: {e}. "
                                f"Searched paths: {search_paths}"
                            )
                    else:
                        # No file server URL available
                        raise FileNotFoundError(
                            f"File not found: {downloaded_file_path}. "
                            f"Remote path: {remote_file_path}. "
                            f"File server URL: Not configured. "
                            f"Searched paths: {search_paths}. "
                            "Either configure a file server, place the file in your data_dir, "
                            "or in the tutorials directory."
                        )
        else:
            # It's already a full URL, download directly
            logger.info(f"Attempting to download full URL: {remote_file_path}")
            try:
                sparql_client.download_file(remote_file_path, downloaded_file_path)
                logger.info(f"Successfully downloaded to: {downloaded_file_path}")
            except Exception as e:
                logger.error(f"Failed to download {remote_file_path}: {e}")
                if not os.path.exists(downloaded_file_path):
                    raise FileNotFoundError(
                        f"File not found: {downloaded_file_path}. "
                        f"Remote path: {remote_file_path}. "
                        f"Download error: {e}"
                    )

        # Ensure the file exists
        if not os.path.exists(downloaded_file_path):
            raise FileNotFoundError(
                f"File not found: {downloaded_file_path}. "
                f"Remote path: {remote_file_path}. "
                f"File server URL: {fs_url or 'Not configured'}. "
                "Check if the file was created and is accessible."
            )

        mol = MolFromXYZFile(downloaded_file_path)
        for a in mol.GetAtoms():
            pos = mol.GetConformer().GetAtomPosition(a.GetIdx())
            pt = geo.Point(x=pos.x, y=pos.y, z=pos.z, label=a.GetSymbol())
            lst_pt.append(pt)
        self.hasPoints = lst_pt
import os
import uuid
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdchem, rdMolTransforms, rdMolDescriptors, Descriptors
from scipy.optimize import minimize


PERIODIC_TABLE = rdchem.GetPeriodicTable()


def is_asymmetric_dummy_atoms(smiles: str, dummy_atomic_number: int = 0) -> bool:
    """
    Given a SMILES string, check if it contains exactly two dummy atoms (atomicNum == 0)
    and whether they are asymmetric based on their connectivity.
    Returns True if asymmetric, False if symmetric or not applicable.
    """
    mol = Chem.MolFromSmiles(smiles)
    dummy_atoms = [
        atom.GetIdx() 
        for atom in mol.GetAtoms() 
        if atom.GetAtomicNum() == dummy_atomic_number
    ]
    if len(dummy_atoms) != 2:
        return False

    d1, d2 = dummy_atoms
    # Create two temporary copies to assign atom maps and generate SMILES
    tmp1 = Chem.Mol(mol)
    for atom in tmp1.GetAtoms():
        atom.SetAtomMapNum(0)
    tmp1.GetAtomWithIdx(d1).SetAtomMapNum(1)
    tmp1.GetAtomWithIdx(d2).SetAtomMapNum(2)
    smiles1 = Chem.MolToSmiles(tmp1, isomericSmiles=True)

    tmp2 = Chem.Mol(mol)
    for atom in tmp2.GetAtoms():
        atom.SetAtomMapNum(0)
    tmp2.GetAtomWithIdx(d1).SetAtomMapNum(2)
    tmp2.GetAtomWithIdx(d2).SetAtomMapNum(1)
    smiles2 = Chem.MolToSmiles(tmp2, isomericSmiles=True)
    
    return not smiles1 == smiles2

def create_swapped_dummy_atoms_mol(
    mol_file_path: str,
    swapped_file_path: str,
    dummy_atomic_number: int = 0,
    # sanitize: bool = False,
) -> dict:
    """
    Load a molecule from a .mol file and compute all of the
    properties needed to build a MolecularFragment.
    Returns a dict with keys:
      - mol
      - charge
      - molecular_weight
      - molecular_formula
      - atom_data
      - smiles
    """

    if not os.path.exists(mol_file_path):
        raise FileNotFoundError(f"The file {mol_file_path} does not exist.")
    
    mol = Chem.MolFromMolFile(mol_file_path, removeHs=False, sanitize=False)
    mol.UpdatePropertyCache(strict=False)
    if mol is None:
        raise ValueError(f"Failed to load molecule from {mol_file_path}.")
    
    dummy_atoms = [atom.GetIdx() for atom in mol.GetAtoms() if atom.GetAtomicNum() == dummy_atomic_number]
    if len(dummy_atoms) != 2:
        raise ValueError("Not exactly two dummy atoms")
    
    # swap dummy atom indices
    d1, d2 = dummy_atoms
    new_order = list(range(mol.GetNumAtoms()))
    new_order[d1], new_order[d2] = new_order[d2], new_order[d1]
    
    mol = Chem.RenumberAtoms(mol, new_order)

    Chem.MolToMolFile(
        mol,
        swapped_file_path,
    )

    conf = mol.GetConformer()

    atoms = []
    for atom in mol.GetAtoms():
        pos = conf.GetAtomPosition(atom.GetIdx())
        atoms.append({
            'label': atom.GetSymbol(),
            'coordinate_x': pos.x,
            'coordinate_y': pos.y,
            'coordinate_z': pos.z,
        })

    smiles = Chem.MolToSmiles(
        Chem.RemoveHs(mol),
        canonical=True
    )

    return {
        'mol': mol,
        'atoms': atoms,
        'smiles': smiles,
    }




def load_molecular_fragment_from_mol_file(
    mol_file_path: str,
    dummy_atomic_number: int = 0,
    check_asymmetry: bool = False,
    # sanitize: bool = False,
) -> dict:
    """
    Load a molecule from a .mol file and compute all of the
    properties needed to build a MolecularFragment.
    Returns a dict with keys:
      - mol
      - charge
      - molecular_weight
      - molecular_formula
      - atom_data
      - smiles
    """

    if not os.path.exists(mol_file_path):
        raise FileNotFoundError(f"The file {mol_file_path} does not exist.")
    
    mol = Chem.MolFromMolFile(mol_file_path, removeHs=False, sanitize=False)
    mol.UpdatePropertyCache(strict=False)
    if mol is None:
        raise ValueError(f"Failed to load molecule from {mol_file_path}.")
    
    charge = Chem.GetFormalCharge(mol)

    molecular_weight = 0
    element_counts = {
        PERIODIC_TABLE.GetElementSymbol(z): 0
        for z in {a.GetAtomicNum() for a in mol.GetAtoms()} 
        if z != dummy_atomic_number
    }
    for atom in mol.GetAtoms():
        Z = atom.GetAtomicNum()
        if Z == dummy_atomic_number:
            continue
        elem_sym = PERIODIC_TABLE.GetElementSymbol(Z)
        element_counts[elem_sym] += 1
        molecular_weight += atom.GetMass()
    
    molecular_formula = ""
    for elem in ('C','H','N','O'):
        if elem in element_counts:
            n = element_counts.pop(elem)
            molecular_formula += f"{elem}{n if n>1 else ''}"
    for elem in sorted(element_counts):
        n = element_counts[elem]
        molecular_formula += f"{elem}{n if n>1 else ''}"


    conf = mol.GetConformer()

    atoms = []
    for atom in mol.GetAtoms():
        pos = conf.GetAtomPosition(atom.GetIdx())
        atoms.append({
            'label': atom.GetSymbol(),
            'coordinate_x': pos.x,
            'coordinate_y': pos.y,
            'coordinate_z': pos.z,
        })
    
    smiles = Chem.MolToSmiles(
        Chem.RemoveHs(mol),
        canonical=True
    )

    return {
        'mol': mol,
        'charge': charge,
        'molecular_weight': molecular_weight,
        'molecular_formula': molecular_formula,
        'atoms': atoms,
        'smiles': smiles,
    }


def _get_local_frame(conf, mol: Chem.Mol, dummy_idx: int, nbr_idx: int):
    """
    Build a right-handed orthonormal frame at the neighbour atom:
      origin = coords[nbr_idx]
      e1 = (coords[dummy_idx] - coords[nbr_idx]) normalized
      pick any other atom bonded to nbr_idx (≠ dummy_idx) as nbr2_idx
      temp = coords[nbr2_idx] - coords[nbr_idx]
      e2 = (temp - (temp·e1)e1) normalized
      e3 = e1 × e2
    Returns (origin, 3×3 matrix [e1,e2,e3]).
    """
    # 1) positions
    pos = lambda i: np.array(conf.GetAtomPosition(i))
    o = pos(nbr_idx)
    # 2) first axis: neighbour → dummy
    v1 = pos(dummy_idx) - o
    e1 = v1 / np.linalg.norm(v1)
    # 3) find a second neighbour of nbr_idx
    nbr2_idx = None
    for b in mol.GetAtomWithIdx(nbr_idx).GetBonds():
        idx = b.GetOtherAtomIdx(nbr_idx)
        if idx != dummy_idx:
            nbr2_idx = idx
            break
    if nbr2_idx is None:
        raise ValueError(f"No second neighbour found for atom {nbr_idx}")
    # 4) second axis: project out component along e1
    v_temp = pos(nbr2_idx) - o
    v2 = v_temp - np.dot(v_temp, e1) * e1
    e2 = v2 / np.linalg.norm(v2)
    # 5) third axis
    e3 = np.cross(e1, e2)
    return o, np.vstack((e1, e2, e3)).T

    

def reset_dummy_atom_atomic_numbers(mol: Chem.Mol, atomic_number: int):
    rw = Chem.RWMol(mol)
    for atom in rw.GetAtoms():
        if atom.GetAtomicNum() == atomic_number:
            atom.SetAtomicNum(0)
            atom.SetFormalCharge(0)
            atom.SetIsotope(0)
    return rw.GetMol()

def _get_single_dummy_and_neighbor(mol: Chem.Mol, dummy_idx: int):
    dummy_atoms = [atom.GetIdx() for atom in mol.GetAtoms() if atom.GetAtomicNum() == 0]
    if not (0 <= dummy_idx < len(dummy_atoms)):
        raise ValueError(f"Invalid dummy_idx {dummy_idx}; found {len(dummy_atoms)} dummy atoms")
    d_idx = dummy_atoms[dummy_idx]
    bond = mol.GetAtomWithIdx(d_idx).GetBonds()[0]
    nbr = bond.GetBeginAtom() if bond.GetBeginAtom().GetIdx() != d_idx else bond.GetEndAtom()
    return d_idx, nbr.GetIdx(), bond.GetBondType()

def _compute_rigid_transform(P_src: np.ndarray, P_dst: np.ndarray):
    """
    Compute the rigid transformation (rotation R and translation t) that aligns
    points P_src to points P_dst using Singular Value Decomposition (SVD).
    Args:
        P_src: Source points (shape: [N, 3])
        P_dst: Destination points (shape: [N, 3])
    Returns:    
        R: Rotation matrix (shape: [3, 3])
        t: Translation vector (shape: [3])
    """
    centroid_src = P_src.mean(axis=0)
    centroid_dst = P_dst.mean(axis=0)
    Q_src, Q_dst = P_src - centroid_src, P_dst - centroid_dst
    H = Q_src.T @ Q_dst
    U, _, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[2, :] *= -1
        R = Vt.T @ U.T
    t = centroid_dst - R @ centroid_src
    return R, t

def reassemble_two_fragments(
        frag1: Chem.Mol, 
        frag2: Chem.Mol, 
        dummy_idxs: tuple =(0, 0), 
        sanitize: bool = False
    ) -> tuple[Chem.Mol, tuple[int,int]]:
    """
    Rigidly align frag2 onto frag1 via their dummy atoms, then delete both dummies
    and re-bond the two heavy neighbors. Returns one combined Chem.Mol.
    """
    # 1) Extract dummy & neighbor from frag1
    d1_idx, h1_idx, bond_type1 = _get_single_dummy_and_neighbor(frag1, dummy_idxs[0])

    # 2) Extract dummy & neighbor from frag2
    d2_idx, h2_idx, bond_type2 = _get_single_dummy_and_neighbor(frag2, dummy_idxs[1])

    # Choose bond type to add
    bond_to_add = bond_type1 if bond_type1 == bond_type2 else bond_type1
    
    pt = rdchem.GetPeriodicTable()
    r1 = pt.GetRcovalent(frag1.GetAtomWithIdx(h1_idx).GetAtomicNum())
    r2 = pt.GetRcovalent(frag2.GetAtomWithIdx(h2_idx).GetAtomicNum())
    target_dist = (r1 + r2) #/ 2.0

    # 3) Build a local frame [e1,e2,e3] at each dummy‐neighbour, and their origins.
    conf1 = frag1.GetConformer()
    conf2 = frag2.GetConformer()
    o1, F1 = _get_local_frame(conf1, frag1, d1_idx, h1_idx)
    o2, F2 = _get_local_frame(conf2, frag2, d2_idx, h2_idx)

    # 4) reverse the first axis on frag2 so e1_2 → -e1_2
    F2[:, 0] *= -1

    rotation_angle = 0
    if abs(rotation_angle) > 1e-8:
        phi = np.deg2rad(rotation_angle)
        e2 = F2[:, 1].copy()
        e3 = F2[:, 2].copy()
        # right‐hand rule around e1: 
        F2[:, 1] =  np.cos(phi) * e2 + np.sin(phi) * e3
        F2[:, 2] = -np.sin(phi) * e2 + np.cos(phi) * e3

    # 5) rotation that takes frame2 into frame1: R = F1 · F2^T
    R = F1 @ F2.T

    pt = rdchem.GetPeriodicTable()
    r1 = pt.GetRcovalent(frag1.GetAtomWithIdx(h1_idx).GetAtomicNum())
    r2 = pt.GetRcovalent(frag2.GetAtomWithIdx(h2_idx).GetAtomicNum())
    target_dist = (r1 + r2) #/ 2.0

    # 6) translation to bring origins to o1
    # t = o1 - R.dot(o2) # overlapping origins
    t = (o1 + F1[:, 0] * target_dist) - R.dot(o2)


    # 5) Apply (R, t) to all atoms in frag2
    new_conf2 = Chem.Conformer(frag2.GetNumAtoms())
    for i in range(frag2.GetNumAtoms()):
        old_pos = np.array(conf2.GetAtomPosition(i))
        new_pos = R.dot(old_pos) + t
        new_conf2.SetAtomPosition(i, Chem.rdGeometry.Point3D(*new_pos))

    frag2_aligned = Chem.Mol(frag2)
    frag2_aligned.RemoveAllConformers()
    frag2_aligned.AddConformer(new_conf2, assignId=True)

    # 6) Combine
    combined = Chem.CombineMols(frag1, frag2_aligned)
    em = Chem.EditableMol(combined)

    N1 = frag1.GetNumAtoms()
    H1_cidx = h1_idx
    H2_cidx = h2_idx + N1
    D1_cidx = d1_idx
    D2_cidx = d2_idx + N1

    # 7) Add bond between H1_cidx and H2_cidx
    em.AddBond(H1_cidx, H2_cidx, order=bond_to_add)
    new_bond = (H1_cidx, H2_cidx)

    # 8) Remove dummy atoms in descending order
    del_indices = sorted([D1_cidx, D2_cidx], reverse=True)
    for delete_idx in del_indices:
        em.RemoveAtom(delete_idx)

    # for delete_idx in sorted([D1_cidx, D2_cidx], reverse=True):
    #     em.RemoveAtom(delete_idx)
    final_bond = list(new_bond)
    for delete_idx in del_indices:
        for i, idx in enumerate(final_bond):
            if idx > delete_idx:
                final_bond[i] -= 1
    new_bond = tuple(final_bond)

    # 9) Sanitize and return
    new_mol = em.GetMol()
    if sanitize:
        Chem.SanitizeMol(new_mol)
    return new_mol, new_bond

def _load_fragment_molecule_from_mol_block(
        mol_block: str, 
        dummy_atomic_number: int = None,
        sanitize: bool = False
    ) -> Chem.Mol:
    mol = Chem.MolFromMolBlock(mol_block, sanitize=sanitize)
    if mol is None:
        raise ValueError("Failed to load molecule from MolBlock.")
    if dummy_atomic_number is not None:
        mol = reset_dummy_atom_atomic_numbers(mol, dummy_atomic_number)
    return mol

def _load_fragment_molecule_from_mol_file(
        mol_file_path: str,
        dummy_atomic_number: int = None,
        sanitize: bool = False
    ) -> Chem.Mol:
    if not os.path.exists(mol_file_path):
        raise FileNotFoundError(f"The file {mol_file_path} does not exist.")
    mol = Chem.MolFromMolFile(mol_file_path, removeHs=False, sanitize=sanitize)
    if mol is None:
        raise ValueError(f"Failed to load molecule from {mol_file_path}.")
    if dummy_atomic_number is not None:
        mol = reset_dummy_atom_atomic_numbers(mol, dummy_atomic_number)
    return mol


def make_binding_groups_coplanar(mol: Chem.Mol, conf: Chem.Conformer):
    """Adjust torsions between binding fragments so that binding atoms lie close to a common plane.

    * ≥3 sites  → minimise binding‑atom distances to mid‑point plane.
    *   2 sites → make coplanar with first binding fragment.
    """
        
    # -----------------------------------------------------------------------------
    # Helper geometry routines
    # -----------------------------------------------------------------------------

    def reset_conf(conf, orig):
        """Restore *conf* coordinates from *orig* list of (x,y,z)."""
        for i, pos in enumerate(orig):
            conf.SetAtomPosition(i, pos)


    def fit_plane(points: np.ndarray):
        """Return (centroid, unit normal) of least‑squares plane through *points*."""
        centroid = points.mean(axis=0)
        _, _, vh = np.linalg.svd(points - centroid)
        normal = vh[-1]
        return centroid, normal / np.linalg.norm(normal)


    def get_CCO_dihedrals(conf, torsion_defs):
        return [AllChem.GetDihedralDeg(conf, *t) for t in torsion_defs]

    # -----------------------------------------------------------------------------
    # Optimisation objectives
    # -----------------------------------------------------------------------------

    def objective_pairwise(angles, conf, orig_pos, cco_defs, inter_defs):
        """objective for exactly two sites (pairwise torsion matching). make coplanar"""
        reset_conf(conf, orig_pos)
        for theta, (a,b,c,d) in zip(angles, cco_defs):
            rdMolTransforms.SetDihedralDeg(conf, a, b, c, d, float(theta))
        inter_binding_site_dihedrals = [AllChem.GetDihedralDeg(conf, *d) for d in inter_defs]
        return float(np.sum(np.abs(inter_binding_site_dihedrals)))


    def objective_plane_atoms(angles, conf, orig_pos, cco_defs, mid_pairs, bind_atoms):
        """Minimise the sum of squared distances of *binding atoms* to the plane
        defined by the mid‑points of the binding sites.
        """
        reset_conf(conf, orig_pos)
        # 1) Apply the trial torsions
        for theta, (a,b,c,d) in zip(angles, cco_defs):
            rdMolTransforms.SetDihedralDeg(conf, a, b, c, d, float(theta))

        # 2) Compute the mid‑points and fit their best‑fit plane
        mid_pts = []
        for o1, o2 in mid_pairs:
            p1, p2 = conf.GetAtomPosition(o1), conf.GetAtomPosition(o2)
            mid_pts.append([(p1.x+p2.x)*0.5, (p1.y+p2.y)*0.5, (p1.z+p2.z)*0.5])
        centroid, normal = fit_plane(np.asarray(mid_pts))

        # 3) Distances of *all binding atoms* to that plane
        acc = 0.0
        for idx in bind_atoms:
            p = conf.GetAtomPosition(idx)
            d = np.dot(np.array([p.x, p.y, p.z]) - centroid, normal)
            acc += d*d
        return float(acc)
    
    # -----------------------------------------------------------------------------
    # Save original coordinates
    # -----------------------------------------------------------------------------

    orig_pos = [tuple(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]

    # ---------------------------------------------------------------------
    # 1) Locate binding sites by smiles matching # TODO: should pass binding fragments
    # ---------------------------------------------------------------------
    patt_coo = Chem.MolFromSmarts('*[C;X3](=O)[O-]')  
    matches = list(mol.GetSubstructMatches(patt_coo))

    patt2 = Chem.MolFromSmarts('*c1cn[n-]c1')
    matches += mol.GetSubstructMatches(patt2)
    print(matches)
    if len(matches) < 3:
        raise RuntimeError("Need ≥2 carboxylates to define inter-COO torsions")
    n_sites = len(matches)
    if n_sites < 2:
        raise RuntimeError(f"Need ≥2 binding sites, found {n_sites}")

    # ---------------------------------------------------------------------
    # 2) Build inter binding fragment torsion definitions
    # ---------------------------------------------------------------------
    variable_torsions = []
    for m in matches:
        r = m[0]
        neigh = [nbr.GetIdx() for nbr in mol.GetAtomWithIdx(r).GetNeighbors()
                 if nbr.GetIdx() not in m]
        variable_torsions.append((neigh[0], r, m[1], m[2]))

    starting_binding_frag_dihedrals = [AllChem.GetDihedralDeg(conf, *t) for t in variable_torsions] #get_CCO_dihedrals(conf, variable_torsions)
    print("Initial binding fragments inter dihedrals:", np.round(starting_binding_frag_dihedrals, 2))

    # ---------------------------------------------------------------------
    # 3) Optimisation branch: two sites vs ≥3 sites
    # ---------------------------------------------------------------------
    if n_sites == 2:
        # ========== Two‑site fallback ===========
        (c0, o0_db, o0_sg) = matches[0][1:4]
        (c1, o1_db, o1_sg) = matches[1][1:4]
        inter_defs = [(o0_sg, c0, c1, o1_sg)]
        res = minimize(
            objective_pairwise,
            x0=np.array(starting_binding_frag_dihedrals),
            args=(conf, orig_pos, variable_torsions, inter_defs),
            method="Powell",
            options={"maxiter": 500, "disp": True},
        )
    else:
        # ========== Plane‑based objective for ≥3 sites ===========
        mid_pairs = [(m[2], m[3]) for m in matches]  # (O_db, O_sg)
        bind_atoms = [idx for m in matches for idx in (m[1], m[2], m[3])]
        res = minimize(
            objective_plane_atoms,
            x0=np.array(starting_binding_frag_dihedrals),
            args=(conf, orig_pos, variable_torsions, mid_pairs, bind_atoms),
            method="Powell",
            options={"maxiter": 800, "disp": True},
        )

    # ---------------------------------------------------------------------
    # 4) Apply optimised torsions
    # ---------------------------------------------------------------------
    reset_conf(conf, orig_pos)
    for theta, (a,b,c,d) in zip(res.x, variable_torsions):
        rdMolTransforms.SetDihedralDeg(conf, a, b, c, d, float(theta))


def determine_binding_atoms_from_mol(mol: Chem.Mol) -> list[str]:
    """
    Determine the binding atoms in a molecule based on the presence of carboxylate
    (–COO⁻) or pyrazole (c1cn[n-]c1) groups. Returns a list of atom symbols that
    are part of the binding groups.
    """
    binding_atoms = []
    
    # Check for carboxylate groups
    patt_coo = Chem.MolFromSmarts('[C;X3](=O)[O-]')
    matches_coo = mol.GetSubstructMatches(patt_coo)

    if matches_coo:
        return "CO2"  # If any carboxylate group is found, return CO2 as binding fragment

    # Check for pyrazole groups
    patt_py = Chem.MolFromSmarts('c1cn[n-]c1')
    matches_py = mol.GetSubstructMatches(patt_py)

    if matches_py:
        return "N2"
    
    return None

def determine_binding_atoms_from_json(cbu_json):
    """
    Given a geometry dict (as returned by mol_to_json_dict), find all
    dummy atoms ("X"), compute their two nearest non-dummy neighbors,
    and from their element types infer the binding fragment:
      - if any neighbor is O → "CO2"
      - if any neighbor is N → "N2"
    """
    binding_coords = []
    nonbinding = []
    # 1) split out dummy vs real atoms
    for uid, v in cbu_json.items():
        x, y, z = v['coordinate_x'], v['coordinate_y'], v['coordinate_z']
        atom = v['atom']
        if atom == 'X':
            binding_coords.append((x, y, z))
        else:
            nonbinding.append((x, y, z, atom))

    neighbor_atom_types = set()

    # 2) for each binding site, find the two closest real atoms
    for bx, by, bz in binding_coords:
        # compute squared distances to every non-dummy atom
        dists = []
        for x, y, z, atom in nonbinding:
            dx, dy, dz = x - bx, y - by, z - bz
            d2 = dx*dx + dy*dy + dz*dz
            dists.append((d2, atom))
        # sort by distance
        dists.sort(key=lambda t: t[0])
        # take the two nearest
        for _, atom in dists[:2]:
            neighbor_atom_types.add(atom)

    # 3) infer binding fragment
    binding_fragment = None
    if 'O' in neighbor_atom_types:
        binding_fragment = 'CO2'
    if 'N' in neighbor_atom_types:
        binding_fragment = 'N2'

    return binding_fragment


def determine_cbu_formula(cbu_json):
    from collections import defaultdict
    atom_counts = defaultdict(int)

    for k, v in cbu_json.items():
        if v['atom'] == 'X':
            continue
        atom_counts[v['atom']] += 1

    formula = ""
    for elem in ['C', 'H', 'N', 'O']:
        if elem in atom_counts and atom_counts[elem] > 0:
            formula += f"{elem}{atom_counts.pop(elem)}"

    for elem in sorted(atom_counts):
        formula += f"{elem}{atom_counts.pop(elem)}"

    return formula

def mol_formula(mol):
    """
    Calculate the molecular formula of a given RDKit Mol object.
    Returns a string representation of the formula.
    """
    if mol is None:
        return ""

    atom_counts = {
        x: 0 
        for x in {
            a.GetSymbol().strip("0123456789") 
            for a in mol.GetAtoms() if a.GetAtomicNum() > 0
        }
    }
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 0:
            continue
        atom_counts[atom.GetSymbol().strip("0123456789")] += 1
    
    formula = ""
    for elem in ['C', 'H', 'N', 'O']:
        if elem in atom_counts and atom_counts[elem] > 1:
            formula += f"{elem}{atom_counts.pop(elem)}"
        elif elem in atom_counts and atom_counts[elem] == 1:
            formula += f"{elem}"
            atom_counts.pop(elem)
        

    for elem in sorted(atom_counts):
        if atom_counts[elem] > 1:
            formula += f"{elem}{atom_counts.pop(elem)}"
        else:
            formula += f"{elem}"
            atom_counts.pop(elem)

    return formula
    

def insert_carboxylate_binding_dummy_atoms(mol, conf, data):
    #patt = Chem.MolFromSmarts('C(=O)[O-]')
    patt = Chem.MolFromSmarts('C(=O)[O]')
    matches = mol.GetSubstructMatches(patt)
    #if len(matches) != 2:
    #    return None

    for c_idx, o1_idx, o2_idx in matches:
        p1 = conf.GetAtomPosition(o1_idx)
        p2 = conf.GetAtomPosition(o2_idx)
        mx, my, mz = (p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0, (p1.z + p2.z) / 2.0

        # vector from carboxylate C to O midpoint
        c_pos = conf.GetAtomPosition(c_idx)
        vx = mx - c_pos.x
        vy = my - c_pos.y
        vz = mz - c_pos.z

        dummy_x = mx + 1.0 * vx
        dummy_y = my + 1.0 * vy
        dummy_z = mz + 1.0 * vz

        dummy_uid = str(uuid.uuid4())
        data[dummy_uid] = {
            "atom":         "X",
            "coordinate_x": dummy_x,
            "coordinate_y": dummy_y,
            "coordinate_z": dummy_z,
            "bond":         [],    # no explicit bonds
            "mmtype":       "",
            "qmmm":         "",
        }

def insert_pyrazole_binding_dummy_atoms(mol, conf, data):
    patt2 = Chem.MolFromSmarts('c1cn[n-]c1')
    matches = mol.GetSubstructMatches(patt2)
    #if len(matches)>0:
    #    return None

    for c1_idx, c2_idx, n1_idx, n2_idx, c3_idx in matches:
        p1 = conf.GetAtomPosition(n1_idx)
        p2 = conf.GetAtomPosition(n2_idx)
        mx, my, mz = (p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0, (p1.z + p2.z) / 2.0

        # vector from carboxylate C to O midpoint
        c_pos = conf.GetAtomPosition(c1_idx)
        vx = mx - c_pos.x
        vy = my - c_pos.y
        vz = mz - c_pos.z

        dummy_x = mx + 0.25 * vx
        dummy_y = my + 0.25 * vy
        dummy_z = mz + 0.25 * vz

        dummy_uid = str(uuid.uuid4())
        data[dummy_uid] = {
            "atom":         "X",
            "coordinate_x": dummy_x,
            "coordinate_y": dummy_y,
            "coordinate_z": dummy_z,
            "bond":         [],    # no explicit bonds
            "mmtype":       "",
            "qmmm":         "",
        }

def cbu_mol_to_json_dict(mol: Chem.Mol, conf: Chem.Conformer) -> dict:
    """
    Embed & optimize `mol`, deprotonate –COOH → –COO⁻, enforce coplanar binding
    groups, then collect per-atom & per-bond data into a JSON-serializable dict.
    """

    # 4) build JSON dict
    cbu_json = {}
    idx2uid = {atom.GetIdx(): str(uuid.uuid4()) for atom in mol.GetAtoms()}

    # atoms
    for atom in mol.GetAtoms():
        uid = idx2uid[atom.GetIdx()]
        pos = conf.GetAtomPosition(atom.GetIdx())
        cbu_json[uid] = {
            "atom":         atom.GetSymbol(),
            "coordinate_x": pos.x,
            "coordinate_y": pos.y,
            "coordinate_z": pos.z,
            "bond":         [],
            "mmtype":       atom.GetProp('_uffAtomType') if atom.HasProp('_uffAtomType') else "",
            "qmmm":         "MM"
        }

    # bonds
    for bond in mol.GetBonds():
        a, b = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        order = 1.5 if bond.GetIsAromatic() else bond.GetBondTypeAsDouble()
        cbu_json[idx2uid[a]]["bond"].append({"to_atom": idx2uid[b], "bond_order": order})
        cbu_json[idx2uid[b]]["bond"].append({"to_atom": idx2uid[a], "bond_order": order})

    # 5) insert any additional dummies here if needed…
    insert_carboxylate_binding_dummy_atoms(mol, conf, cbu_json)
    insert_pyrazole_binding_dummy_atoms(mol, conf, cbu_json)

    return cbu_json

from scipy.optimize import minimize

def _optimize_only_fragment_torsions(
    mol: Chem.Mol,
    bonds: list[tuple[int,int]],
    maxiter: int = 200
):
    """ Vary each dihedral around the given bonds to minimise the UFF energy. """
    conf = mol.GetConformer()
    # 1) Build list of (i,j,k,l) dihedral‐tuples
    dihedrals = []
    for a, b in bonds:
        # pick one neighbor on each side
        nbrs_a = [n.GetIdx() for n in mol.GetAtomWithIdx(a).GetNeighbors() if n.GetIdx()!=b]
        nbrs_b = [n.GetIdx() for n in mol.GetAtomWithIdx(b).GetNeighbors() if n.GetIdx()!=a]
        if not nbrs_a or not nbrs_b:
            continue
        dihedrals.append((nbrs_a[0], a, b, nbrs_b[0]))

    if not dihedrals:
        return

    # 2) Save original positions
    orig = [tuple(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]

    # 3) Define the objective: set all the dihedrals, then compute UFF energy
    def obj(angles):
        # reset coords
        for idx, pos in enumerate(orig):
            conf.SetAtomPosition(idx, Chem.rdGeometry.Point3D(*pos))
        # apply each trial angle
        for θ, (i,j,k,l) in zip(angles, dihedrals):
            rdMolTransforms.SetDihedralDeg(conf, i, j, k, l, float(θ))
        ff = AllChem.UFFGetMoleculeForceField(mol, confId=conf.GetId())
        return ff.CalcEnergy()

    # 4) initial guess
    init = [rdMolTransforms.GetDihedralDeg(conf, *d) for d in dihedrals]

    # 5) run SciPy‐Powell
    res = minimize(obj, x0=np.array(init), method="Powell",
                   options={"maxiter": maxiter, "disp": False})
    # 6) apply final
    for θ, d in zip(res.x, dihedrals):
        rdMolTransforms.SetDihedralDeg(conf, *d, float(θ))



def assemble_fragments_to_cbu(
        linker_mol_files: list[str],
        binding_group_mol_files: str,
        node_mol_files: str = None,
        dummy_atomic_number: int = 68,
        **kwargs
) -> tuple[dict, str]:
    """
    Assemble a CBU (Chemical Building Unit) from given linker and binding group molecules.
    Args:   
        linker_mol_blocks (list[str]): List of Mol blocks for linker molecules.
        binding_group_mol_block (str): Mol block for the binding group molecule.
        node_mol_block (str, optional): Mol block for the node molecule. Defaults to None.
        dummy_atomic_number (int, optional): Atomic number for dummy atoms. Defaults to 68.
        **kwargs: Additional keyword arguments for sanitization and optimization.
    Returns:
        tuple[dict, str]: A tuple containing the CBU JSON dictionary and the Mol block of the assembled CBU.
    """
    linker_mols = [
        _load_fragment_molecule_from_mol_file(
            mol_file, 
            dummy_atomic_number=dummy_atomic_number, 
            sanitize=kwargs.get("sanitize", False)
        )
        for mol_file in linker_mol_files
    ]

    binding_group_mol = _load_fragment_molecule_from_mol_file(
        binding_group_mol_files, 
        dummy_atomic_number=dummy_atomic_number,
        sanitize=kwargs.get("sanitize", False)
    )

    node_mol = None
    if node_mol_files is not None:
        node_mol = _load_fragment_molecule_from_mol_file(
            node_mol_files, 
            dummy_atomic_number=dummy_atomic_number,
            sanitize=kwargs.get("sanitize", False)
        )

    # if node_mol is None:
    #     fragments = [ binding_group_mol ] + linker_mols + [ binding_group_mol ]

    # cbu_mol = binding_group_mol
    cbu_mol = Chem.Mol(binding_group_mol)
    new_bonds = []

    for i, linker_mol in enumerate(linker_mols):
        cbu_mol, new_bond = reassemble_two_fragments(
            cbu_mol, linker_mol, 
            sanitize=kwargs.get("sanitize", False)
        )
        new_bonds.append(new_bond)

    if node_mol is None:
        # cbu_formula = "CH"
        cbu_formula = (
            "".join([f"({mol_formula(m)})" for m in linker_mols]) + 
            f"({mol_formula(binding_group_mol)})2"
        )
        cbu_mol, new_bond = reassemble_two_fragments(
            cbu_mol, binding_group_mol, 
            sanitize=kwargs.get("sanitize", False)
        )
        new_bonds.append(new_bond)
    else:
        num_node_dummy_atoms = sum([1 for _c in node_mol.GetAtoms() if _c.GetAtomicNum() == 0])
        # cbu_formula = "CH"
        cbu_formula = (
            f"({mol_formula(node_mol)})" + "(" +
            "".join([f"({mol_formula(m)})" for m in linker_mols + [binding_group_mol] ]) + ")" + 
            f"{str(num_node_dummy_atoms)}"
        )
        arm_mol = cbu_mol
        _cbu_mol = node_mol
        arm_new_bonds = [ b for b in new_bonds ]
        new_bonds = []
        node_offset = node_mol.GetNumAtoms() - num_node_dummy_atoms
        arm_offset = arm_mol.GetNumAtoms() - 1
        for i in range(num_node_dummy_atoms):
            _cbu_mol, new_bond = reassemble_two_fragments(
                _cbu_mol, arm_mol,
                sanitize=kwargs.get("sanitize", False)
            )
            # TODO : this is a quick fix to correct the atom indices, probably better way to do this
            new_bond = (new_bond[0], new_bond[1] + i + 1 - num_node_dummy_atoms ) # the idx of the frag depends on how many dummy atoms have been removed, fortuantely will always be the second index
            new_bonds.append(new_bond)
            new_bonds += [ (x[0] + node_offset + i*arm_offset, x[1] + node_offset + i*arm_offset) for x in arm_new_bonds ]
        cbu_mol = _cbu_mol
        

    if kwargs.get("optimize", False):
        assert kwargs.get("sanitize", False), "Must --sanitize to --optimize"
        AllChem.UFFOptimizeMolecule(cbu_mol)
    else:
        cbu_mol.UpdatePropertyCache(strict=False)
        Chem.GetSymmSSSR(cbu_mol) 

    _optimize_only_fragment_torsions(cbu_mol, new_bonds)

    cbu_conf = cbu_mol.GetConformer()

    # align binding groups to be coplanar
    make_binding_groups_coplanar(cbu_mol, cbu_conf)

    # Convert to JSON  
    cbu_json = cbu_mol_to_json_dict(cbu_mol, cbu_conf)
    
    cbu_mol_block = Chem.MolToMolBlock(cbu_mol, confId=0)
    cbu_smiles = Chem.MolToSmiles(cbu_mol, canonical=True)

    # binding_atoms = determine_binding_atoms_from_json(cbu_json)

    return cbu_json, cbu_smiles, cbu_formula, cbu_mol_block
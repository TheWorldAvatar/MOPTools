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


# def load_molecular_fragment_from_mol_file(
#     mol_file_path: str,
#     dummy_atomic_number: int = 0,
#     check_asymmetry: bool = False,
#     # sanitize: bool = False,
# ) -> dict:
#     """
#     Load a molecule from a .mol file and compute all of the
#     properties needed to build a MolecularFragment.
#     Returns a dict with keys:
#       - mol
#       - charge
#       - molecular_weight
#       - molecular_formula
#       - atom_data
#       - smiles
#     """

#     if not os.path.exists(mol_file_path):
#         raise FileNotFoundError(f"The file {mol_file_path} does not exist.")
    
#     mol = Chem.MolFromMolFile(mol_file_path, removeHs=False, sanitize=False)
#     mol.UpdatePropertyCache(strict=False)
#     if mol is None:
#         raise ValueError(f"Failed to load molecule from {mol_file_path}.")
    
#     charge = Chem.GetFormalCharge(mol)

#     molecular_weight = 0
#     element_counts = {
#         PERIODIC_TABLE.GetElementSymbol(z): 0
#         for z in {a.GetAtomicNum() for a in mol.GetAtoms()} 
#         if z != dummy_atomic_number
#     }
#     for atom in mol.GetAtoms():
#         Z = atom.GetAtomicNum()
#         if Z == dummy_atomic_number:
#             continue
#         elem_sym = PERIODIC_TABLE.GetElementSymbol(Z)
#         element_counts[elem_sym] += 1
#         molecular_weight += atom.GetMass()
    
#     molecular_formula = ""
#     for elem in ('C','H','N','O'):
#         if elem in element_counts:
#             n = element_counts.pop(elem)
#             molecular_formula += f"{elem}{n if n>1 else ''}"
#     for elem in sorted(element_counts):
#         n = element_counts[elem]
#         molecular_formula += f"{elem}{n if n>1 else ''}"

#     if check_asymmetry:
#         mols = create_asymmetric_dummy_atoms(mol, dummy_atomic_number)
#     else:
#         mols = [mol]

#     mol_data = []
#     for mol in mols:
#         conf = mol.GetConformer()

#         atoms = []
#         for atom in mol.GetAtoms():
#             pos = conf.GetAtomPosition(atom.GetIdx())
#             atoms.append({
#                 'label': atom.GetSymbol(),
#                 'coordinate_x': pos.x,
#                 'coordinate_y': pos.y,
#                 'coordinate_z': pos.z,
#             })
        
#         smiles = Chem.MolToSmiles(
#             Chem.RemoveHs(mol),
#             canonical=True
#         )

    
#         mol_data.append({
#             'mol': mol,
#             'charge': charge,
#             'molecular_weight': molecular_weight,
#             'molecular_formula': molecular_formula,
#             'atoms': atoms,
#             'smiles': smiles,
#         })

#     return mol_data

    

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

    # 3) Get 3D coords
    conf1 = frag1.GetConformer()
    conf2 = frag2.GetConformer()

    D2_pos = np.array(conf2.GetAtomPosition(d2_idx))
    H2_pos = np.array(conf2.GetAtomPosition(h2_idx))
    H1_pos = np.array(conf1.GetAtomPosition(h1_idx))
    D1_pos = np.array(conf1.GetAtomPosition(d1_idx))

    # P_src = np.vstack([D2_pos, H2_pos])
    # P_dst = np.vstack([H1_pos, D1_pos])

    pt = rdchem.GetPeriodicTable()
    r1 = pt.GetRcovalent(frag1.GetAtomWithIdx(h1_idx).GetAtomicNum())
    r2 = pt.GetRcovalent(frag2.GetAtomWithIdx(h2_idx).GetAtomicNum())
    target_dist = (r1 + r2) #/ 2.0

    #    determine the unit vector from H1 -> D1
    v = D1_pos - H1_pos
    norm_v = np.linalg.norm(v)
    if norm_v < 1e-6:
        raise ValueError("Dummy and neighbor in frag1 are coincident; cannot set bond length.")
    v_unit = v / norm_v

    #    place the target position for frag2's neighbor (H2) at H1_pos + target_dist * v_unit
    D1_target = H1_pos + v_unit * target_dist

    v = D2_pos - H2_pos
    norm_v = np.linalg.norm(v)
    if norm_v < 1e-6:
        raise ValueError("Dummy and neighbor in frag1 are coincident; cannot set bond length.")
    v_unit = v / norm_v

    #    place the target position for frag2's neighbor (H2) at H1_pos + target_dist * v_unit
    D2_target = H2_pos + v_unit * target_dist

    P_src = np.vstack([D2_target, H2_pos])
    P_dst = np.vstack([H1_pos, D1_target])

    # 4) Compute transform
    R, t = _compute_rigid_transform(P_src, P_dst)

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
    """
    Rotate all carboxylate (–COO⁻) groups (and pyrazole matches) so that
    their out-of-plane torsions are driven to zero, i.e. they become coplanar.
    Modifies `conf` in place.

    TODO: if greater than 2 binding groups, rotate to binding plane
    """

    if conf is None:
        raise ValueError("No conformer found in the molecule")

    def reset_coords(pts):
        for idx, p in enumerate(orig_pos):
            conf.SetAtomPosition(idx, p)

    def measure_inter_torsions(conf, defs):
        return [AllChem.GetDihedralDeg(conf, *t) for t in defs]

    def objective(angles, conf, defs_var, defs_inter):
        reset_coords(orig_pos)
        # set each –C–C=O dihedral
        for θ, (r1, r2, c, o) in zip(angles, defs_var):
            rdMolTransforms.SetDihedralDeg(conf, r1, r2, c, o, float(θ))
        # sum absolute inter-group torsions
        return np.sum(np.abs(measure_inter_torsions(conf, defs_inter)))

    # save original
    orig_pos = [tuple(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]

    # collect all –C(=O)[O-] (or –C(=O)[O]) matches
    patt_coo = Chem.MolFromSmarts('*[C;X3](=O)[O-]') # Chem.MolFromSmarts('*[C;X3](=O)[O]') # Chem.MolFromSmarts('*[C;X3](=O)[O-]')
    patt_py  = Chem.MolFromSmarts('*c1cn[n-]c1') # 
    matches = mol.GetSubstructMatches(patt_coo) + mol.GetSubstructMatches(patt_py)
    if len(matches) < 2:
        return  # nothing to do

    # define the variable dihedrals: for each match except the first
    var_defs = []
    for match in matches[1:]:
        carbon = match[0]
        nbrs = [n.GetIdx() for n in mol.GetAtomWithIdx(carbon).GetNeighbors()
                if n.GetIdx() not in match]
        # (R–C–O–O) => pick nbrs[0], carbon, match[1], match[2]
        var_defs.append((nbrs[0], carbon, match[1], match[2]))

    # define inter-group torsions relative to the first match
    inter_defs = []
    ref = matches[0]
    for m in matches[1:]:
        inter_defs.append((ref[2], ref[1], m[1], m[2]))

    # initial angles
    init = [AllChem.GetDihedralDeg(conf, *t) for t in var_defs]

    # optimize
    res = minimize(
        objective, x0=np.array(init),
        args=(conf, var_defs, inter_defs),
        method="Powell",
        options={"maxiter": 500, "disp": False}
    )
    optimized = res.x

    # apply optimized angles
    reset_coords(orig_pos)
    for θ, tup in zip(optimized, var_defs):
        rdMolTransforms.SetDihedralDeg(conf, *tup, float(θ))

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
        node_dummy_atoms = sum([1 for _c in node_mol.GetAtoms() if _c.GetAtomicNum() == 0])
        # cbu_formula = "CH"
        cbu_formula = (
            f"({mol_formula(node_mol)})" + "(" +
            "".join([f"({mol_formula(m)})" for m in linker_mols + [binding_group_mol] ]) + ")" + 
            f"{str(node_dummy_atoms)}"
        )
        arm_mol = cbu_mol
        _cbu_mol = node_mol
        for _ in range(node_dummy_atoms):
            _cbu_mol, new_bond = reassemble_two_fragments(
                _cbu_mol, arm_mol,
                sanitize=kwargs.get("sanitize", False)
            )
            new_bonds.append(new_bond)
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
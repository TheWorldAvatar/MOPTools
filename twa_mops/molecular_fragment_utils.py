import os
import uuid
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdchem, rdMolTransforms, rdMolDescriptors, Descriptors
from scipy.optimize import minimize

PERIODIC_TABLE = rdchem.GetPeriodicTable()

def has_nonbonded_overlaps(
    mol: Chem.Mol,
    threshold_factor: float = 1.2
) -> bool:
    """check for overlap between non-bonded atoms in a molecule"""
    from rdkit.Chem import rdmolops

    conf = mol.GetConformer()
    n = mol.GetNumAtoms()

    # covalent radii for each atom
    radii = np.array([ # use van der Waals?
        PERIODIC_TABLE.GetRcovalent(atom.GetAtomicNum())
        # PERIODIC_TABLE.GetRvdw(atom.GetAtomicNum())
        for atom in mol.GetAtoms()
    ])

    # adjacency matrix with masked out bonded pairs
    adj = Chem.GetAdjacencyMatrix(mol, useBO=False)
    mask = (adj == 0)
    np.fill_diagonal(mask, False)

    # distance matrix
    D = rdmolops.Get3DDistanceMatrix(mol, confId=conf.GetId())

    # threshold matrix
    T = threshold_factor * (radii[:, None] + radii[None, :])

    return bool(np.any((D < T) & mask))



def is_asymmetric_dummy_atoms(
    smiles: str,
    dummy_atomic_number: int = 0
) -> bool:
    """
    Given a SMILES string, check if it contains exactly two dummy atoms
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

def load_molecular_fragment_from_mol_file( #TODO change to mol file content/str so works with local and remote
    mol_file_path: str,
    dummy_atomic_number: int = 0,
    sanitize=True,
) -> dict:
    """
    Load a molecule from a .mol file and compute properties.
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
    
    mol = Chem.MolFromMolFile(mol_file_path, removeHs=False, sanitize=sanitize)
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
    Build a right-handed orthonormal frame consisting of the dummy atom
    and the two nearest neighbours

    Returns:
        o : (3,) float array
            origin at neighbour atom
        frame : (3,3) float array
            columns are e1, e2, e3 unit vectors
    """
    
    pos = lambda i: np.array(conf.GetAtomPosition(i))
    o = pos(nbr_idx)
    
    # first axis: neighbour → dummy
    v1 = pos(dummy_idx) - o
    e1 = v1 / np.linalg.norm(v1)
    
    # find a second neighbour of nbr_idx
    nbr2_idx = None
    for b in mol.GetAtomWithIdx(nbr_idx).GetBonds(): # TODO check canonical ranking of neighbours
        idx = b.GetOtherAtomIdx(nbr_idx)
        if idx != dummy_idx:
            nbr2_idx = idx
            break
    if nbr2_idx is None:
        raise ValueError(f"No second neighbour found for atom {nbr_idx}")
    
    # second axis: project out component along e1
    v_temp = pos(nbr2_idx) - o
    v2 = v_temp - np.dot(v_temp, e1) * e1
    norm_v2 = np.linalg.norm(v2)


    # check for colinearity
    if norm_v2 < 1e-6:
        # colinear, pick a vector not parallel to e1
        arb = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(arb, e1)) > 0.9:
            arb = np.array([0.0, 1.0, 0.0])
        # form a perpendicular axis
        e2 = np.cross(e1, arb)
        e2 /= np.linalg.norm(e2)
    else:
        # not colinear
        e2 = v2 / norm_v2

    # third axis, cross product of first two
    e3 = np.cross(e1, e2)

    frame = np.vstack((e1, e2, e3)).T
    return o, frame

def reset_dummy_atom_atomic_numbers(mol: Chem.Mol, atomic_number: int):
    """
    Reset all dummy atoms with the specified atomic number to atomic number 0.
    """
    rw = Chem.RWMol(mol)
    for atom in rw.GetAtoms():
        if atom.GetAtomicNum() == atomic_number:
            atom.SetAtomicNum(0)
            atom.SetFormalCharge(0)
            atom.SetIsotope(0)
    return rw.GetMol()

def _get_single_dummy_and_neighbor(mol: Chem.Mol, dummy_idx: int):
    """
    Extract the specified dummy atom and its heavy neighbor from the molecule.

    Returns:
        d_idx : int
            index of the dummy atom
        h_idx : int
            index of the heavy neighbor atom
        bond_type : Chem.rdchem.BondType
            bond type between dummy and neighbor
    """
    dummy_atoms = [atom.GetIdx() for atom in mol.GetAtoms() if atom.GetAtomicNum() == 0]
    if not (0 <= dummy_idx < len(dummy_atoms)):
        raise ValueError(f"Invalid dummy_idx {dummy_idx}; found {len(dummy_atoms)} dummy atoms")
    d_idx = dummy_atoms[dummy_idx]
    bond = mol.GetAtomWithIdx(d_idx).GetBonds()[0]
    nbr = bond.GetBeginAtom() if bond.GetBeginAtom().GetIdx() != d_idx else bond.GetEndAtom()
    return d_idx, nbr.GetIdx(), bond.GetBondType()


def reassemble_two_fragments(
    frag1: Chem.Mol, 
    frag2: Chem.Mol, 
    dummy_idxs: tuple =(0, 0),
    rotation_angle_increment: float = 10.0,
    sanitize: bool = False,
    optimize: bool = False,
) -> tuple[Chem.Mol, tuple[int,int]]:
    """
    Rigidly align frag2 onto frag1 via their dummy atoms, then delete both dummies
    and re-bond the two heavy neighbors. Returns one combined Chem.Mol.

    TODO: only calculate transformation once, then try multiple rotations about the bond axis

    Args:
        frag1: Chem.Mol
            First fragment RDKit molecule with dummy atom(s).
        frag2: Chem.Mol
            Second fragment RDKit molecule with dummy atom(s).
        dummy_idxs: tuple of int
            Indices of which dummy atom to use in frag1 and frag2.
            Default use the first dummy atom (index 0) in each fragment.
        sanitize: bool
            Whether to sanitize the final molecule.
        optimize: bool
            Whether to perform a quick optimization to relieve any clashes.

    Returns:
        combined_mol: Chem.Mol
            The combined molecule after alignment, bonding, and dummy removal.
        new_bond: tuple of int
            The atom indices of the new bond formed between frag1 and frag2.
    """
    # extract dummy and neighbor from frag1
    d1_idx, h1_idx, bond_type1 = _get_single_dummy_and_neighbor(frag1, dummy_idxs[0])

    # extract dummy and neighbor from frag2
    d2_idx, h2_idx, bond_type2 = _get_single_dummy_and_neighbor(frag2, dummy_idxs[1])

    # set bond type
    bond_order = bond_type1 # bond_order: Chem.BondType = Chem.BondType.SINGLE

    # Build a local frame consisting of dummy and two nearest neighbours for each fragment
    conf1 = frag1.GetConformer()
    conf2 = frag2.GetConformer()
    o1, F1 = _get_local_frame(conf1, frag1, d1_idx, h1_idx)
    o2, F2 = _get_local_frame(conf2, frag2, d2_idx, h2_idx)

    # reverse the dummy to neighbour axis on frag2 so orientate frags towards each other
    F2[:, 0] *= -1

    # Determine target distance between h1 and h2 based on covalent radii
    pt = rdchem.GetPeriodicTable()
    r1 = pt.GetRcovalent(frag1.GetAtomWithIdx(h1_idx).GetAtomicNum())
    r2 = pt.GetRcovalent(frag2.GetAtomWithIdx(h2_idx).GetAtomicNum())
    target_dist = (r1 + r2) #/ 2.0

    rotation_angle = 0
    
    while rotation_angle < 360:
        phi = np.deg2rad(rotation_angle)
        e2 = F2[:, 1].copy()
        e3 = F2[:, 2].copy()

        # rotate of frag2 about e1 by angle phi
        F2[:, 1] =  np.cos(phi) * e2 + np.sin(phi) * e3
        F2[:, 2] = -np.sin(phi) * e2 + np.cos(phi) * e3

        # rotation that aligns frame2 with frame1
        R = F1 @ F2.T

        # transformation to bring origins to o1
        t = (o1 + F1[:, 0] * target_dist) - R.dot(o2)


        # Apply (R, t) to all atoms in frag2
        old_pos = frag2.GetConformer().GetPositions()
        new_pos = old_pos.dot(R.T) + t 
        new_conf2 = Chem.Conformer(frag2.GetNumAtoms())
        for i, coords in enumerate(new_pos):
            new_conf2.SetAtomPosition(i, Chem.rdGeometry.Point3D(*coords))

        frag2_aligned = Chem.Mol(frag2)
        frag2_aligned.RemoveAllConformers()
        frag2_aligned.AddConformer(new_conf2, assignId=True)

        # combined molecule
        combined = Chem.CombineMols(frag1, frag2_aligned)
        em = Chem.EditableMol(combined)

        # calculate indices for dummy and neighbor atoms in combined molecule
        N1 = frag1.GetNumAtoms()
        H1_cidx = h1_idx
        H2_cidx = h2_idx + N1
        D1_cidx = d1_idx
        D2_cidx = d2_idx + N1

        # add bond between H1_cidx and H2_cidx
        em.AddBond(H1_cidx, H2_cidx, order=bond_order)
        new_bond = (H1_cidx, H2_cidx)

        # remove dummy atoms in descending order
        del_indices = sorted([D1_cidx, D2_cidx], reverse=True)
        for delete_idx in del_indices:
            em.RemoveAtom(delete_idx)

        final_bond = list(new_bond)
        for delete_idx in del_indices:
            for i, idx in enumerate(final_bond):
                if idx > delete_idx:
                    final_bond[i] -= 1
        new_bond = tuple(final_bond)

        new_mol = em.GetMol()

        if optimize or not has_nonbonded_overlaps(new_mol):
            
            if sanitize:
                Chem.SanitizeMol(new_mol)
                
            return new_mol, new_bond
        
        rotation_angle += rotation_angle_increment
    
    raise RuntimeError(f"Cannot place frag2 without atom overlap at {rotation_angle_increment} angle increments")

def _load_fragment_molecule_from_mol_block(
    mol_block: str, 
    dummy_atomic_number: int = None,
    sanitize: bool = False
) -> Chem.Mol:
    """
    Load an RDKit molecule from a Mol File string.
    """
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
    """
    Load an RDKit molecule from a Mol File.
    """
    if not os.path.exists(mol_file_path):
        raise FileNotFoundError(f"The file {mol_file_path} does not exist.")
    mol = Chem.MolFromMolFile(mol_file_path, removeHs=False, sanitize=sanitize)
    if mol is None:
        raise ValueError(f"Failed to load molecule from {mol_file_path}.")
    if dummy_atomic_number is not None:
        mol = reset_dummy_atom_atomic_numbers(mol, dummy_atomic_number)
    return mol


def make_binding_groups_coplanar(
        mol: Chem.Mol, 
        conf: Chem.Conformer, 
        is_2bent=False,
        binding_site_angle_offset=0.0,
    ):
    """
    Adjust torsions around binding sites so that they are aligned correctly. For
    two binding sites, this means making them coplanar.
    For three or more binding sites, this means making them all lie in a common plane.
    For 2-bent, this means aligning to plane including binding site axes intersection.

    # TODO: refactor to use functions from geo.py
    # TODO: remove carboxylate naming assumption

    Args:
        mol: Chem.Mol
            The RDKit molecule containing binding sites.
        conf: Chem.Conformer
            The conformer of the molecule to modify.
        is_2bent: bool
            Whether the molecule is a 2-bent type (special case for two binding sites).
        binding_site_angle_offset: float
            An angle offset to add to the final binding site torsions (degrees).   
    """
        
    #################################################################################
    # helper functions and opt objective functions
    #################################################################################
    def reset_conf(conf, orig):
        """Restore coordinates from original list."""
        for i, pos in enumerate(orig):
            conf.SetAtomPosition(i, pos)


    def fit_plane(points: np.ndarray):
        """Return (centroid, unit normal) of least-squares plane through points."""
        centroid = points.mean(axis=0)
        _, _, vh = np.linalg.svd(points - centroid)
        normal = vh[-1]
        return centroid, normal / np.linalg.norm(normal)
    
    def find_intersection_of_lines(p1, d1, p2, d2):
        """
        p1, p2: (3,) float arrays
            anchor points on the two lines
        d1, d2: (3,) float arrays
            direction vectors (need not be unit-length)

        Returns the midpoint of the shortest segment connecting the two
        infinite lines, or None if they are (numerically) parallel.
        """
        a = np.column_stack((d1, -d2))           # 3×2 matrix
        b = p2 - p1                              # 3-vector
        if np.linalg.matrix_rank(a) < 2:         # lines almost parallel
            raise ValueError("lines are parallel and do not have intersection point")
        # least-squares solution of  a*[t, s]^T = b
        t = np.linalg.lstsq(a, b, rcond=None)[0][0]
        intersection = p1 + t * d1 # p1 + t·d1
        return intersection
    
    def atom_array(idx):
        p = conf.GetAtomPosition(idx)
        return np.array([p.x, p.y, p.z])


    def objective_pairwise(angles, conf, orig_pos, cco_defs, inter_defs):
        """
        objective for 2-linear, makes binding groups coplanar
        
        args:
            angles: iterable of float
                trial torsion angles for each binding site
            conf: Chem.Conformer
                conformer to modify
            orig_pos: list of tuple of float
                original coordinates to reset to
            cco_defs: list of tuple of int
                torsion definitions for each binding site
            inter_defs: list of tuple of int
                torsion definitions for inter-binding site dihedrals
        returns:
            float
                sum of absolute values of inter-binding site dihedrals
        """
        reset_conf(conf, orig_pos)
        for theta, (a,b,c,d) in zip(angles, cco_defs):
            rdMolTransforms.SetDihedralDeg(conf, a, b, c, d, float(theta))
        inter_binding_site_dihedrals = [AllChem.GetDihedralDeg(conf, *d) for d in inter_defs]
        return float(np.sum(np.abs(inter_binding_site_dihedrals)))


    def objective_plane_atoms(angles, conf, orig_pos, cco_defs, mid_pairs, bind_atoms, inter_pt=None):
        """Minimise the sum of squared distances of binding atoms to the plane
        defined by the mid-points of the binding sites.

        Args:
            angles: iterable of float
                trial torsion angles for each binding site
            conf: Chem.Conformer
                conformer to modify
            orig_pos: list of tuple of float
                original coordinates to reset to
            cco_defs: list of tuple of int
                torsion definitions for each binding site
            mid_pairs: list of tuple of int
                pairs of atom indices defining mid-points for each binding site
            bind_atoms: list of int
                atom indices of all binding atoms
            inter_pt: (3,) float array or None
                optional intersection point to include in plane fitting

        Returns:
            float
                sum of squared distances of binding atoms to fitted plane
        """
        reset_conf(conf, orig_pos)
        # apply the trial torsions
        for theta, (a,b,c,d) in zip(angles, cco_defs):
            rdMolTransforms.SetDihedralDeg(conf, a, b, c, d, float(theta))

        # compute the mid‑points and fit their best‑fit plane
        mid_pts = []
        for o1, o2 in mid_pairs:
            p1, p2 = conf.GetAtomPosition(o1), conf.GetAtomPosition(o2)
            mid_pts.append([(p1.x+p2.x)*0.5, (p1.y+p2.y)*0.5, (p1.z+p2.z)*0.5])
        if inter_pt is not None:
            mid_pts.append(inter_pt)
        centroid, normal = fit_plane(np.asarray(mid_pts))

        # distances of all binding atoms to that plane
        acc = 0.0
        for idx in bind_atoms:
            p = conf.GetAtomPosition(idx)
            d = np.dot(np.array([p.x, p.y, p.z]) - centroid, normal)
            acc += d*d
        return float(acc)
    
    #################################################################################
    
    
    
    # save original coordinates
    orig_pos = [tuple(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]

    # get binding site indices by pattern matching
    patt_coo = Chem.MolFromSmarts('*[C;X3](=O)[O-]') # 0 = neighbour, 1 = C, 2 = O (double), 3 = O (single)
    matches = list(mol.GetSubstructMatches(patt_coo))

    patt2 = Chem.MolFromSmarts('*c1cn[n-]c1') # 0 = neighbour, 1 = c1, 2 = c2, 3 = n3, 4 = n4, 5 = c5
    matches += mol.GetSubstructMatches(patt2)

    n_sites = len(matches)
    if n_sites < 2:
        raise RuntimeError(f"Need ≥2 binding sites, found {n_sites}")

    # get torsion definitions for each binding fragment
    # second atom in neigbour, first atom in neighbour,
    # first atom in fragment, second atom in fragment 
    variable_torsions = []
    for m in matches:
        r = m[0]
        neigh = [nbr.GetIdx() for nbr in mol.GetAtomWithIdx(r).GetNeighbors()
                 if nbr.GetIdx() not in m]
        variable_torsions.append((neigh[0], r, m[1], m[2]))

    starting_binding_frag_dihedrals = [AllChem.GetDihedralDeg(conf, *t) for t in variable_torsions]

    # Optimise torsions numerically
    if n_sites == 2 and is_2bent: # special case for 2-bent
        (ra0, c0), (ra1, c1) = [(t[1], t[2]) for t in variable_torsions]
        # for coo-, ra = first neighbour atom, c = carbon atom
        # for pyra, ra = first neighbour atom, c = first ring carbon atom

        # get coordinates of neighbour and fragment atoms
        p1, p2 = atom_array(ra0), atom_array(c0)
        q1, q2 = atom_array(ra1), atom_array(c1)

        # line aligned from first frag atom to neighbour atom
        d1, d2 = (p2 - p1), (q2 - q1)

        # find intersection point of the two lines
        inter_pt = find_intersection_of_lines(p1, d1, q1, d2)

        # pairs of atom indices defining mid-points for each binding site
        # these are the two O atoms for carboxylate,
        # and currently C2 and N3 for pyrazolate (TODO: works, but change to N3 and N4)
        mid_pairs = [(m[2], m[3]) for m in matches]

        bind_atoms = [idx for m in matches for idx in (m[1], m[2], m[3])] # COO- indexes
        res = minimize(
            objective_plane_atoms,
            x0=np.array(starting_binding_frag_dihedrals),
            args=(conf, orig_pos, variable_torsions, mid_pairs, bind_atoms, inter_pt),
            method="Powell",
            options={"maxiter": 800, "disp": False},
        )

        # for 2-bent typically want to add 90° offset to final torsions
        binding_site_angle_offset = 90.0 + binding_site_angle_offset
    elif n_sites == 2: # 2-linear case
        # TODO: change to just use the first two atoms of frag? 
        # this was the idea and only assumes binding fragment isn't linear
        (c0, o0_db, o0_sg) = matches[0][1:4] # for pyrazolate, c0 is C1, o0_db is C2, o0_sg is N3 
        (c1, o1_db, o1_sg) = matches[1][1:4]
        inter_defs = [(o0_sg, c0, c1, o1_sg)]
        res = minimize(
            objective_pairwise,
            x0=np.array(starting_binding_frag_dihedrals),
            args=(conf, orig_pos, variable_torsions, inter_defs),
            method="Powell",
            options={"maxiter": 500, "disp": False},
        )
    else: # if n_sites >= 3, optimise to binding site plane 
        # for COO- midpoints are the two O atoms
        # for pyrazolate midpoints are currently C2 and N3 (TODO: change to N3 and N4)
        mid_pairs = [(m[2], m[3]) for m in matches] 
        bind_atoms = [idx for m in matches for idx in (m[1], m[2], m[3])] # COO- indexes
        res = minimize(
            objective_plane_atoms,
            x0=np.array(starting_binding_frag_dihedrals),
            args=(conf, orig_pos, variable_torsions, mid_pairs, bind_atoms),
            method="Powell",
            options={"maxiter": 800, "disp": False},
        )

    # update conformer with optimal torsions
    reset_conf(conf, orig_pos)
    for theta, (a,b,c,d) in zip(res.x, variable_torsions):
        rdMolTransforms.SetDihedralDeg(conf, a, b, c, d, float(theta + binding_site_angle_offset))



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
    """
    Update CBU JSON dict to include dummy atoms for carboxylate binding sites.
    """

    patt = Chem.MolFromSmarts('C(=O)[O-]')
    # patt = Chem.MolFromSmarts('C(=O)[O]')
    matches = mol.GetSubstructMatches(patt)

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
    """
    Update CBU JSON dict to include dummy atoms for pyrozolate binding sites.
    """
    patt2 = Chem.MolFromSmarts('c1cn[n-]c1')
    matches = mol.GetSubstructMatches(patt2)

    for c1_idx, c2_idx, n1_idx, n2_idx, c3_idx in matches:
        p1 = conf.GetAtomPosition(n1_idx)
        p2 = conf.GetAtomPosition(n2_idx)
        mx, my, mz = (p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0, (p1.z + p2.z) / 2.0

        # vector from carbon opposite nitrogens to midpoint of nitrogens
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
    Convert an RDKit Mol and Conformer into a CBU JSON dict.
    """

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

    # insert any binding site dummy atoms
    insert_carboxylate_binding_dummy_atoms(mol, conf, cbu_json)
    insert_pyrazole_binding_dummy_atoms(mol, conf, cbu_json)

    return cbu_json


def reassemble_two_smiles(
    smi1: str,
    smi2: str,
    dummy_atomic_number: int = 68,
    dummy_idxs: tuple =(0, 0),
    bond_order: Chem.BondType = Chem.BondType.SINGLE
) -> Chem.Mol:
    """
    Take two fragments encoded as SMILES, remove the dummies and connect 
    the two fragments by a new bond between the two neighbors.

    Args:
      smi1:  SMILES of fragment 1
      smi2:  SMILES of fragment 2
      dummy_atomic_number:  atomic number used for dummy atoms in the SMILES
      dummy_idxs:  tuple of (idx1, idx2) indicating which dummy atom to use
                    from each fragment (0-based)
      bond_order:  bond order to use for the new bond

    Returns:
      newmol:  combined Chem.Mol object
    """
    # load molecules
    m1 = Chem.MolFromSmiles(smi1, sanitize=False)
    m2 = Chem.MolFromSmiles(smi2, sanitize=False)
    if m1 is None or m2 is None:
        raise ValueError(f"Invalid SMILES: {smi1!r}, {smi2!r}")

    # find the dummy atoms in each frag
    d1 = [a.GetIdx() for a in m1.GetAtoms() if a.GetAtomicNum() == dummy_atomic_number]
    d2 = [a.GetIdx() for a in m2.GetAtoms() if a.GetAtomicNum() == dummy_atomic_number]

    d1_idx, d2_idx = dummy_idxs
    if not (0 <= d1_idx < len(d1)):
        raise ValueError(f"Invalid dummy_idx {d1_idx}; found {len(d1)} dummy atoms")
    if not (0 <= d2_idx < len(d2)):
        raise ValueError(f"Invalid dummy_idx {d2_idx}; found {len(d2)} dummy atoms")
    
    d1, d2 = d1[d1_idx], d2[d2_idx]

    # find their (single) heavy‐atom neighbors
    nbr1 = m1.GetAtomWithIdx(d1).GetNeighbors()[0].GetIdx()
    nbr2 = m2.GetAtomWithIdx(d2).GetNeighbors()[0].GetIdx()

    # combine graphs
    combo = Chem.CombineMols(m1, m2)
    em = Chem.EditableMol(combo)
    offset = m1.GetNumAtoms()

    # add the new bond
    em.AddBond(nbr1, nbr2 + offset, order=bond_order)

    # remove the dummy atoms (delete higher‐index first)
    for idx in sorted([d1, d2 + offset], reverse=True):
        em.RemoveAtom(idx)

    newmol = em.GetMol()
    Chem.SanitizeMol(newmol)
    return newmol

def smiles_assemble_fragments_to_cbu(
    linker_smiles: list[str],
    binding_smiles: str,
    node_smiles: str = None,
    dummy_atomic_number: int = 68,
    linker_first_dummy_idxs: list[int] = None,
    **kwargs
) -> tuple[dict, str]:
    """
    Assemble a CBU from SMILES fragments without a geometry

    Args:
        linker_smiles:  list of SMILES strings for linker fragments
        binding_smiles:  SMILES string for binding group fragment
        node_smiles:  SMILES string for node fragment (optional)
        dummy_atomic_number:  atomic number used for dummy atoms in the SMILES
        linker_first_dummy_idxs:  index of first dummy atom connected in each linker frag

    Returns:
        cbu_smiles:  SMILES string of the assembled CBU
        formula:  molecular formula of the assembled CBU   
    """
    # start from the binding group
    cbu = Chem.MolFromSmiles(binding_smiles, sanitize=False)
    Chem.SanitizeMol(cbu)

    if linker_first_dummy_idxs is None:
        dummy_indices = [(0,0) for _ in linker_mols]
    else:
        assert len(linker_first_dummy_idxs) == len(linker_smiles), "must have equal number of linker dummy indices and linker frags"
        dummy_indices = [ (0, idx) for idx in linker_first_dummy_idxs ]

    # attach each linker
    for i, smi in enumerate(linker_smiles):
        cbu = reassemble_two_smiles(
            Chem.MolToSmiles(cbu, canonical=True),
            smi,
            dummy_atomic_number=dummy_atomic_number,
            dummy_idxs=dummy_indices[i]
        )
    # if no node, cap with binding group
    if node_smiles is None:
        cbu = reassemble_two_smiles(
            Chem.MolToSmiles(cbu, canonical=True),
            binding_smiles,
            dummy_atomic_number=dummy_atomic_number
        )
    else: # if node, attach copies of arms onto node
        node = Chem.MolFromSmiles(node_smiles, sanitize=False)
        Chem.SanitizeMol(node)
        arm_smi = Chem.MolToSmiles(cbu, canonical=True)
        # count dummies in the node
        n_dummies = sum(1 for a in node.GetAtoms() if a.GetAtomicNum() == dummy_atomic_number)
        assembled = node
        for _ in range(n_dummies):
            assembled = reassemble_two_smiles(
                Chem.MolToSmiles(assembled, canonical=True),
                arm_smi,
                dummy_atomic_number=dummy_atomic_number
            )
        cbu = assembled

    Chem.SanitizeMol(cbu)
    cbu_smiles = Chem.MolToSmiles(cbu, canonical=True)
    formula = rdMolDescriptors.CalcMolFormula(cbu)
    return cbu_smiles, formula



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
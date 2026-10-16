# Step 1 of the synthesis prediction: for each base MOP_0, find all candidate tuples (MOP_x, MOP_1, MOP_2)
# (see queryMOPs.getCandidateTuples) and rank them by how well the known syntheses of MOP_0, MOP_1 and MOP_2
# are expected to transfer to MOP_x. Writes one CSV per base MOP.
import os
import sys
# make the shared modules in the repo root importable
parent = parent = os.path.abspath('')
sys.path.append(parent)
sys.path.append('..')
from twa.kg_operations import PySparqlClient
import pandas as pd
import queryMOPs
import credentials
import ontomops
import ontosyn
import mops_synthesis

# base MOPs (MOP_0) for which candidate tuples are searched
Zr_H2BDC_MOP = "[Zr3O(OH)3(C5H5)3]4[(C6H4)(CO2)2]6"
Zr_H3BTC_MOP = "[Zr3O(OH)3(C5H5)3]4[(C6H3)(CO2)3]4"
Zr_H2BPDC_MOP = "[Zr3O(OH)3(C5H5)3]4[(C6H4)2(CO2)2]6"

# True: MOP_x is a computationally assembled (novel) MOP, False: MOP_x is an experimentally reported MOP
MOP_NOVELTY = True

# provenance DOIs of the assembled MOPs, MOP_1 and MOP_2 must not stem from these
ASSEMBLED_MOP_DOI_1 = "10.1021/jacs.2c03402"
ASSEMBLED_MOP_DOI_2 = "10.1039/D5DD00069F"
assembled_mop_dois = [ASSEMBLED_MOP_DOI_1,ASSEMBLED_MOP_DOI_2]

mops_client = PySparqlClient(credentials.ONTOMOPS_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)
syn_client = PySparqlClient(credentials.ONTOSYN_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)

# retrieve the base MOPs
mops_query = queryMOPs.getMOPIRI([Zr_H2BDC_MOP,Zr_H3BTC_MOP,Zr_H2BPDC_MOP])
mops_response = mops_client.perform_query(mops_query)
mop0_iris = []
for mop0_iri in mops_response:
    mop0_iris.append(mop0_iri['mop'])
mop0_list = ontomops.MetalOrganicPolyhedron.pull_from_kg(mop0_iris,mops_client,0)

for mop0 in mop0_list:

    # find all candidate tuples for this base MOP
    mop0_label = list(mop0.hasMOPFormula)[0]
    mops_query = queryMOPs.getCandidateTuples(mop0_label,assembled_mop_dois,MOP_NOVELTY)
    predictable_mops = mops_client.perform_query(mops_query)
    
    rows = []
    print("Base MOP " + mop0_label  + " yields a total of " + str(len(predictable_mops)) + " tupels")
    i=0
    for tupel in predictable_mops:
        i = i+1
        print("== Tupel " + str(i) +" ==")

        # This code needs to be written in this slightly awkward manner because the "pull_from_kg" method currently does not
        # guarantee returning the queried instances of a given IRI list in the same order as defined through the IRI list.
        [mopx] = ontomops.MetalOrganicPolyhedron.pull_from_kg(tupel['MOP_x'],mops_client,0)
        [mop1] = ontomops.MetalOrganicPolyhedron.pull_from_kg(tupel['MOP_1'],mops_client,0)
        [mop2] = ontomops.MetalOrganicPolyhedron.pull_from_kg(tupel['MOP_2'],mops_client,0)
        print("MOPs loaded")

        # metal CBUs (M0 of MOP_0/MOP_x, M1 of MOP_1/MOP_2) and organic CBUs (L0 of MOP_0/MOP_1, L2 of MOP_x/MOP_2)
        [M0] = ontomops.ChemicalBuildingUnit.pull_from_kg(tupel['metalCBU_0'],mops_client,1)
        [M1] = ontomops.ChemicalBuildingUnit.pull_from_kg(tupel['metalCBU_2'],mops_client,1)
        [L0] = ontomops.ChemicalBuildingUnit.pull_from_kg(tupel['organicCBU_0'],mops_client,1)
        [L2] = ontomops.ChemicalBuildingUnit.pull_from_kg(tupel['organicCBU_x'],mops_client,1)
        print("CBUs loaded")

        # load the syntheses of the three known MOPs, the tuple is skipped (marked '-') if any of them is missing
        syn0 = mops_synthesis.getMOPSynthesis(mop0,syn_client)
        syn1 = mops_synthesis.getMOPSynthesis(mop1,syn_client)
        syn2 = mops_synthesis.getMOPSynthesis(mop2,syn_client)
        
        if syn0 == False or syn1 == False or syn2 == False:
            rows.append({
                "id" : i,
                "MOPx" : list(mopx.hasMOPFormula)[0],
                "MOP1" : list(mop1.hasMOPFormula)[0],
                "MOP2" : list(mop2.hasMOPFormula)[0],
                "AM1=AM0" : '-',
                "AM2=AMx" : '-',
                "T2=T1" : '-',
                "RM1=RM2" : '-',
                "P1=P2" : '-',
                "AM1=AM2" : '-',
                "AM0=AMx" : '-',
                "BL0=BL2": '-',
                "S2=S0": '-',
                "criteria": '-'
            })
            print("Failed to load syntheses!")
            print("========")
            print("")
            continue
        else:
            print("Syntheses loaded")
        
        # metal reactants used in the syntheses of MOP_1 and MOP_2 (both contain the metal CBU M1)
        R_M1 = mops_synthesis.getInputAssociatedWithCBU(syn1,M1.instance_iri,syn_client)
        R_M2 = mops_synthesis.getInputAssociatedWithCBU(syn2,M1.instance_iri,syn_client)
        print("Reactants loaded")

        # strong criteria (weight 0.2): same assembly models (AM) across the square, similar heating temperature, same metal reactant
        # weak criteria (weight 0.1): same publication, same AM for all four MOPs, same ligand binding fragment, same solvent
        crit1a = mop1.hasAssemblyModel == mop0.hasAssemblyModel
        crit1b = mop2.hasAssemblyModel == mopx.hasAssemblyModel
        crit2 = mops_synthesis.compareHeating(syn2,syn1)
        crit3 = R_M1 != False and R_M1 == R_M2
        crit4 = mop1.hasProvenance == mop2.hasProvenance
        crit5a = mop1.hasAssemblyModel == mop2.hasAssemblyModel
        crit5b = mop0.hasAssemblyModel == mopx.hasAssemblyModel
        crit6 = mops_synthesis.compareBindingSites(L0,L2)
        crit7 = mops_synthesis.compareSolvents(syn2,syn0,syn_client)
        print("Criteria checked")

        rows.append({
            "id" : i,
            "MOPx" : list(mopx.hasMOPFormula)[0],
            "MOP1" : list(mop1.hasMOPFormula)[0],
            "MOP2" : list(mop2.hasMOPFormula)[0],
            "AM1=AM0" : crit1a,
            "AM2=AMx" : crit1b,
            "T2=T1" : crit2,
            "RM1=RM2" : crit3,
            "P1=P2" : crit4,
            "AM1=AM2" : crit5a,
            "AM0=AMx" : crit5b,
            "BL0=BL2": crit6,
            "S2=S0": crit7,
            "criteria": (crit1a and crit1b)*0.2+crit2*0.2+crit3*0.2+crit4*0.1+(crit5a and crit5b)*0.1+crit6*0.1+crit7*0.1
        })
        print("========")
        print("")

    # collect the scores of all tuples and save them
    syn_crit = pd.DataFrame(rows,columns=["id","MOPx","MOP1","MOP2","AM1=AM0","AM2=AMx","T2=T1","RM1=RM2","P1=P2","AM1=AM2","AM0=AMx","BL0=BL2","S2=S0","criteria"])
    if MOP_NOVELTY is True:
        novel_string = "novel"
    else:
        novel_string = "existing"

    print("--------------------------------------------------------------")
    print("Possible "+novel_string+" MOP tuples for base MOP " + list(mop0.hasMOPFormula)[0] + ":")
    print(syn_crit)
    print("--------------------------------------------------------------")
    
    syn_crit.to_csv("MOP_criteria_" + list(mop0.hasMOPFormula)[0] + "_" + novel_string +".csv")
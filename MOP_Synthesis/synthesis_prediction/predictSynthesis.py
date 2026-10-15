import os
import sys
parent = parent = os.path.abspath('')
sys.path.append(parent)
sys.path.append('..')
from twa.kg_operations import PySparqlClient
import credentials
import ontomops
import ontosyn
import mops_synthesis
import queryMOPs

############### DEF ##############
MOPX = "[Zr3O(OH)3(C5H5)3]4[(C6H4C)2(CO2)2]6"
MOP0 = "[Zr3O(OH)3(C5H5)3]4[(C6H3)(CO2)3]4"
MOP1 = "[V6O6(OCH3)9(SO4)]4[(C6H3)(CO2)3]4"
MOP2 = "[V6O6(OCH3)9(SO4)]4[(C6H4C)2(CO2)2]6"

anchor_amount = 50.0
mass_unit = 'milligram'
volume_unit = 'millilitre'
temp_unit = 'celsius'
time_unit = 'hour'
##################################
syn_client = PySparqlClient(credentials.ONTOSYN_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)
mops_client = PySparqlClient(credentials.ONTOMOPS_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)

mop_list=[MOP0,MOP1,MOP2,MOPX]
mops = list()
for mop in mop_list:
    mops_query = queryMOPs.getMOPIRI([mop])
    mops_response = mops_client.perform_query(mops_query)
    mop_iri = mops_response[0]['mop']
    mops.append(ontomops.MetalOrganicPolyhedron.pull_from_kg(mop_iri,mops_client,3)[0])


syn0 = mops_synthesis.getMOPSynthesis(mops[0],syn_client)
syn1 = mops_synthesis.getMOPSynthesis(mops[1],syn_client)
syn2 = mops_synthesis.getMOPSynthesis(mops[2],syn_client)


CBU_M=['','','','']
CBU_L=['','','','']
for i, mop in enumerate(mops):
    for cbu in mop.hasChemicalBuildingUnit:
        if isinstance(list(cbu.hasBindingSite)[0],ontomops.MetalSite):
            CBU_M[i] = cbu
        else:
            CBU_L[i] = cbu 


reactant_M = mops_synthesis.getInputAssociatedWithCBU(syn0,CBU_M[3].instance_iri,syn_client)
reactant_L = mops_synthesis.getInputAssociatedWithCBU(syn2,CBU_L[3].instance_iri,syn_client)
solvent = mops_synthesis.getSolvent(syn2,syn_client)
heating = mops_synthesis.getMainHeating(syn0)
heating[0] = mops_synthesis.convertUnit(heating[0],temp_unit)
heating[1] = mops_synthesis.convertUnit(heating[1],time_unit)

ADD_S=['','','']
ADD_M=['','','']
ADD_L=['','',''] 

for i, syn in enumerate([syn0,syn1,syn2]):
    ADD_M[i] = mops_synthesis.getAddedAmountsAssociatedWithCBU(syn,CBU_M[i].instance_iri,syn_client)
    ADD_M[i] = mops_synthesis.convertUnit(ADD_M[i],mass_unit)
    ADD_L[i] = mops_synthesis.getAddedAmountsAssociatedWithCBU(syn,CBU_L[i].instance_iri,syn_client)
    ADD_L[i] = mops_synthesis.convertUnit(ADD_L[i],mass_unit)
    ADD_S[i] = mops_synthesis.getSolventAmount(syn,syn_client)
    ADD_S[i] = mops_synthesis.convertUnit(ADD_S[i],volume_unit)

amount_M = [anchor_amount, mass_unit]

M_L_ratio = ADD_M[2][0]*ADD_L[1][0]*ADD_M[0][0]/(ADD_M[1][0]*ADD_L[2][0]*ADD_L[0][0])
amount_L = amount_M.copy()
amount_L[0] = amount_M[0] / M_L_ratio

solvent_ratio=[0,0,0,0]
for i in range(0,3):
    solvent_ratio[i] = ADD_S[i][0] / (ADD_M[i][0]+ADD_L[i][0])
solvent_ratio[3] = solvent_ratio[2]/solvent_ratio[1]*solvent_ratio[0]

amount_S = ADD_S[2].copy()
amount_S[0] = solvent_ratio[3] * (amount_M[0] + amount_L[0])

text = f"""
    Dissolve {round(amount_M[0],1)} {amount_M[1]} of {list(reactant_M.rdfs_label)[0]} 
    and {round(amount_L[0],1)} {amount_L[1]} of {list(reactant_L.rdfs_label)[0]} 
    in {round(amount_S[0],1)} {amount_S[1]} of {list(solvent.rdfs_label)[0]} along with a few drops of distilled water. 
    Heat the mixture at {round(heating[0][0],1)} {heating[0][1]} for {round(heating[1][0],1)} {heating[1][1]}. 
    Crystallise under static conditions, then allow to cool to room temperature in air. 
    Filter the resulting crystals and wash repeatedly with {list(solvent.rdfs_label)[0]}.
    """

out = []
out.append([[list(reactant_M.rdfs_label)[0],round(amount_M[0],2)],
           [list(reactant_L.rdfs_label)[0],round(amount_L[0],2)],
           [list(solvent.rdfs_label)[0],round(amount_S[0],1)],
           [round(heating[0][0],1),round(heating[1][0],1)]])

print(text)
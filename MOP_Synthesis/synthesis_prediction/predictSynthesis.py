import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
sys.path.append('..')
from twa.kg_operations import PySparqlClient
import pandas as pd
import queryMOPs
import credentials
import ontomops
import ontosyn
from pint import UnitRegistry
import mops_synthesis

############### DEF ##############
MOPX_IRI = "https://www.theworldavatar.com/kg/ontomops/MetalOrganicPolyhedra_7f5757c2-fc8b-4820-972f-689f36c76f0c"
MOP0_IRI = "https://www.theworldavatar.com/kg/ontomops/MetalOrganicPolyhedra_e67c729f-f153-4742-9fee-e00c623d151b"
MOP1_IRI = "https://www.theworldavatar.com/kg/ontomops/MetalOrganicPolyhedra_a6eebd24-3cd1-4084-b8b9-8583940167e5"
MOP2_IRI = "https://www.theworldavatar.com/kg/ontomops/MetalOrganicPolyhedra_bc771edc-702d-4cea-8495-e8128c54ebe5"


anchor_amount = 30.0
mass_unit = 'milligram'
volume_unit = 'millilitre'
temp_unit = 'celsius'
time_unit = 'hour'
##################################
mop_iris = [MOP0_IRI,MOP1_IRI,MOP2_IRI,MOPX_IRI]
ureg = UnitRegistry(autoconvert_offset_to_baseunit = True)

syn_client = PySparqlClient(credentials.ONTOSYN_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)
mops_client = PySparqlClient(credentials.ONTOMOPS_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)
mops = list()
for mop_iri in mop_iris:
    mops.append(ontomops.MetalOrganicPolyhedron.pull_from_kg(mop_iri,mops_client,2)[0])


#SAME AS IN selectCandidates.py!!
def getMOPSynthesis(mop): 
    syn_iri = syn_client.perform_query(queryMOPs.getSynthesis(mop))
    if len(list(syn_iri)) != 1:
        return False
    else:
        [syn] = ontosyn.ChemicalSynthesis.pull_from_kg(list(syn_iri)[0]["chemSyn"],syn_client,4)
        return syn

#SAME AS IN selectCandidates.py!! 
def getSpecies(chemicalInput):
    material=list(chemicalInput.referencesMaterial)[0]
    thermoBehaviour=list(material.thermodynamicBehaviour)[0]
    subsystems=list(thermoBehaviour.isComposedOfSubsystem)
    species = list(subsystems[0].representsOccurenceOf)[0]
    return(species)

#ALMOST SAME AS IN selectCandidates.py!! (passing on client)
def getInputAssociatedWithCBU(syn,cbu_iri,client):
    cbu = ontomops.ChemicalBuildingUnit.pull_from_kg(cbu_iri,client,0)
    cbu_specs = list(cbu[0].isUsedAsChemical)
    for cbu_spec in cbu_specs:
        for input in syn.hasChemicalInput:
            spec = getSpecies(input)
            if cbu_spec == spec:
                species = ontosyn.Species.pull_from_kg(spec,client,0)
                return species[0] 
    return False

def getAddedAmountsAssociatedWithCBU(syn,cbu_iri,client):
    cbu = ontomops.ChemicalBuildingUnit.pull_from_kg(cbu_iri,client,0)
    cbu_specs = list(cbu[0].isUsedAsChemical)
    for cbu_spec in cbu_specs:
        for input in syn.hasChemicalInput:
            spec = getSpecies(input)
            if cbu_spec == spec:
                for step in list(syn.hasSynthesisStep):
                    if step.__class__ == ontosyn.Add:
                        chemIn = list(step.hasAddedChemicalInput)[0]
                        if chemIn == input:
                            mat=list(chemIn.referencesMaterial)[0]
                            phase=list(mat.thermodynamicBehaviour)[0]
                            comp_iri=list(phase.hasComposition)[0].instance_iri
                            comp = ontosyn.Composition.pull_from_kg(comp_iri,client,-1)
                            conc=list(comp[0].comprisesDirectly)[0]
                            addVal = getValue(conc)
                            return addVal
    return False

#SAME AS IN selectCandidates.py!!
def getSolvent(syn,client):
    for step in syn.hasSynthesisStep:
        if step.__class__ == ontosyn.Dissolve:
            solventInput = list(step.hasSolventDissolve)[0]
            solvent_iri = getSpecies(solventInput)
            solvent = ontosyn.Species.pull_from_kg(solvent_iri,client,0)
            return solvent[0]
    return False

def getSolventAmount(syn,client):
    for step in syn.hasSynthesisStep:
        if step.__class__ == ontosyn.Dissolve:
            solventInput = list(step.hasSolventDissolve)[0]
            mat=list(solventInput.referencesMaterial)[0]
            phase=list(mat.thermodynamicBehaviour)[0]
            comp_iri=list(phase.hasComposition)[0].instance_iri
            comp = ontosyn.Composition.pull_from_kg(comp_iri,client,-1)
            conc=list(comp[0].comprisesDirectly)[0]
            dissVal = getValue(conc)
            return dissVal
    return False

#SAME AS IN selectCandidates.py!!
def getMainHeating(syn):
    heating=[]
    for step in syn.hasSynthesisStep:
        if step.__class__ == ontosyn.HeatChill:
            stepTemp=list(step.hasTargetTemperature)[0]
            stepTempVal=getValue(stepTemp)
            if stepTempVal[1]=="kelvin":
                stepTempVal[0]-=273.15
                stepTempVal[1]="celsius"
            stepDur=list(step.hasStepDuration)[0]
            stepDurVal=getValue(stepDur)
            if stepDurVal[1]=="day":
                stepDurVal[0]*=24
                stepDurVal[1]="hour"
            heating.append([stepTempVal,stepDurVal])
    i = 0
    i_max = 0
    max_temp = 0
    for heat in heating:
        temp = heat[0][0]*heat[1][0]
        if temp > max_temp:
            max_temp = temp
            i_max = i
        i+=1
    return heating[i_max]

#AMOST SAME AS IN selectCandidates.py (here, meas is pulled)
#NOT THE SAME AS IN retrieve_synthesis.py!!
def getValue(meas,defaultString="unknown"):
    val = list(meas.hasValue)[0]
    numVal=list(val.hasNumericalValue)[0]
    unit=list(val.hasUnit)[0]
    unitLab=list(unit.rdfs_label)[0]
    return [numVal,unitLab]

def convertUnit(scalar,unit):
    temp=scalar[0]*ureg.parse_expression(scalar[1].replace(' ','_'))
    temp=temp.to(ureg(unit))
    scalar[0]=temp.magnitude
    scalar[1]=unit
    return scalar

syn0 = getMOPSynthesis(mops[0])
syn1 = getMOPSynthesis(mops[1])
syn2 = getMOPSynthesis(mops[2])


CBU_M=['','','','']
CBU_L=['','','','']
for i, mop in enumerate(mops):
    for cbu in mop.hasChemicalBuildingUnit:
        if list(cbu.hasBindingSite)[0].__class__ == ontomops.MetalSite:
            CBU_M[i] = cbu
        else:
            CBU_L[i] = cbu 


reactant_M = getInputAssociatedWithCBU(syn0,CBU_M[3].instance_iri,syn_client)
reactant_L = getInputAssociatedWithCBU(syn2,CBU_L[3].instance_iri,syn_client)
solvent = getSolvent(syn2,syn_client)
heating = getMainHeating(syn0)
heating[0] = convertUnit(heating[0],temp_unit)
heating[1] = convertUnit(heating[1],time_unit)

ADD_S=['','','']
ADD_M=['','','']
ADD_L=['','',''] 

for i, syn in enumerate([syn0,syn1,syn2]):
    ADD_M[i] = getAddedAmountsAssociatedWithCBU(syn,CBU_M[i].instance_iri,syn_client)
    ADD_M[i] = convertUnit(ADD_M[i],mass_unit)
    ADD_L[i] = getAddedAmountsAssociatedWithCBU(syn,CBU_L[i].instance_iri,syn_client)
    ADD_L[i] = convertUnit(ADD_L[i],mass_unit)
    ADD_S[i] = getSolventAmount(syn,syn_client)
    ADD_S[i] = convertUnit(ADD_S[i],volume_unit)

amount_M = [anchor_amount, mass_unit]

M_L_ratio = ADD_M[2][0]*ADD_L[1][0]*ADD_M[0][0]/(ADD_M[1][0]*ADD_L[2][0]*ADD_L[0][0])
amount_L = amount_M
amount_L[0] = amount_M[0] / M_L_ratio

solvent_ratio=[0,0,0,0]
for i in range(0,3):
    solvent_ratio[i] = ADD_S[i][0] / (ADD_M[i][0]+ADD_L[i][0])
solvent_ratio[3] = solvent_ratio[2]/solvent_ratio[1]*solvent_ratio[0]

amount_S = ADD_S[2]
amount_S[0] = solvent_ratio[3] * (amount_M[0] + amount_L[0])

text = f"""
    Dissolve {round(amount_M[0],2)} {amount_M[1]} of {list(reactant_M.rdfs_label)[0]} 
    and {round(amount_L[0],2)} {amount_L[1]} of {list(reactant_L.rdfs_label)[0]} 
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
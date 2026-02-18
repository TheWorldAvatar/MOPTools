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

Zr_H2BDC_MOP_IRI = "https://www.theworldavatar.com/kg/ontomops/MetalOrganicPolyhedra_e67c729f-f153-4742-9fee-e00c623d151b"
Zr_H3BTC_MOP_IRI = "https://www.theworldavatar.com/kg/ontomops/MetalOrganicPolyhedra_1d52f054-9421-4aac-bd29-76d8a9519ccb"
Zr_H2BPDC_MOP_IRI = "https://www.theworldavatar.com/kg/ontomops/MetalOrganicPolyhedra_3d71c19a-ab54-4993-8c94-267dcfe41792"
mop0_iris = [Zr_H2BDC_MOP_IRI,Zr_H3BTC_MOP_IRI,Zr_H2BPDC_MOP_IRI]

ASSEMBLED_MOP_DOI_1 = "10.1021/jacs.2c03402"
ASSEMBLED_MOP_DOI_2 = "Placeholder DOI for TWA OGM"
assembled_mop_dois = [ASSEMBLED_MOP_DOI_1,ASSEMBLED_MOP_DOI_2]

mops_client = PySparqlClient(credentials.ONTOMOPS_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)
syn_client = PySparqlClient(credentials.ONTOSYN_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)
mop0_list = ontomops.MetalOrganicPolyhedron.pull_from_kg(mop0_iris,mops_client,0)

def compareBindingSites(L0,L2):
    bs0_type = []
    bs2_type = []
    for bs in list(L0.hasBindingSite):
        bs0_type.append(list(bs.hasBindingFragment)[0])
    for bs in list(L2.hasBindingSite):
        bs2_type.append(list(bs.hasBindingFragment)[0])
    return set(bs0_type)==set(bs2_type)

def compareHeating(syn1,syn2):
    heat1 = getMainHeating(syn1)
    heat2 = getMainHeating(syn2)
    if abs(heat1[0][0]-heat2[0][0]) < 0.1*heat1[0][0]:
        return True
    else:
        return False
    
def getSpecies(chemicalInput):
    material=list(chemicalInput.referencesMaterial)[0]
    thermoBehaviour=list(material.thermodynamicBehaviour)[0]
    subsystems=list(thermoBehaviour.isComposedOfSubsystem)

    if len(subsystems)==1: 
        species = list(subsystems[0].representsOccurenceOf)[0]

    return(species)

def getMainHeating(syn):
    heating=[]
    for step in syn.hasSynthesisStep:
        if step.__class__ == ontosyn.HeatChill:
            stepTemp=list(step.hasTargetTemperature)[0]
            stepTempVal=getValue(stepTemp)
            if stepTempVal[1]=="kelvin":
                stepTempVal[0]-=273.15
                stepTempVal[1]=="celsius"
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


def getValue(meas,defaultString="unknown"):
    val = list(meas.hasValue)[0]
    numVal=list(val.hasNumericalValue)[0]
    unit=list(val.hasUnit)[0]
    unitLab=list(unit.rdfs_label)[0]
    return [numVal,unitLab]

for mop0 in mop0_list:

    mop0_label = list(mop0.hasMOPFormula)[0]
    mops_query = queryMOPs.simple_query(mop0_label,assembled_mop_dois)
    predictable_mops = mops_client.perform_query(mops_query)
    
    syn_crit = pd.DataFrame(columns=["id","MOPx","MOP1","MOP2","AM1=AM0","AM2=AMx","T2=T1","RM2=RM3"])
    for tupel in predictable_mops:
        
        # This code needs to be written in this slightly awkward manner because the "pull_from_kg" method currently does not
        # guarantee returning the queried instances of a given IRI list in the same order as defined through the IRI list.
        [mopx] = ontomops.MetalOrganicPolyhedron.pull_from_kg(tupel['MOP_x'],mops_client,0)
        [mop1] = ontomops.MetalOrganicPolyhedron.pull_from_kg(tupel['MOP_1'],mops_client,0)
        [mop2] = ontomops.MetalOrganicPolyhedron.pull_from_kg(tupel['MOP_2'],mops_client,0)

        [M0] = ontomops.ChemicalBuildingUnit.pull_from_kg(tupel['metalCBU_0'],mops_client,1)
        [M1] = ontomops.ChemicalBuildingUnit.pull_from_kg(tupel['metalCBU_2'],mops_client,1)
        [L0] = ontomops.ChemicalBuildingUnit.pull_from_kg(tupel['organicCBU_0'],mops_client,1)
        [L2] = ontomops.ChemicalBuildingUnit.pull_from_kg(tupel['organicCBU_x'],mops_client,1)

        syn0_iri = syn_client.perform_query(queryMOPs.getSynthesis(mop0))
        syn1_iri = syn_client.perform_query(queryMOPs.getSynthesis(mop1))
        syn2_iri = syn_client.perform_query(queryMOPs.getSynthesis(mop2))
        [syn0] = ontosyn.ChemicalSynthesis.pull_from_kg(list(syn0_iri)[0]["chemSyn"],syn_client,-1)
        [syn1] = ontosyn.ChemicalSynthesis.pull_from_kg(list(syn1_iri)[0]["chemSyn"],syn_client,-1)
        [syn2] = ontosyn.ChemicalSynthesis.pull_from_kg(list(syn2_iri)[0]["chemSyn"],syn_client,-1)
        
        crit1a = mop1.hasAssemblyModel == mop0.hasAssemblyModel
        crit1b = mop2.hasAssemblyModel == mopx.hasAssemblyModel
        crit2 = compareHeating(syn2,syn1)
        #crit3
        crit4 = mop1.hasProvenance == mop2.hasProvenance
        crit5a = mop1.hasAssemblyModel == mop2.hasAssemblyModel
        crit5b = mop0.hasAssemblyModel == mopx.hasAssemblyModel
        crit6 = compareBindingSites(L0,L2)
        
        #crit7

        print("test")



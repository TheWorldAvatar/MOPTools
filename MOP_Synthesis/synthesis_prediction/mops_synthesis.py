# Helper functions to read synthesis conditions (reactants, amounts, solvent, heating) from OntoSyn
# and to compare them between MOPs. Used by selectCandidates.py and predictSynthesis.py.
import ontosyn
import queryMOPs
import ontomops
from pint import UnitRegistry


def getMOPSynthesis(mop,client): 
    """Pull the (unique) ChemicalSynthesis of a MOP from OntoSyn, returns False if there is none or more than one."""
    syn_iri = client.perform_query(queryMOPs.getSynthesis(mop.hasMOPFormula))
    if len(list(syn_iri)) != 1:
        return False
    else:
        [syn] = ontosyn.ChemicalSynthesis.pull_from_kg(list(syn_iri)[0]["chemSyn"],client,4)
        return syn


def getSpecies(chemicalInput):
    """Species of a ChemicalInput (ChemicalInput -> Material -> SinglePhase -> first PhaseComponent -> Species)."""
    material=list(chemicalInput.referencesMaterial)[0]
    thermoBehaviour=list(material.thermodynamicBehaviour)[0]
    subsystems=list(thermoBehaviour.isComposedOfSubsystem)
    species = list(subsystems[0].representsOccurenceOf)[0]
    return(species)

def getAddedAmountsAssociatedWithCBU(syn,cbu_iri,client):
    """[value, unit] of the amount added in the Add step whose chemical input is the species used as the given CBU.
    Returns False if no such input / Add step exists.
    """
    cbu = ontomops.ChemicalBuildingUnit.pull_from_kg(cbu_iri,client,0)
    cbu_specs = list(cbu[0].isUsedAsChemical)
    for cbu_spec in cbu_specs:
        for input in syn.hasChemicalInput:
            spec = getSpecies(input)
            if cbu_spec == spec:
                for step in list(syn.hasSynthesisStep):
                    if isinstance(step,ontosyn.Add):
                        chemIn = list(step.hasAddedChemicalInput)[0]
                        if chemIn == input:
                            # the amount is stored as the (first) concentration of the material's composition
                            mat=list(chemIn.referencesMaterial)[0]
                            phase=list(mat.thermodynamicBehaviour)[0]
                            comp_iri=list(phase.hasComposition)[0].instance_iri
                            comp = ontosyn.Composition.pull_from_kg(comp_iri,client,-1)
                            conc=list(comp[0].comprisesDirectly)[0]
                            addVal = getValue(conc)
                            return addVal
    return False

def getSolvent(syn,client):
    """Solvent species of the first Dissolve step (pulled from the KG if only its IRI is known)."""
    for step in syn.hasSynthesisStep:
        if isinstance(step,ontosyn.Dissolve):
            solventInput = list(step.hasSolventDissolve)[0]
            solvent_iri = getSpecies(solventInput)
            if type(solvent_iri) is str:
                solvent = ontosyn.Species.pull_from_kg(solvent_iri,client,0)
                return solvent[0]
            else:
                return solvent_iri                
    return False

def getSolventAmount(syn,client):
    """[value, unit] of the solvent amount used in the first Dissolve step."""
    for step in syn.hasSynthesisStep:
        if isinstance(step,ontosyn.Dissolve):
            solventInput = list(step.hasSolventDissolve)[0]
            mat=list(solventInput.referencesMaterial)[0]
            phase=list(mat.thermodynamicBehaviour)[0]
            comp_iri=list(phase.hasComposition)[0].instance_iri
            comp = ontosyn.Composition.pull_from_kg(comp_iri,client,-1)
            conc=list(comp[0].comprisesDirectly)[0]
            dissVal = getValue(conc)
            return dissVal
    return False


def getValue(meas):
    """[numerical value, unit label] of an OM quantity."""
    val = list(meas.hasValue)[0]
    numVal=list(val.hasNumericalValue)[0]
    unit=list(val.hasUnit)[0]
    unitLab=list(unit.rdfs_label)[0]
    return [numVal,unitLab]

def getMainHeating(syn):
    """[[temperature, unit], [duration, unit]] of the "main" HeatChill step,
    i.e. the step with the largest temperature * duration product (in celsius * hours).
    """
    heating=[]
    for step in syn.hasSynthesisStep:
        if isinstance(step,ontosyn.HeatChill):
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
    # pick the step with the largest temperature * duration
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

def convertUnit(scalar,unit):
    """Convert a [value, unit label] pair in place to the target unit via pint (spaces in unit labels become underscores)."""
    ureg = UnitRegistry(autoconvert_offset_to_baseunit = True)
    temp=scalar[0]*ureg.parse_expression(scalar[1].replace(' ','_'))
    temp=temp.to(ureg(unit))
    scalar[0]=temp.magnitude
    scalar[1]=unit
    return scalar

def getInputAssociatedWithCBU(syn,cbu_iri,client):
    """Reactant species of the synthesis that is used as the given CBU, returns False if not found."""
    cbu = ontomops.ChemicalBuildingUnit.pull_from_kg(cbu_iri,client,0)
    cbu_specs = list(cbu[0].isUsedAsChemical)
    for cbu_spec in cbu_specs:
        for input in syn.hasChemicalInput:
            spec = getSpecies(input)
            if cbu_spec == spec:
                if type(spec) is str:
                    species = ontosyn.Species.pull_from_kg(spec,client,0)
                    return species[0]
                else:
                    return spec 
    return False


def compareBindingSites(L0,L2):
    """True if both CBUs have the same set of binding fragments (e.g. CO2)."""
    bs0_type = []
    bs2_type = []
    for bs in list(L0.hasBindingSite):
        bs0_type.append(list(bs.hasBindingFragment)[0])
    for bs in list(L2.hasBindingSite):
        bs2_type.append(list(bs.hasBindingFragment)[0])
    return set(bs0_type)==set(bs2_type)

def compareHeating(syn1,syn2):
    """True if the main heating temperatures of both syntheses differ by less than 10 % (of syn1's temperature)."""
    heat1 = getMainHeating(syn1)
    heat2 = getMainHeating(syn2)
    if abs(heat1[0][0]-heat2[0][0]) < 0.1*heat1[0][0]:
        return True
    else:
        return False

def compareSolvents(syn1,syn2,client):
    """True if both syntheses use the same solvent in their Dissolve step."""
    S1 = getSolvent(syn1,client)
    S2 = getSolvent(syn2,client)
    if S1 == False or S2 == False:
        return False
    return S1==S2 

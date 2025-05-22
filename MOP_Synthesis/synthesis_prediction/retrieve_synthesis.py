import sys

import twa.data_model
import twa.data_model.base_ontology
import twa.kg_operations
sys.path.append('..')
import ontosyn
import credentials
import twa

ontosyn_client = twa.kg_operations.PySparqlClient(credentials.ONTOSYN_ENDPOINT, 'restricted')
ontospecies_client = twa.kg_operations.PySparqlClient(credentials.ONTOSPECIES_ENDPOINT, 'restricted')

synthesis_iris = ['https://www.theworldavatar.com/kg/OntoSyn/ChemicalSynthesis_96270260-1b57-43e5-80b1-a6b23bb6ceca']
syns = ontosyn.ChemicalSynthesis.pull_from_kg(iris=synthesis_iris,sparql_client=ontosyn_client,recursive_depth=-1)
    
def encode_to_utf(str):
    try:
        return str.encode('ISO-8859-1').decode('utf-8')
    except Exception as e:
        print(f"unable to encode {str}: {e}")
        return str


def getMaterial(material,name=''):
    thermoBehaviour=list(material.thermodynamicBehaviour)[0]
    subsystems=list(thermoBehaviour.isComposedOfSubsystem)

    matString="Material " + name + ": "
    compStrings = []
    for subsystem in subsystems:
        species = list(subsystem.representsOccurenceOf)[0]
        speciesLab = encode_to_utf(list(species.rdfs_label)[0])
        conc=list(subsystem.hasProperty)[0]
        amount = getValue(conc,"undefined amount")
        if ontospecies_client.check_if_triple_exist(species.instance_iri,None,None):
            compStrings.append(amount + " of " + speciesLab + " (exists in OntoSpecies)")
        else:
            compStrings.append(amount + " of " + speciesLab + " (NOT in OntoSpecies)")

    if len(subsystems)>1:
        for i in range(len(compStrings)):
            matString += "\n \t Component " + str(i) + ": " + compStrings[i]
    else:
        matString += compStrings[0]

    return(matString)

def getValue(meas,defaultString="unknown"):
    val = list(meas.hasValue)[0]
    numVal=list(val.hasNumericalValue)[0]
    if val.__class__ == ontosyn.Measure:
        unit=list(val.hasUnit)[0]
    else:
        unit=list(val.hasUnitOfMeasure)[0]
    unitLab=encode_to_utf(list(unit.rdfs_label)[0])
    if numVal==0.0 and unitLab=="N/A":
        amount = defaultString
    else:
        amount = str(numVal) + unitLab

    return amount

def getStep(step):
    order = list(step.hasOrder)[0]
    instr="Step " + str(order) + ": "
    match step.__class__:
        case ontosyn.Add:
            addedChemical=list(step.hasAddedChemicalInput)[0]
            instr+="Add " + getMaterial(list(addedChemical.referencesMaterial)[0])
            instr+="\n"
            if list(step.isLayered)[0]:
                instr+=" in a layered fashion "
            if list(step.isStirred)[0]:
                instr+="under stirring "
            targetPh = list(step.hasTargetPh)[0]
            if targetPh != -1:
                instr+="while target pH is " + str(targetPh)
        case ontosyn.Separate:
            separationSolvent = list(step.hasSeparationSolvent)[0]
            sepSolvMat = getMaterial(list(separationSolvent.referencesMaterial)[0])
            instr+="Separate with " + sepSolvMat
            sepType = list(step.isSeparationType)[0]
            instr += "via " + list(sepType.rdfs_label)[0]
        case ontosyn.Dissolve:
            solvent = list(step.hasDissolveSolvent)[0]
            solvMat = getMaterial(list(solvent.referencesMaterial)[0])
            instr += "Dissolve in " + solvMat
        case ontosyn.Transfer:
            amount = getValue(list(step.hasTransferedAmount)[0])
            newVessel = list(step.isTransferedTo)[0]
            newVesselLab = list(newVessel.rdfs_label)[0]
            newVesselType = list(newVessel.hasVesselType)[0]
            newVesselTypeLab = list(newVesselType.rdfs_label)[0]
            instr += "Transfer " + amount + " to " + newVesselLab + " (" + newVesselTypeLab +")"
            if list(step.isLayered)[0]:
                instr+=" in a layered fashion "
        case ontosyn.Sonicate:
            instr+="Sonicate"
        case ontosyn.Crystallize:
            instr +="Crystallize"
        case ontosyn.Stir:
            if list(step.isWait)[0]:
                instr+="Wait"
            else:
                temp = list(step.hasStirringTemperature)[0]
                tempVal = getValue(temp, "unknown temperature")
                instr+="Stir at " + tempVal
        case ontosyn.HeatChill:
            temp = list(step.hasTargetTemperature)[0]
            tempVal = getValue(temp, "unknown temperature")
            tempRate = list(step.hasTemperatureRate)[0]
            tempRateVal = getValue(tempRate, "undefined rate")
            instr+="Heat or Chill to " + tempVal + " at " + tempRateVal
            if list(step.hasVacuum)[0]:
                instr+="\n under vacuum"
            if list(step.isSealed)[0]:
                instr+="\n while sealed"
        case ontosyn.Filter:
            solvent = list(step.hasWashingSolvent)[0]
            if len(solvent.rdfs_label) > 0 and list(solvent.rdfs_label)[0] == "N/A":
                instr+= "Filter "
                if list(step.isVacuumFiltration)[0]:
                    instr+= "under vacuum"
            else:
                solventMat = getMaterial(list(solvent.referencesMaterial)[0])
                instr+= "Wash with " + solventMat
            
            rep = list(step.isRepeated)[0]
            instr+="\n " + str(rep) + " times"
        case ontosyn.Dry:
            pressure=list(step.hasDryingPressure)[0]
            pVal=getValue(pressure,"undefined pressure")
            temperature=list(step.hasDryingTemperature)[0]
            tVal=getValue(temperature,"undefined temperature")
            instr+="Dry under " + pVal + " at " + tVal
        case ontosyn.Evaporate:
            removedChem = list(step.removesSpecies)[0]
            instr += "Evaporate "
            if len(removedChem.rdfs_label) > 0 and list(removedChem.rdfs_label)[0] == "N/A":
                instr+=getMaterial(list(removedChem.referencesMaterial)[0])
            pressure=list(step.hasEvaporationPressure)[0]
            pVal=getValue(pressure,"undefined pressure")
            temperature=list(step.hasEvaporationTemperature)[0]
            tVal=getValue(temperature,"undefined temperature")
            instr+="\n under " + pVal + " at " + tVal
            if list(step.hasRotaryEvaporator)[0]:
                instr+="\n with rotary evaporator"

    vessel = list(step.hasVessel)[0]
    vesselLab = list(vessel.rdfs_label)[0]
    vesselType = list(vessel.hasVesselType)[0]
    vesselTypeLab = list(vesselType.rdfs_label)[0]
    instr+="\n in " + vesselLab + " (" + vesselTypeLab +")"

    vesselEnv = list(step.hasVesselEnvironment)[0]
    vesselEnvLab = list(vesselEnv.rdfs_label)[0]
    if vesselEnvLab != "N/A":
        instr+="\n under " + vesselEnvLab

    if step.__class__ != ontosyn.Filter:
        stepDur = list(step.hasStepDuration)[0]
        stepDurVal = getValue(stepDur,"undefined duration")
        instr+="\n for " + stepDurVal
    
    comment = list(step.rdfs_comment)[0]
    if comment != "" and comment != "N/A":
        instr+="\n comment: " + comment

    return instr


def getSynthesis(synthesis):
    MOP = "a"
    query = "SELECT ?chemOut WHERE { ?trans <" + ontosyn.IsDescribedBy.predicate_iri + "> <" + synthesis.instance_iri + "> ; <" + ontosyn.HasChemicalOutput.predicate_iri + "> ?chemOut . }"
    chemOutResp = ontosyn_client.perform_query(query)
    chemOut = chemOutResp[0]['chemOut']
    chemOutKg=ontosyn.ChemicalOutput.pull_from_kg(chemOut,ontosyn_client,recursive_depth=-1)
    chemicalOutput=list(chemOutKg)[0]
    MOP = list(chemicalOutput.isRepresentedBy)[0]
    MOPFormula = list(MOP.hasMOPFormula)[0]
    print("== Synthesis of " + MOPFormula + "==")
    
    doc=list(synthesis.retrievedFrom)[0]
    doi=list(doc.doi)[0]
    print("Procedure retrieved from " + doi)
    print("")
    print("--- Chemical Inputs ---")
    chemicalInputs=list(synthesis.hasChemicalInput)
    for i, chemicalInput in enumerate(chemicalInputs):
        material = list(chemicalInput.referencesMaterial)[0]
        print(getMaterial(material, str(i+1)))

    print("")
    print("--- Procedure Steps ---")
    steps = list(synthesis.hasSynthesisStep)
    steps.sort(key=lambda step: list(step.hasOrder)[0])
    for step in steps:
        print(getStep(step))

    print("")
    print("--- Measurements ---")
    synYield = list(synthesis.hasYield)[0]
    yieldVal = getValue(synYield,"unknown")
    print("\n Yield: " + yieldVal) 



for syn in syns:
    getSynthesis(syn)

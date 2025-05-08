import credentials

PREFIX_ONTOMOPS = "PREFIX mop: <https://www.theworldavatar.com/kg/ontomops/>"
PREFIX_ONTOSPECIES = "PREFIX spec: <http://www.theworldavatar.com/ontology/ontospecies/OntoSpecies.owl#>"
PREFIX_ONTOSYN = "PREFIX syn: <https://www.theworldavatar.com/kg/OntoSyn/>"
PREFIX_RDFS = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"
PREFIX_RDF = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>"
PREFIX_SKOS = "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>"
PREFIX_OM = "PREFIX om: <http://www.ontology-of-units-of-measure.org/resource/om-2/>"
PREFIX_BIBO = "PREFIX bibo: <http://purl.org/ontology/bibo/>"

MATERIAL_TO_SPECIES_PRED = "<http://www.theworldavatar.com/ontology/ontocape/material/material.owl#thermodynamicBehaviour>/<http://www.theworldavatar.com/ontology/ontocape/upper_level/system.owl#isComposedOfSubsystem>/<http://www.theworldavatar.com/ontology/ontocape/material/phase_system/phase_system.owl#representsOccurenceOf>"

PAPER1_DOI = "10.1021/jacs.2c03402"
PAPER2_DOI = "Placeholder DOI for TWA OGM"

def construct(mop0,solvent_via_os=False,criteria=False):

        if solvent_via_os:
                solvent0 = f"""
                OPTIONAL {{
                        ?chemSyn_0 syn:hasSynthesisStep ?addedStep_0 .
                        ?addedStep_0 rdf:type syn:Add ;
                                syn:hasAddedChemicalInput/syn:referencesMaterial/{MATERIAL_TO_SPECIES_PRED} ?solventCandidate_0 .
                        ?solventCandidate_0 rdfs:label ?solventLabel_0 .
              
                        SERVICE <{credentials.ONTOSPECIES_ENDPOINT}> {{
                                ?solventCandidate_0 spec:hasUse ?use0	.
                                ?use0 rdfs:label ?useLabel0 .
                                FILTER regex(lcase(str(?useLabel0)), "solvent") .
                        }}
                }}
                """

                solvent2 = f"""
                OPTIONAL {{
                        ?chemSyn_2 syn:hasSynthesisStep ?addedStep_2 .
                        ?addedStep_2 rdf:type syn:Add ;
                                syn:hasAddedChemicalInput/syn:referencesMaterial/{MATERIAL_TO_SPECIES_PRED} ?solventCandidate_2 .
                        ?solventCandidate_2 rdfs:label ?solventLabel_2 .
              
                        SERVICE <{credentials.ONTOSPECIES_ENDPOINT}> {{
                                ?solventCandidate_2 spec:hasUse ?use2	.
                                ?use2 rdfs:label ?useLabel2 .
                                FILTER regex(lcase(str(?useLabel2)), "solvent") .
                        }}
                }}
                """

                solvent3 = f"""
                OPTIONAL {{
                        ?chemSyn_3 syn:hasSynthesisStep ?addedStep_3 .
                        ?addedStep_3 rdf:type syn:Add ;
                                syn:hasAddedChemicalInput/syn:referencesMaterial/{MATERIAL_TO_SPECIES_PRED} ?solventCandidate_3 .
                        ?solventCandidate_3 rdfs:label ?solventLabel_3 .
              
                        SERVICE <{credentials.ONTOSPECIES_ENDPOINT}> {{
                                ?solventCandidate_3 spec:hasUse ?use3	.
                                ?use3 rdfs:label ?useLabel3 .
                                FILTER regex(lcase(str(?useLabel3)), "solvent") .
                        }}
                }}
                """
        else:
                solvent0 = f"""
                OPTIONAL {{
                        ?chemSyn_0 syn:hasSynthesisStep ?dissolveStep_0 .
                        ?dissolveStep_0 rdf:type syn:Dissolve ;
                                        syn:hasSolventDissolve/syn:referencesMaterial/{MATERIAL_TO_SPECIES_PRED} ?solvent_0 .
                        ?solvent_0 rdfs:label ?solventLabel_0 .
                }}
                """

                solvent2 = f"""
                OPTIONAL {{
                        ?chemSyn_2 syn:hasSynthesisStep ?dissolveStep_2 .
                        ?dissolveStep_2 rdf:type syn:Dissolve ;
                                        syn:hasSolventDissolve/syn:referencesMaterial/{MATERIAL_TO_SPECIES_PRED} ?solvent_2 .
                        ?solvent_2 rdfs:label ?solventLabel_2 .
                }}
                """

                solvent3 = f"""
                OPTIONAL {{
                        ?chemSyn_3 syn:hasSynthesisStep ?dissolveStep_3 .
                        ?dissolveStep_3 rdf:type syn:Dissolve ;
                                        syn:hasSolventDissolve/syn:referencesMaterial/{MATERIAL_TO_SPECIES_PRED} ?solvent_3 .
                        ?solvent_3 rdfs:label ?solventLabel_3 .
                }}
                """

        query = f"""
        {PREFIX_ONTOMOPS}
        {PREFIX_ONTOSPECIES}
        {PREFIX_ONTOSYN}
        {PREFIX_RDF}
        {PREFIX_RDFS}
        {PREFIX_SKOS}
        {PREFIX_OM}
        {PREFIX_BIBO}

        SELECT ?MOPLabel_0 ?organicLigandLabel_0 ?DOI_0 (GROUP_CONCAT(DISTINCT STR(?solventLabel_0); separator=", ") AS ?solventLabels_0) ?AMLabel_0 (GROUP_CONCAT(DISTINCT CONCAT(STR(?siteCBUCoord_0), "-", STR(?siteCBUFrag_0)); separator=", ") AS ?sitesCBU_0) (GROUP_CONCAT(DISTINCT CONCAT(STR(?stepTypeLab_0), ": ", STR(?tempNumVal_0), " ", STR(?tempUnitLabel_0), " for ", STR(?durNumVal_0), " ", STR(?durUnitLabel_0)); separator=", ") AS ?temperatureLabel_0)
                ?MOP_1 ?MOPLabel_1 ?organicCBULabel_1  ?organicLigandLabel_1 ?DOI_1 ?AMLabel_1 (GROUP_CONCAT(DISTINCT CONCAT(STR(?siteCBUCoord_1), "-", STR(?siteCBUFrag_1)); separator=", ") AS ?sitesCBU_1)
                ?MOPLabel_2 ?metalCBULabel_2 ?DOI_2 (GROUP_CONCAT(DISTINCT ?solventLabel_2; separator=", ") AS ?solventLabels_2) ?AMLabel_2 (GROUP_CONCAT(DISTINCT CONCAT(STR(?stepTypeLab_2), ": ", STR(?tempNumVal_2), " ", STR(?tempUnitLabel_2), " for ", STR(?durNumVal_2), " ", STR(?durUnitLabel_2)); separator=", ") AS ?temperatureLabel_2)
                ?MOPLabel_3 ?DOI_3 (GROUP_CONCAT(DISTINCT ?solventLabel_3; separator=", ") AS ?solventLabels_3) ?AMLabel_3 (GROUP_CONCAT(DISTINCT CONCAT(STR(?stepTypeLab_3), ": ", STR(?tempNumVal_3), " ", STR(?tempUnitLabel_3), " for ", STR(?durNumVal_3), " ", STR(?durUnitLabel_3)); separator=", ") AS ?temperatureLabel_3)
                
        WHERE {{
                ?MOP_0 mop:hasMOPFormula ?MOPLabel_0 ; 
                        mop:hasAssemblyModel ?AM_0 ;
                        mop:hasChemicalBuildingUnit ?metalCBU_0 ;
                        mop:hasChemicalBuildingUnit ?organicCBU_0 ;
                        mop:hasProvenance/mop:hasReferenceDOI ?DOI_0 .
                ?metalCBU_0 mop:hasBindingSite/rdf:type mop:MetalSite .
                ?organicCBU_0 mop:hasBindingSite ?siteCBU_0 .
                ?siteCBU_0 rdf:type mop:OrganicSite ;
                        mop:hasOuterCoordinationNumber ?siteCBUCoord_0 ;
                        mop:hasBindingFragment ?siteCBUFrag_0 .
                ?AM_0 rdfs:label ?AMLabel_0 .
                FILTER(?MOP_0 = {mop0})
  
                ?MOP_1 a mop:MetalOrganicPolyhedron ;
                        mop:hasChemicalBuildingUnit ?metalCBU_0 ;
                        mop:hasChemicalBuildingUnit ?organicCBU_1 ;
                        mop:hasAssemblyModel ?AM_1 ;
                        mop:hasMOPFormula ?MOPLabel_1 ;
                        mop:hasProvenance/mop:hasReferenceDOI ?DOI_1 .

                VALUES ?DOI_1 {{ "{PAPER1_DOI}" "{PAPER2_DOI}" }} .

                ?organicCBU_1 mop:hasCBUFormula ?organicCBULabel_1 ;
                                mop:hasBindingSite ?siteCBU_1 .
                ?siteCBU_1 rdf:type mop:OrganicSite ;
                        mop:hasOuterCoordinationNumber ?siteCBUCoord_1 ;
                        mop:hasBindingFragment ?siteCBUFrag_1 .
                ?AM_1 rdfs:label ?AMLabel_1 .
                FILTER (?organicCBU_1 != ?organicCBU_0)
        
                ?MOP_2 a mop:MetalOrganicPolyhedron ;
                        mop:hasChemicalBuildingUnit ?organicCBU_1 ;
                        mop:hasChemicalBuildingUnit ?metalCBU_2 ;
                        mop:hasAssemblyModel ?AM_2 ;
                        mop:hasProvenance/mop:hasReferenceDOI ?DOI_2 ;
                        mop:hasMOPFormula ?MOPLabel_2 .
                ?metalCBU_2 mop:hasCBUFormula ?metalCBULabel_2 ;
                        mop:hasBindingSite/rdf:type mop:MetalSite .
                ?AM_2 rdfs:label ?AMLabel_2 .

                FILTER (?DOI_2 NOT IN ("{PAPER1_DOI}", "{PAPER2_DOI}"))
                FILTER (?metalCBU_2 != ?metalCBU_0 )

                ?MOP_3 a mop:MetalOrganicPolyhedron ;
                        mop:hasChemicalBuildingUnit ?metalCBU_2 ;
                        mop:hasChemicalBuildingUnit ?organicCBU_0 ;
                        mop:hasAssemblyModel ?AM_3 ;
                        mop:hasProvenance/mop:hasReferenceDOI ?DOI_3 ;
                        mop:hasMOPFormula ?MOPLabel_3 .
                ?AM_3 rdfs:label ?AMLabel_3 .
                FILTER (?DOI_3 NOT IN ("{PAPER1_DOI}", "{PAPER2_DOI}"))

  
                SERVICE <{credentials.ONTOSYN_ENDPOINT}> {{
                        ?chemOut_0 syn:isRepresentedBy ?MOP_0 .
                        ?chemTrans_0 syn:hasChemicalOutput ?chemOut_0 ;
                                        syn:isDescribedBy ?chemSyn_0 .
                        ?chemSyn_0 a syn:ChemicalSynthesis ;
                                syn:hasSynthesisStep ?heatingStep_0 .

                        ?heatingStep_0 syn:hasStepDuration ?dur_0 ;
                                rdf:type/rdfs:label ?stepTypeLab_0 .
                        ?dur_0 om:hasValue ?durVal_0 .
                        ?durVal_0 om:hasNumericalValue ?durNumVal_0 ;
                                om:hasUnit/rdfs:label ?durUnitLabel_0 .
                        ?heatingStep_0 ?hasTemperature ?temp_0 .
                        VALUES ?hasTemperature {{ syn:hasTargetTemperature syn:hasDryingTemperature syn:hasStirringTemperature syn:hasEvaporationTemperature }}
                                ?temp_0 om:hasValue ?tempVal_0 .
                        ?tempVal_0 om:hasNumericalValue ?tempNumVal_0 ;
                                om:hasUnit/rdfs:label ?tempUnitLabel_0 .
                        FILTER (?tempUnitLabel_0 != "N/A")
                        FILTER (?durUnitLabel_0 != "N/A")

                        {solvent0}
        
                        OPTIONAL {{
                                ?chemOut_2 syn:isRepresentedBy ?MOP_2 .
                                ?chemTrans_2 syn:hasChemicalOutput ?chemOut_2 ;
                                                syn:isDescribedBy ?chemSyn_2 .
                                ?chemSyn_2 a syn:ChemicalSynthesis ;
                                                syn:hasSynthesisStep ?heatingStep_2 .
                                ?heatingStep_2 syn:hasStepDuration ?dur_2 ;
                                        rdf:type/rdfs:label ?stepTypeLab_2 .
                                ?dur_2 om:hasValue ?durVal_2 .
                                ?durVal_2 om:hasNumericalValue ?durNumVal_2 ;
                                                om:hasUnit/rdfs:label ?durUnitLabel_2 .
                                ?heatingStep_2 ?hasTemperature ?temp_2 .
                                VALUES ?hasTemperature {{ syn:hasTargetTemperature syn:hasDryingTemperature syn:hasStirringTemperature syn:hasEvaporationTemperature }}
                                ?temp_2 om:hasValue ?tempVal_2 .
                                ?tempVal_2 om:hasNumericalValue ?tempNumVal_2 ;
                                                om:hasUnit/rdfs:label ?tempUnitLabel_2 .
                                
                                FILTER (?tempUnitLabel_2 != "N/A")
                                FILTER (?durUnitLabel_2 != "N/A")
                
                                {solvent2}
                        }}
                                        
                        OPTIONAL {{
                                ?organicCBU_0 mop:isUsedAsChemical ?organicLigand_0 .
                                ?chemSyn_0 syn:hasChemicalInput/syn:referencesMaterial/{MATERIAL_TO_SPECIES_PRED} ?organicLigand_0 .
                                ?organicLigand_0 rdfs:label ?organicLigandLabel_0 .
                        }}
                        
                        OPTIONAL {{
                                ?organicCBU_1 mop:isUsedAsChemical ?organicLigand_1 .
                                ?chemSyn_2 syn:hasChemicalInput/syn:referencesMaterial/{MATERIAL_TO_SPECIES_PRED} ?organicLigand_1 .
                                ?organicLigand_1 rdfs:label ?organicLigandLabel_1 .
                        }}
        

                        OPTIONAL {{
                                ?chemOut_3 syn:isRepresentedBy ?MOP_3 .
                                ?chemTrans_3 syn:hasChemicalOutput ?chemOut_3 ;
                                                syn:isDescribedBy ?chemSyn_3 .
                                ?chemSyn_3 a syn:ChemicalSynthesis ;
                                                syn:hasSynthesisStep ?heatingStep_3 .
                                ?heatingStep_3 syn:hasStepDuration ?dur_3 ;
                                        rdf:type/rdfs:label ?stepTypeLab_3 .
                                ?dur_3 om:hasValue ?durVal_3 .
                                ?durVal_3 om:hasNumericalValue ?durNumVal_3 ;
                                                om:hasUnit/rdfs:label ?durUnitLabel_3 .
                                ?heatingStep_3 ?hasTemperature ?temp_3 .
                                VALUES ?hasTemperature {{ syn:hasTargetTemperature syn:hasDryingTemperature syn:hasStirringTemperature syn:hasEvaporationTemperature }}
                                ?temp_3 om:hasValue ?tempVal_3 .
                                ?tempVal_3 om:hasNumericalValue ?tempNumVal_3 ;
                                        om:hasUnit/rdfs:label ?tempUnitLabel_3 .
                                FILTER (?tempUnitLabel_3 != "N/A")
                                FILTER (?durUnitLabel_3 != "N/A")
                                
                                {solvent3}
                        }}
                }}
        }}
         
        GROUP BY ?MOP_0 ?MOPLabel_0 ?organicLigandLabel_0 ?solventCandidate_0 ?DOI_0 ?AMLabel_0 
                ?MOP_1 ?MOPLabel_1 ?DOI_1 ?organicCBULabel_1 ?AMLabel_1 ?organicLigandLabel_1 
                ?MOPLabel_2 ?metalCBULabel_2 ?DOI_2 ?AMLabel_2 
                ?MOPLabel_3 ?DOI_3 ?AMLabel_3 
        ORDER BY ?MOPLabel_1 ?MOPLabel_2 ?MOPLabel_3
        """

        return query
PREFIX_ONTOMOPS = "PREFIX mop: <https://www.theworldavatar.com/kg/ontomops/>"
PREFIX_ONTOSPECIES = "PREFIX spec: <http://www.theworldavatar.com/ontology/ontospecies/OntoSpecies.owl#>"
PREFIX_ONTOSYN = "PREFIX syn: <https://www.theworldavatar.com/kg/OntoSyn/>"
PREFIX_RDFS = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"
PREFIX_RDF = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>"
PREFIX_SKOS = "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>"
PREFIX_OM = "PREFIX om: <http://www.ontology-of-units-of-measure.org/resource/om-2/>"
PREFIX_BIBO = "PREFIX bibo: <http://purl.org/ontology/bibo/>"
PREFIX_UNITSOFMEASURE = "PREFIX om: <http://www.ontology-of-units-of-measure.org/resource/om-2/>"

MATERIAL_TO_SPECIES_PRED = "<http://www.theworldavatar.com/ontology/ontocape/material/material.owl#thermodynamicBehaviour>/<http://www.theworldavatar.com/ontology/ontocape/upper_level/system.owl#isComposedOfSubsystem>/<http://www.theworldavatar.com/ontology/ontocape/material/phase_system/phase_system.owl#representsOccurenceOf>"

PAPER1_DOI = "10.1021/jacs.2c03402"
PAPER2_DOI = "Placeholder DOI for TWA OGM"

def getSynthesis(mop_list):
        mop_string = "{" + " ".join(f'"{item}"' for item in mop_list) + "}"
        query = f"""
        {PREFIX_ONTOSYN}
        {PREFIX_ONTOMOPS}

        SELECT DISTINCT ?chemSyn
        WHERE {{
        ?chemOut syn:isRepresentedBy/mop:hasMOPFormula ?mopF .
        VALUES ?mopF { mop_string }
        ?chemTrans syn:hasChemicalOutput ?chemOut ;
                        syn:isDescribedBy ?chemSyn .
        ?chemSyn a syn:ChemicalSynthesis ;
                syn:hasSynthesisStep ?step .
        }}
        """

        return query

def getMOPs(known=False,charge=None,shape=None,cbu=None,gbu=None):
    known_query = ""
    charge_query = ""
    shape_query = ""
    cbu_query = ""
    gbu_query = ""
    
    if known:
        known_query = f"""FILTER (?doi NOT IN ("{PAPER1_DOI}", "{PAPER2_DOI}"))"""

    if charge is not None:
        charge_query = f"""
            ?charge om:hasValue/om:hasNumericalValue ?chargeNumVal .
            FILTER (?chargeNumVal = 0.0)
        """
    
    if shape is not None:
        shape_query = f"""FILTER(?shapeSymb = "{shape}") """

    if cbu is not None:
        cbu_query = f"""?MOP mop:hasChemicalBuildingUnit/mop:hasCBUFormula "[{cbu}]" . """

    if gbu is not None:
        gbu_query = f"""?am mop:hasGenericBuildingUnit/mop:hasGBUType/rdfs:label "{gbu}" . """

    query = f"""
    {PREFIX_ONTOMOPS}
    {PREFIX_ONTOSPECIES}
    {PREFIX_UNITSOFMEASURE}
    {PREFIX_RDFS}
    SELECT ?MOPFormula (CONCAT(STR(?chargeNumVal), " ", ?chargeUnitLab) as ?chargeStr) ?shapeSymb ?geoFile ?doi WHERE {{
        ?MOP a mop:MetalOrganicPolyhedron ;
            mop:hasProvenance ?prov ;
            mop:hasAssemblyModel ?am ;
            spec:hasGeometry ?geo ;
            spec:hasCharge ?charge .
        
        ?MOP mop:hasMOPFormula ?MOPFormula .
        ?am mop:hasPolyhedralShape/mop:hasSymbol ?shapeSymb .
        ?charge om:hasValue ?chargeVal .
        ?chargeVal om:hasNumericalValue ?chargeNumVal ;
                    om:hasUnit/rdfs:label ?chargeUnitLab .
        ?geo spec:hasGeometryFile ?geoFile .
        ?prov mop:hasReferenceDOI ?doi .

        {known_query}
        {charge_query}
        {shape_query}
        {cbu_query}
        {gbu_query}
    }}
    """

    return query

def getIRPeaks(mop_iri):
    query = f"""
    {PREFIX_ONTOMOPS}
    {PREFIX_ONTOSPECIES}
    {PREFIX_ONTOSYN}
    {PREFIX_RDFS}
    SELECT ?peakLocation ?peakStrength WHERE {{
        ?chemOut syn:isRepresentedBy {mop_iri} ;
                spec:hasFourierTransformSpectrum/spec:hasSpectraGraph ?spectrum .
        ?spectrum spec:hasPeak ?peak .
        ?peak spec:hasX1 ?peakLocation ;
                rdfs:comment ?peakStrength .
    }}
    """

    return query

def getCandidateTuples(mop0_label,assembled_mop_dois,novel):

        assembled_mops = str(assembled_mop_dois)[1:-1]

        if novel is True:
                mop_x_filter = f"""FILTER (?DOI_x IN ('{PAPER1_DOI}'))"""
        else:
                mop_x_filter = f"""FILTER (?DOI_x NOT IN ('{PAPER1_DOI}',{PAPER2_DOI}))"""

        query = f"""
        {PREFIX_ONTOMOPS}
        {PREFIX_RDF}

        SELECT DISTINCT ?MOP_x ?MOP_1 ?MOP_2 ?metalCBU_0 ?metalCBU_2 ?organicCBU_0 ?organicCBU_x
        WHERE {{
        ?MOP_0 mop:hasMOPFormula "{mop0_label}" ;
                mop:hasChemicalBuildingUnit ?metalCBU_0 ;
                mop:hasChemicalBuildingUnit ?organicCBU_0 .
        ?metalCBU_0 mop:hasBindingSite/rdf:type mop:MetalSite .
        ?organicCBU_0 mop:hasBindingSite/rdf:type mop:OrganicSite .
        
        ?MOP_x a mop:MetalOrganicPolyhedron ;
                mop:hasChemicalBuildingUnit ?metalCBU_0 ;
                mop:hasChemicalBuildingUnit ?organicCBU_x ;
                mop:hasProvenance/mop:hasReferenceDOI ?DOI_x ;
                mop:hasMOPFormula ?MOPLabel_x .

        {mop_x_filter}
        
        ?organicCBU_x mop:hasBindingSite/rdf:type mop:OrganicSite .
        FILTER (?organicCBU_x != ?organicCBU_0)

        ?MOP_2 a mop:MetalOrganicPolyhedron ;
                mop:hasChemicalBuildingUnit ?organicCBU_x ;
                mop:hasChemicalBuildingUnit ?metalCBU_2 ;
                mop:hasProvenance/mop:hasReferenceDOI ?DOI_2 ;
                mop:hasMOPFormula ?MOPLabel_2 .
        ?metalCBU_2 mop:hasBindingSite/rdf:type mop:MetalSite .
        FILTER (?metalCBU_2 != ?metalCBU_0 )
        FILTER (?DOI_2 NOT IN ({assembled_mops}))

        ?MOP_1 a mop:MetalOrganicPolyhedron ;
                mop:hasChemicalBuildingUnit ?metalCBU_2 ;
                mop:hasChemicalBuildingUnit ?organicCBU_0 ;
                mop:hasProvenance/mop:hasReferenceDOI ?DOI_1 ;
                mop:hasMOPFormula ?MOPLabel_1 .
        FILTER (?DOI_1 NOT IN ({assembled_mops}))

        }}
        """

        return query

def getMOPIRI(mop_list):
        mop_string = "{" + " ".join(f'"{item}"' for item in mop_list) + "}"
        query = f"""
        {PREFIX_ONTOMOPS}

        SELECT DISTINCT ?mop
        WHERE {{
        ?mop mop:hasMOPFormula ?mopF .
        VALUES ?mopF { mop_string }
        }}
        """
        return query
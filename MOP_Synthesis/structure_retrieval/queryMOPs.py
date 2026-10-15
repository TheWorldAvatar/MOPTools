PREFIX_ONTOMOPS = "PREFIX mop: <https://www.theworldavatar.com/kg/ontomops/>"
PREFIX_ONTOSPECIES = "PREFIX spec: <http://www.theworldavatar.com/ontology/ontospecies/OntoSpecies.owl#>"
PREFIX_UNITSOFMEASURE = "PREFIX om: <http://www.ontology-of-units-of-measure.org/resource/om-2/>"
PREFIX_RDFS = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"
PREFIX_ONTOSYN = "PREFIX syn: <https://www.theworldavatar.com/kg/OntoSyn/>"


JACS_PAPER_DOI  = "10.1021/jacs.2c03402"
OGM_PAPER_DOI = "10.1039/D5DD00069F"

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

def construct(known=False,charge=None,shape=None,cbu=None,gbu=None):
    known_query = ""
    charge_query = ""
    shape_query = ""
    cbu_query = ""
    gbu_query = ""
    
    if known:
        known_query = f"""FILTER (?doi NOT IN ("{JACS_PAPER_DOI}", "{OGM_PAPER_DOI}"))"""

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
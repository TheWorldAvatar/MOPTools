from twa.kg_operations import PySparqlClient
import pandas as pd
import queryMOPs
import credentials

Zr_H2BDC_MOP_IRI = "mop:MetalOrganicPolyhedra_e67c729f-f153-4742-9fee-e00c623d151b"
Zr_H3BTC_MOP_IRI = "mop:MetalOrganicPolyhedra_1d52f054-9421-4aac-bd29-76d8a9519ccb"
Zr_H2BPDC_MOP_IRI = "mop:MetalOrganicPolyhedra_3d71c19a-ab54-4993-8c94-267dcfe41792"


sparql_client = PySparqlClient(credentials.ONTOMOPS_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)
mops_query = queryMOPs.construct(Zr_H2BPDC_MOP_IRI)
predictable_mops = sparql_client.perform_query(mops_query)

for mop in predictable_mops:
    print(mop['MOPLabel_1'], end='; Crit1: ')

    if mop['AMLabel_3'] == mop['AMLabel_0']:
        c1 = 'YES (' + mop['AMLabel_3'] + '), '
    else:
        c1 = 'NO (' + mop['AMLabel_1'] + ' vs. ' + mop['AMLabel_3'] + ')'

    print(c1,end='; Crit2: ')

    if mop['AMLabel_2'] == mop['AMLabel_1']:
        c2 = 'YES (' + mop['AMLabel_2'] + '), '
    else:
        c2 = 'NO (' + mop['AMLabel_2'] + ' vs. ' + mop['AMLabel_1'] + ')'

    print(c2,end='; Crit3: ')
    print('')
    ## TODO add criteria
    ## TODO add prediction algorithm
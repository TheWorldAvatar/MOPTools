import os
import sys
parent = os.path.abspath('')
sys.path.append(parent)
sys.path.append('..')
from twa.kg_operations import PySparqlClient
import pandas as pd
import matplotlib.pyplot as plt
import queryMOPs
import credentials
import os
import numpy as np

Zr_H2BDC_MOP_IRI = "mop:MetalOrganicPolyhedra_e67c729f-f153-4742-9fee-e00c623d151b"
Zr_H3BTC_MOP_IRI = "mop:MetalOrganicPolyhedra_1d52f054-9421-4aac-bd29-76d8a9519ccb"
Zr_H2BPDC_MOP_IRI = "mop:MetalOrganicPolyhedra_3d71c19a-ab54-4993-8c94-267dcfe41792"

DMA_IR_REF = "DMA-Transmittance.0.dpt"
DMF_IR_REF = "DMF-Transmittance.0.dpt"
DIW_IR_REF = "DIW-Transmittance.0.dpt"
Zr_IR_REF = "zironocene dichloride.0.dpt"
H2BDC_IR_REF = "Terephthalic-acid_v3.dpt"
H3BTC_IR_REF = "H3BTC-ligand.0.dpt"
H2BPDC__IR_REF = "44biphenyldicarboxylic-acid_v3.dpt"
H2PDC_IR_REF = "Pyrene27dicarboxylic-acid_v2.dpt"
H2BPyDC_IR_REF = "22bipyridine44dicarboxylic-acid.dpt"

exp_folder_path = "../IR-data"

#### SETTINGS TO CHECK EACH TIME! ###
file = "zrcl2cp2andh3btc.0.dpt"
sample_nr = 1
solvent_reference = DMF_IR_REF
ligand_reference = H3BTC_IR_REF
MOP_peaks = Zr_H3BTC_MOP_IRI
###
data = pd.read_csv(os.path.join(exp_folder_path,file), delimiter='\t', header=None, names=['wavenumber', 'intensity'])
ref_metal = pd.read_csv(os.path.join(exp_folder_path,Zr_IR_REF), delimiter='\t', header=None, names=['wavenumber', 'intensity'])
ref_ligand = pd.read_csv(os.path.join(exp_folder_path,ligand_reference), delimiter='\t', header=None, names=['wavenumber', 'intensity'])
ref_solvent = pd.read_csv(os.path.join(exp_folder_path,solvent_reference), delimiter='\t', header=None, names=['wavenumber', 'intensity'])
ref_water = pd.read_csv(os.path.join(exp_folder_path,DIW_IR_REF), delimiter='\t', header=None, names=['wavenumber', 'intensity'])

sparql_client = PySparqlClient(credentials.ONTOSYN_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)
peaks = sparql_client.perform_query(queryMOPs.construct(MOP_peaks))
#print(peaks)

#plt.plot(ref_metal['wavenumber'], -np.log10(ref_metal['intensity']), color='tan', linewidth=1, label='Metal IR reference')
#plt.plot(ref_ligand['wavenumber'], -np.log10(ref_ligand['intensity']), color='grey', linewidth=1, label='Ligand IR reference')
plt.plot(ref_solvent['wavenumber'], -np.log10(ref_solvent['intensity']), color='skyblue', linewidth=1, label='Solvent IR reference')
plt.plot(ref_metal['wavenumber'], ref_metal['intensity'], color='tan', linewidth=1, label='Metal IR reference')
plt.plot(ref_ligand['wavenumber'], ref_ligand['intensity'], color='grey', linewidth=1, label='Ligand IR reference')
#plt.plot(ref_solvent['wavenumber'], ref_solvent['intensity'], color='skyblue', linewidth=1, label='Solvent IR reference')
plt.plot(data['wavenumber'], data['intensity'], color='green', linewidth=3, label='IR experiment')


min_i = min(data['intensity'])-0.5
max_i = max(data['intensity'])+0.5
verystrong = []
strong = []
medium = []

for peak in peaks:
    match peak['peakStrength']:
        case 'vs':
            verystrong.append(float(peak['peakLocation']))
        case 's':
            strong.append(float(peak['peakLocation']))
        case 'm':
            medium.append(float(peak['peakLocation']))


plt.vlines(x=verystrong, ymin=min_i, ymax=max_i, color='red', linestyle='--', linewidth=2, label='very strong expected peak')
plt.vlines(x=strong, ymin=min_i, ymax=max_i, color='red', linestyle='--', linewidth=1, label='strong expected peak')
plt.vlines(x=medium, ymin=min_i, ymax=max_i, color='red', linestyle=':', linewidth=1, label='medium expected peak')

# Add labels and title
plt.xlabel(r'Wavenumber [cm$^{-1}$]')
plt.xlim(500,2000)
plt.ylabel('Absorbance [-]')
plt.ylim(-0.05,0.7)
#plt.title('IR measurement - sample ' + str(sample_nr))
plt.legend(loc='upper center',ncol=2)

#plt.show()
# Show the plot
plt.show(block=False)
plt.savefig('sample_' + str(sample_nr) + '.png')
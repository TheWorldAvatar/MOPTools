# Plot a measured FTIR spectrum of a synthesised MOP against IR references of the involved metal precursor,
# ligand and solvent, and mark the MOP peaks expected from the literature (stored in OntoSyn).
import os
import sys
# make the shared modules in the repo root importable
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

# MOPs whose literature IR peaks are stored in the KG
Zr_H2BDC_MOP = "[Zr3O(OH)3(C5H5)3]4[(C6H4)(CO2)2]6"
Zr_H3BTC_MOP = "[Zr3O(OH)3(C5H5)3]4[(C6H3)(CO2)3]4"
Zr_H2BPDC_MOP = "[Zr3O(OH)3(C5H5)3]4[(C6H4)2(CO2)2]6"

# reference spectra files (tab-separated wavenumber / intensity) in exp_folder_path
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
MOP_peaks = Zr_H3BTC_MOP
###
# load the measured spectrum and the references
data = pd.read_csv(os.path.join(exp_folder_path,file), delimiter='\t', header=None, names=['wavenumber', 'intensity'])
ref_metal = pd.read_csv(os.path.join(exp_folder_path,Zr_IR_REF), delimiter='\t', header=None, names=['wavenumber', 'intensity'])
ref_ligand = pd.read_csv(os.path.join(exp_folder_path,ligand_reference), delimiter='\t', header=None, names=['wavenumber', 'intensity'])
ref_solvent = pd.read_csv(os.path.join(exp_folder_path,solvent_reference), delimiter='\t', header=None, names=['wavenumber', 'intensity'])
ref_water = pd.read_csv(os.path.join(exp_folder_path,DIW_IR_REF), delimiter='\t', header=None, names=['wavenumber', 'intensity'])

# expected MOP peaks from the KG
sparql_client = PySparqlClient(credentials.ONTOSYN_ENDPOINT, 'restricted', fs_url=credentials.FILE_SERVER, fs_user=credentials.FS_USER, fs_pwd=credentials.FS_PW)
peaks = sparql_client.perform_query(queryMOPs.getIRPeaks(MOP_peaks))
#print(peaks)

# plot spectra; -log10 converts transmittance to absorbance
#plt.plot(ref_metal['wavenumber'], -np.log10(ref_metal['intensity']), color='tan', linewidth=1, label='Metal IR reference')
#plt.plot(ref_ligand['wavenumber'], -np.log10(ref_ligand['intensity']), color='grey', linewidth=1, label='Ligand IR reference')
plt.plot(ref_solvent['wavenumber'], -np.log10(ref_solvent['intensity']), color='skyblue', linewidth=1, label='Solvent IR reference')
plt.plot(ref_metal['wavenumber'], ref_metal['intensity'], color='tan', linewidth=1, label='Metal IR reference')
plt.plot(ref_ligand['wavenumber'], ref_ligand['intensity'], color='grey', linewidth=1, label='Ligand IR reference')
#plt.plot(ref_solvent['wavenumber'], ref_solvent['intensity'], color='skyblue', linewidth=1, label='Solvent IR reference')
plt.plot(data['wavenumber'], data['intensity'], color='green', linewidth=3, label='IR experiment')


# sort the expected peaks by strength and draw them as vertical lines
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
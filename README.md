# Metal-Organic Polyhedra in TWA
This repository contains all code related to the analysis, design, and synthesis of metal-organic polyhedra (MOPs), a class of discrete reticular materials, within The World Avatar (TWA).

## Rational Design of MOPs
The folder "MOP_Discovery" contains all software agents and tools used for the rational design of novel MOP structures based on known MOPs, their building units, and assembly models. This work was published in the 
[Journal of the American Chemical Society](https://doi.org/10.1021/jacs.2c03402), where the described algorithms were used to generate over 1,500 novel MOP structures based on 151 known MOPs.

## MOP Assembly
The folder "MOPs_Assembler" contains all software to run the geometry assembler for newly suggested MOPs described in [preprint 329](https://como.ceb.cam.ac.uk/preprints/329/). This geometry assembler was used to generate geometries for the ~1500 novel MOPs suggested earlier, curated data for reproduction can be found in a [separate repository](https://github.com/cambridge-cares/CuratedMOPs).

## MOP Discovery and Synthesis with OGM
The folder "twa_mops" contains all code of MOPs-related applications used in [preprint 335](https://como.ceb.cam.ac.uk/preprints/335/) to illustrate the capabilities of the TWA Python package. The newly developed object-graph mapper (OGM) was used to simplify rational design and geometry assembly of novel MOPs, highlighted by the incorporation of additional structures and building units. The underlying codes of the TWA Python package can be found in a [separate repository](https://github.com/TheWorldAvatar/baselib/tree/main/python_wrapper).


## MOP Synthesis 
The folder "MOP_Literature_Extraction" contains all code and embedded LLM prompts used for an automated pipeline that extracts reported MOP synthesis descriptions from the literature. As described in [preprint 336](https://como.ceb.cam.ac.uk/preprints/336/), this pipeline was used to extract nearly 300 synthesis procedures related to the original 151 known MOPs and integrate within TWA for analysis and retrosynthetic efforts.
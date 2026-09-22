# Model provenance

## Chemical structure quality control

- Name: RDKit
- Version: 2025.03.6
- Official source: https://www.rdkit.org/
- Input: cached PubChem structure records for compounds 9, 10, 11, 13, 14 and 15
- Output: `results/tables/compound_structure_audit.csv`
- Evidence type: DATABASE for input structures; COMPUTED for RDKit normalization and descriptors
- Script: `analysis/preprocessing/structure_qc.py`
- Interpretation boundary: a successful parse confirms internal consistency, not experimental identity of a laboratory standard

## ADMETlab 3.0

- Status: BLOCKED until a raw export is supplied
- Intended endpoints: skin sensitization, Ames, cytotoxicity, hepatotoxicity, neurotoxicity, nephrotoxicity, carcinogenicity, respiratory toxicity and acute toxicity when available
- Input structures: only `structure_confirmed=yes`
- Raw output location: `data/raw/admetlab/`
- Evidence type: PREDICTED
- Downstream figures: toxicity consensus, probability and uncertainty plots

## ProTox 3.0

- Status: BLOCKED until a raw export is supplied
- Intended use: independent toxicity cross-check
- Raw output location: `data/raw/protox/`
- Evidence type: PREDICTED

## EPA CompTox

- Status: BLOCKED until an official API or batch export is supplied
- Intended endpoints: logKow, water solubility, BCF, Koc, persistence or biodegradation, vapor pressure, measured/predicted status and confidence
- Raw output location: `data/raw/comptox/`
- Evidence type: DATABASE or PREDICTED as marked by EPA

## EPA ECOSAR

- Status: BLOCKED until an ECOSAR or EPI Web Suite export is supplied
- Intended endpoints: fish acute/chronic, aquatic invertebrate and algae/aquatic plant toxicity
- Raw output location: `data/raw/ecosar/`
- Evidence type: PREDICTED unless the source explicitly identifies a measured value

## Source literature

- Zhang Z, Li W, Meng F, et al. Discover the maze-like network for glabridin biosynthesis. Nature Communications 17, 2215 (2026). https://doi.org/10.1038/s41467-026-68881-8
- Cached source data: `data/raw/literature/zhang_2026_source_data.xlsx`
- Use in this repository: pathway identifier and reaction-edge verification only; the source workbook remains unmodified


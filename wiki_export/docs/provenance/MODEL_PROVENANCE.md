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

- Status: COMPLETE for one official web batch run covering all six confirmed structures
- Result ID: `339e57a1a97c24b31790055148`
- Result URL: https://admetlab3.scbdd.com/server/result/339e57a1a97c24b31790055148
- Access date: 2026-09-22
- Model description: ADMETlab 3.0 DMPNN-based web prediction service
- Selected endpoints: skin sensitization, Ames, DILI, carcinogenicity, respiratory toxicity, human hepatotoxicity, neurotoxicity, nephrotoxicity, genotoxicity, hERG, logP, logS, BCF, Tetrahymena IGC50, Daphnia LC50 and fathead minnow LC50
- Input structures: only `structure_confirmed=yes`
- Raw output: `data/raw/admetlab/admetlab_predictions.csv`
- Run metadata: `data/raw/admetlab/run_metadata.json`
- Selected normalized table: `results/tables/admetlab_selected_predictions.csv`
- Evidence type: PREDICTED
- Script: `analysis/adapters/admetlab_api.py` for cache/download and `analysis/adapters/model_cache.py` for normalization
- Downstream figures: `toxicity_prediction_probability.svg`, `environmental_model_outputs.svg`, and `predicted_chemical_property_landscape.svg`
- Uncertainty: the official web CSV did not expose uncertainty values; no uncertainty plot is produced
- API note: the documented `/api/admet` endpoint returned HTTP 404 during this run, so the official web batch interface was used and its CSV was cached

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

# Model provenance

## Chemical structure quality control

- Name: RDKit
- Version: 2026.03.6
- Official source: https://www.rdkit.org/
- Input: cached PubChem structure records for compounds 9, 10, 11, 13, 14 and 15
- Output: `results/tables/compound_structure_audit.csv`
- Evidence type: DATABASE for input structures; COMPUTED for RDKit normalization and descriptors
- Script: `analysis/preprocessing/structure_qc.py`
- Interpretation boundary: a successful parse confirms internal consistency, not experimental identity of a laboratory standard

## ADMET-AI v2

- Status: COMPLETE for all six structure-confirmed compounds
- Official repository: https://github.com/swansonk14/admet_ai
- Package version: ADMET-AI 2.0.1
- Model framework: Chemprop 2.3.1, PyTorch 2.14.0, Lightning 2.6.6
- Access/run date: 2026-09-22
- Dataset: 41 TDC ADMET tasks bundled by the official package; task-level training size and reference AUROC/AUPRC or R2/MAE are retained in the processed table
- Reference database: packaged DrugBank-approved set, 2,845 molecules
- Input: canonical SMILES for compounds 9, 10, 11, 13, 14 and 15 after RDKit QC
- Method: official five-checkpoint classification ensemble and five-checkpoint regression ensemble; per-member predictions retained
- Raw output: `data/raw/admet_ai/admet_ai_predictions.csv`
- Ensemble output: `data/raw/admet_ai/ensemble_member_predictions.csv`
- Run metadata: `data/raw/admet_ai/run_metadata.json`
- Normalized output: `data/processed/admet_ai_predictions.csv`
- Script: `analysis/adapters/admet_ai_local.py`
- Generated figures: `admet_ai_endpoint_heatmap.svg`, `admet_ai_compound_profiles.svg`, `admet_ai_drugbank_reference.svg`, `admet_ai_compound_distance.svg`, `admet_ai_ensemble_uncertainty.svg`
- Evidence type: PREDICTED
- Uncertainty: between-member standard deviation for the five predictions belonging to each compound–task pair
- Applicability note: DrugBank percentiles and prediction-space PCA contextualize outputs but do not establish a formal chemical applicability domain or safety rank

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

- Status: BLOCKED; the official FAQ documents a rate-limited POST API, but its linked sample script returned HTTP 404 on 2026-09-22, and no supported authenticated endpoint/export was available
- Official site: https://tox.charite.de/protox3/
- Intended use: independent toxicity cross-check
- Raw output location: `data/raw/protox/`
- Evidence type: PREDICTED

## VEGA QSAR 1.2.6

- Status: BLOCKED on this host because Java 17+ is not installed; no result values or figures were fabricated
- Official download: https://www.vegahub.eu/download/vega-qsar-download/
- Intended output: `data/raw/vega/` and `data/processed/vega_predictions.csv`
- Intended evidence type: PREDICTED

## Definition-matched multi-model comparison

- Status: PARTIAL; ADMET-AI and ADMETlab are available, while VEGA and ProTox are blocked
- Endpoint map: `docs/methodology/endpoint_harmonization.csv`
- Comparable endpoints: AMES, DILI, carcinogenicity and hERG only
- Method: preserve platform predictions and probabilities; never average probabilities; classify agreement, disagreement or high ADMET-AI ensemble uncertainty
- Output: `results/tables/multi_model_toxicity_consensus.csv`
- Script: `analysis/models/multi_model_consensus.py`
- Generated figures: `multi_model_toxicity_consensus.svg`, `multi_model_agreement_matrix.svg`, `toxicity_model_disagreement.svg`, `prediction_vs_uncertainty.svg`
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

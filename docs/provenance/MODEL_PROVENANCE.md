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
- Model framework: Chemprop 2.3.1, PyTorch 2.8.0+cpu, Lightning 2.6.6
- Fresh Matvision run date: 2026-09-28; original 2026-09-22 cache archived
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

- Status: COMPLETE for six official web requests covering four selected endpoints and oral toxicity; API example returned 404 again on 2026-09-28. Native exports, result URLs and class-confidence semantics are recorded in `data/raw/protox/run_metadata.json`.
- Official site: https://tox.charite.de/protox3/
- Intended use: independent toxicity cross-check
- Raw output location: `data/raw/protox/`
- Evidence type: PREDICTED

## VEGA QSAR 1.2.6

- Status: COMPLETE for ten selected models on six compounds; official VEGA 1.2.6 bundle and Java 17 were executed on Matvision. See `data/raw/vega/run_metadata.json` for bundle SHA-256 and per-model versions. Other endpoints remain unexecuted.
- Official download: https://www.vegahub.eu/download/vega-qsar-download/
- Intended output: `data/raw/vega/` and `data/processed/vega_predictions.csv`
- Intended evidence type: PREDICTED

## Definition-matched multi-model comparison

- Status: PARTIAL; ADMET-AI and ADMETlab are available, VEGA and ProTox predictions are available separately but have not been added without endpoint harmonization
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

- Status: COMPLETE for an official six-compound EPI Web Suite 1.1.0 request; 118 class-specific ECOSAR rows, native units and flags retained. Submodel version IDs were not exported.
- Intended endpoints: fish acute/chronic, aquatic invertebrate and algae/aquatic plant toxicity
- Raw output location: `data/raw/ecosar/`
- Evidence type: PREDICTED unless the source explicitly identifies a measured value

## Source literature

- Zhang Z, Li W, Meng F, et al. Discover the maze-like network for glabridin biosynthesis. Nature Communications 17, 2215 (2026). https://doi.org/10.1038/s41467-026-68881-8
- Cached source data: `data/raw/literature/zhang_2026_source_data.xlsx`
- Use in this repository: pathway identifier and reaction-edge verification only; the source workbook remains unmodified

## Metabolite panel coverage

Five candidate SCENARIO panels are counted against data/compounds/compound_manifest.csv. The analysis preserves a SHA-256 of that input and does not infer reaction edges. See results/summaries/metabolite_panel_coverage.json and docs/methodology/metabolite_panel_coverage_zh.md. T1 remains PARTIAL.

## Matvision reproduction

The earlier cache-only rebuild passed 14 tests; that historical environment is archived in results/summaries/matvision_cached_reproduction_20260928.json. The latest run recomputed ADMET-AI, added four-endpoint Chemprop attribution, executed selected VEGA models and EPA/ProTox web requests, and trained the selected MapLight recipe. Current versions are recorded in results/summaries/matvision_reproduction.json. See docs/methodology/executed_models_20260929.md and the execution manifest for current provenance and checks.

The panel coverage-gap figure is generated by analysis/plotting/panel_coverage_figure.py. It supports analyte selection within the six-compound manifest and cannot demonstrate pathway observability or bottleneck discrimination.

## MapLight and Chemprop attribution

See `data/raw/maplight/run_metadata.json` for the pinned official source commit, five seeds, data split hashes, feature handling, model checkpoint hashes and held-out metrics. The upstream MIT license is retained in `analysis/vendor/MAPLIGHT_LICENSE`. No GNN extension was run.

See `data/raw/chemprop/attribution_metadata.json` for the zero-feature baseline, bond-to-atom allocation, five-member spread and 120 completeness checks.

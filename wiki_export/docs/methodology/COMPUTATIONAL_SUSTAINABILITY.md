# Computational sustainability methodology

## Scientific question

The primary comparison is a matched low-expression OC/DMT baseline without LLPS versus the same OC/DMT background with LLPS. The analysis asks whether LLPS improves product yield or productivity and whether that improvement reduces resource and process burden per unit of purified glabridin without creating unsupported safety, environmental or social claims.

## Functional unit and boundary

The working functional unit is 1 g purified glabridin. It remains subject to review by a process or sustainability stakeholder. The core recurring boundary begins with an engineered yeast inoculum and ends with analyzed or purified product. One-time strain construction is outside the core comparison and may be reported separately as an R&D scenario.

## Structure quality control

Only compounds with a traceable structure source and `structure_confirmed=yes` enter molecular models. RDKit reparses the cached SMILES, canonicalizes structures, computes formula and molecular weight, regenerates InChIKey and detects duplicates. A parse success does not replace authentic analytical standards.

## Model input policy

External services are cache-first. `analysis/run_all.py` never repeatedly calls ADMETlab, ProTox, CompTox or ECOSAR. Raw service exports are immutable inputs. Missing exports remain missing and propagate to readiness status rather than becoming zeros.

ADMETlab 3.0 was run once through its official web batch interface on the six confirmed structures. The complete 122-column CSV is cached unchanged. Ten toxicity probabilities and four physicochemical/environmental outputs are selected by an explicit endpoint map for visualization. A probability of at least 0.5 is used only to describe the model's positive-class prediction; it is not a safety threshold. Because the web export did not include model uncertainty, uncertainty is reported as unavailable rather than inferred.

ADMET-AI 2.0.1 is the primary local model because its official package includes reproducible checkpoints, task metadata and a DrugBank-approved prediction reference. The five classification or regression checkpoint outputs are retained before aggregation. The mean is the model prediction and their standard deviation is reported as ensemble spread. All supported tasks are retained; endpoints were not selected according to whether their results appeared favorable.

## Endpoint harmonization and consensus

Each model's original label, probability, confidence, uncertainty and applicability-domain fields are preserved. Probabilities from different models are not averaged. Consensus categories are assigned only when endpoint mappings and directional interpretations are explicit:

- `CONSENSUS_LOW_CONCERN`
- `CONSENSUS_CONCERN`
- `MODEL_DISAGREEMENT`
- `HIGH_UNCERTAINTY`
- `SINGLE_MODEL_ONLY`
- `NOT_AVAILABLE`

The exact mappings and exclusions are versioned in `endpoint_harmonization.csv`. AMES, DILI, carcinogenicity and hERG are currently comparable between ADMET-AI and ADMETlab. Similar-sounding skin endpoints are excluded because their definitions are not sufficiently aligned. Model disagreement is displayed and treated as a validation priority rather than suppressed.

## Applicability, calibration and leakage prevention

ADMET-AI's packaged DrugBank-approved predictions provide distributional context. Percentiles and PCA distances are prediction-space visualizations, not formal structural applicability-domain decisions and not safety rankings. Reference performance metrics distributed with ADMET-AI are reported as model metadata; this project did not independently recreate calibration curves because the training, validation and held-out labels were not redistributed in a form that supports leakage-safe recalibration.

No project compound is used for training, tuning, threshold selection or model selection. No test-set result is optimized in this repository. Future MapLight or standalone Chemprop training must freeze official train/validation/test splits, use validation data only for selection, evaluate the test split once, and report all prespecified random seeds rather than the best run.

## Wet-lab benchmark and statistics

Core biological endpoints require at least three independent biological replicates. Figures must show raw points, summary estimates and uncertainty. Technical replicates do not replace biological replicates. Two-group comparisons use a method appropriate to the data and report effect size and confidence intervals; multi-group analyses must state the exact procedure. No statistical test is run on empty templates.

## Resource, energy and cost equations

Calculations use transparent mass and energy balances. Yield is reported preferentially on a molar basis. PMI, water, solvent, waste, energy and cost are divided by the functional-unit product mass. OD-normalized substrate uptake is explicitly labeled as a proxy until a strain-specific OD600-to-dry-cell-weight calibration exists. Measured power is distinguished from nameplate or literature scenarios.

## Uncertainty

Bootstrap resampling is used only when replicate data exist. Monte Carlo analysis is used only when distributions are supported by measurements or a documented range. Arbitrary percentage uncertainty is not introduced. Scenario outputs are labeled `SCENARIO` and are never presented as measured uncertainty.

For ADMET-AI, ensemble-member standard deviation is reported without conversion to a confidence interval. `HIGH_UNCERTAINTY` uses the empirical 75th percentile across the current six-compound comparison and is therefore a relative review flag, not a validated decision threshold. ADMETlab uncertainty is marked unavailable because the cached export contains no uncertainty field.

## Interpretation boundary

QSAR predictions are early-stage screening evidence. They do not prove safety, efficacy or environmental compatibility and do not replace containment or viability experiments. Resource accounting is LCA-inspired unless system boundary, inventory, baseline and database provenance are sufficient for a defensible LCA.

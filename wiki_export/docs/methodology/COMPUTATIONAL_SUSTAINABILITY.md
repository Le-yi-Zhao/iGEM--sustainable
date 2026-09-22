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

## Endpoint harmonization and consensus

Each model's original label, probability, confidence, uncertainty and applicability-domain fields are preserved. Probabilities from different models are not averaged. Consensus categories are assigned only when endpoint mappings and directional interpretations are explicit:

- `CONSENSUS_LOW_CONCERN`
- `CONSENSUS_CONCERN`
- `MODEL_DISAGREEMENT`
- `HIGH_UNCERTAINTY`
- `SINGLE_MODEL_ONLY`
- `NOT_AVAILABLE`

## Wet-lab benchmark and statistics

Core biological endpoints require at least three independent biological replicates. Figures must show raw points, summary estimates and uncertainty. Technical replicates do not replace biological replicates. Two-group comparisons use a method appropriate to the data and report effect size and confidence intervals; multi-group analyses must state the exact procedure. No statistical test is run on empty templates.

## Resource, energy and cost equations

Calculations use transparent mass and energy balances. Yield is reported preferentially on a molar basis. PMI, water, solvent, waste, energy and cost are divided by the functional-unit product mass. OD-normalized substrate uptake is explicitly labeled as a proxy until a strain-specific OD600-to-dry-cell-weight calibration exists. Measured power is distinguished from nameplate or literature scenarios.

## Uncertainty

Bootstrap resampling is used only when replicate data exist. Monte Carlo analysis is used only when distributions are supported by measurements or a documented range. Arbitrary percentage uncertainty is not introduced. Scenario outputs are labeled `SCENARIO` and are never presented as measured uncertainty.

## Interpretation boundary

QSAR predictions are early-stage screening evidence. They do not prove safety, efficacy or environmental compatibility and do not replace containment or viability experiments. Resource accounting is LCA-inspired unless system boundary, inventory, baseline and database provenance are sufficient for a defensible LCA.

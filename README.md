# GALATEA sustainable development analysis

This repository is the development and reproducibility package for the Tsinghua-T iGEM 2026 GALATEA Sustainable Development Impact workstream. SDG 12 is the primary quantitative focus. SDG 3 defines responsible purpose, and SDG 9 tests whether the improvement could become a reliable manufacturing process.

The repository does not claim that LLPS improves sustainability until matched wet-lab measurements and process inventories are supplied.

## Current scope: skincare ingredient evaluation

Glabridin is intended for skincare. The default analysis now selects skin/eye contact, photo-related, genetic/carcinogenic hazard, formulation and environmental endpoints. Systemic and endocrine signals remain follow-up evidence because dermal exposure is not established. Oral/brain/ADME drug-development tasks are not routine current tasks.

Fresh Matvision calculations cover 17 selected ADMET-AI tasks, three Chemprop attribution endpoints and five AMES MapLight models. Prior broad exports are historical and are preserved unchanged. Relevant prior web-service outputs are selected without claiming new service execution. No cosmetic-calibrated low-risk threshold, final concentration or measured dermal absorption is available.

See [scope, methods and gaps](docs/methodology/skincare_evaluation.md), [task selection](results/tables/skincare/admet_task_selection.csv) and [current results](results/tables/skincare/evidence.csv). Rebuild with `python analysis/run_all.py`; force inference/training commands are in the methods. Current charts are under `figures/skincare/`.

## Reproduce the current package

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python analysis/run_all.py
.venv/bin/python -m unittest discover -s tests -v
```

`analysis/run_all.py` is cache-first. It validates structures, imports any available model exports, calculates only metrics supported by real inputs, regenerates code-based SVG figures, updates readiness JSON, rebuilds the site and validates local links. It does not call external model services by default.

## Historical broad execution and continuing process evidence

- Six pathway compounds (9, 10, 11, 13, 14 and 15) have traceable PubChem structures and pass RDKit consistency checks.
- The 2026 Nature Communications source workbook is cached unchanged and checksum-recorded.
- ADMET-AI 2.0.1 was run locally on all six compounds using its official five-member Chemprop ensembles: 246 normalized compound–task results and 1,230 member-level predictions are retained.
- ADMETlab 3.0 was run through its official web batch service for all six compounds; the 122-column raw CSV, metadata and normalized table are included.
- Four definition-matched ADMET-AI/ADMETlab endpoints remain separate from new platforms. Matvision now includes fresh Chemprop inference/attribution, ten VEGA models, six-compound EPI/ECOSAR exports and ProTox/admetSAR web predictions; MapLight AMES/DILI/hERG each trained five seeds. EPA CompTox still requires an API key. See `docs/methodology/executed_models_20260929.md` for scope, commands and scientific limits.
- Matched No-LLPS versus LLPS results, resource inventories, containment results and Round 2 stakeholder validation are waiting for data.
- Twelve model-result figures are generated from real cached ADMET-AI and ADMETlab predictions: five ADMET-AI panels, four multi-model panels and three ADMETlab panels. Framework figures remain clearly separated and are not simulated results.

## Input locations

- Compound structures: `data/compounds/compound_manifest.csv`
- External/local model caches: `data/raw/admet_ai/`, `admetlab/`, `vega/`, `protox/`, `comptox/`, `ecosar/`
- Wet-lab time course: `data/wetlab/metabolite_timecourse_template.csv`
- Materials, equipment and cost: `data/wetlab/*_inventory_template.csv`
- Containment: `data/wetlab/containment_template.csv`
- Stakeholder intervention log: `data/stakeholder_intervention_log.csv`

## Outputs

- Audited tables: `results/tables/`
- Readiness and provenance summaries: `results/summaries/`
- Reproducible SVG figures: `figures/evidence/`, `figures/supporting/` and `figures/framework/`
- Static website: repository root
- Official-Wiki-compatible static export: `wiki_export/`

## Scientific integrity rules

Missing data remain missing. Predictions are labeled `PREDICTED`, database values `DATABASE`, model fits `FITTED`, scenarios `SCENARIO`, and direct observations `MEASURED`. QSAR does not establish safety, and LCA-inspired inventories are not described as a full LCA without a defensible boundary, inventory, baseline and database provenance.

## Local extension: metabolite panel coverage

Run `python -m analysis.models.panel_coverage` for a standard-library-only comparison of five candidate panels. Results and limitations appear in the Model-informed experimental design website section and `docs/methodology/metabolite_panel_coverage_zh.md`. Coverage is a design scenario, not a wet-lab measurement or proof of distinguishability.

## Matvision execution and cached rebuild

Project: `/root/autodl-tmp/IGEM/GALATEA-sustainable`. Python: `/root/autodl-tmp/IGEM/.venv/bin/python`.

```bash
cd /root/autodl-tmp/IGEM/GALATEA-sustainable
/root/autodl-tmp/IGEM/.venv/bin/python analysis/run_all.py
/root/autodl-tmp/IGEM/.venv/bin/python -m unittest discover -s tests -v
```

Fresh models were executed on Matvision on 28–29 September 2026. The earlier cached rebuild is archived as `matvision_cached_reproduction_20260928.json`; current versions are in `results/summaries/matvision_reproduction.json`. The former broad pipeline generated four additional attribution/domain/environmental figures; current skincare rebuilds use the scoped figures described above. Force inference and training remain explicit separate commands. Prior ADMET-AI outputs are preserved under `data/raw/admet_ai/archive/`.

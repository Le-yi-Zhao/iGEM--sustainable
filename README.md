# GALATEA sustainable development analysis

This repository is the development and reproducibility package for the Tsinghua-T iGEM 2026 GALATEA Sustainable Development Impact workstream. SDG 12 is the primary quantitative focus. SDG 3 defines responsible purpose, and SDG 9 tests whether the improvement could become a reliable manufacturing process.

The repository does not claim that LLPS improves sustainability until matched wet-lab measurements and process inventories are supplied.

## Reproduce the current package

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python analysis/run_all.py
.venv/bin/python -m unittest discover -s tests -v
```

`analysis/run_all.py` is cache-first. It validates structures, imports any available model exports, calculates only metrics supported by real inputs, regenerates code-based SVG figures, updates readiness JSON, rebuilds the site and validates local links. It does not call external model services by default.

## Current evidence status

- Six pathway compounds (9, 10, 11, 13, 14 and 15) have traceable PubChem structures and pass RDKit consistency checks.
- The 2026 Nature Communications source workbook is cached unchanged and checksum-recorded.
- ADMETlab, ProTox, CompTox and ECOSAR outputs are blocked until raw exports are supplied.
- Matched No-LLPS versus LLPS results, resource inventories, containment results and Round 2 stakeholder validation are waiting for data.
- Framework figures describe evidence status and trade-offs; they are not simulated model results.

## Input locations

- Compound structures: `data/compounds/compound_manifest.csv`
- External model caches: `data/raw/admetlab/`, `protox/`, `comptox/`, `ecosar/`
- Wet-lab time course: `data/wetlab/metabolite_timecourse_template.csv`
- Materials, equipment and cost: `data/wetlab/*_inventory_template.csv`
- Containment: `data/wetlab/containment_template.csv`
- Stakeholder intervention log: `data/stakeholder_intervention_log.csv`

## Outputs

- Audited tables: `results/tables/`
- Readiness and provenance summaries: `results/summaries/`
- Reproducible SVG figures: `figures/evidence/` and `figures/framework/`
- Static website: repository root
- Official-Wiki-compatible static export: `wiki_export/`

## Scientific integrity rules

Missing data remain missing. Predictions are labeled `PREDICTED`, database values `DATABASE`, model fits `FITTED`, scenarios `SCENARIO`, and direct observations `MEASURED`. QSAR does not establish safety, and LCA-inspired inventories are not described as a full LCA without a defensible boundary, inventory, baseline and database provenance.

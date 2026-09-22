# ADMET-AI v2 raw cache

`admet_ai_predictions.csv` contains local ensemble-mean predictions and packaged DrugBank-approved percentiles from ADMET-AI 2.0.1. `ensemble_member_predictions.csv` preserves all five checkpoint predictions per task so uncertainty is reproducible. `run_metadata.json` records versions, device and timestamps. Regenerate cache-first with `python analysis/adapters/admet_ai_local.py --force`.

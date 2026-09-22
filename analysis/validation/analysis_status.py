from __future__ import annotations

import json
from pathlib import Path


def run(root: Path) -> Path:
    status = {
        "allowed_statuses": ["COMPLETE", "PARTIAL", "BLOCKED", "WAITING_FOR_DATA"],
        "modules": {
            "M0_structure_qc": {"status": "COMPLETE", "evidence": "results/tables/compound_structure_audit.csv"},
            "M1_admet_ai": {"status": "COMPLETE", "evidence": "data/raw/admet_ai/admet_ai_predictions.csv"},
            "M2_vega": {"status": "BLOCKED", "reason": "Java 17 runtime and VEGA QSAR model bundle are not installed"},
            "M3_protox": {"status": "BLOCKED", "reason": "official sample API script link returned HTTP 404; no manual export cached"},
            "M4_consensus": {"status": "PARTIAL", "evidence": "results/tables/multi_model_toxicity_consensus.csv", "reason": "ADMET-AI and ADMETlab only; four definition-matched endpoints"},
            "M5_admetlab": {"status": "PARTIAL", "evidence": "data/raw/admetlab/admetlab_predictions.csv", "reason": "official web batch complete; export lacks uncertainty fields"},
            "M6_comptox": {"status": "BLOCKED", "reason": "EPA CTX API key or official batch export not supplied"},
            "M7_ecosar": {"status": "BLOCKED", "reason": "ECOSAR/EPI Suite export not supplied"},
            "M8_maplight": {"status": "BLOCKED", "reason": "official reproducible repository/configuration not yet installed or validated"},
            "M9_chemprop": {"status": "PARTIAL", "evidence": "ADMET-AI 2.0.1 uses Chemprop 2.3.1 checkpoints", "reason": "standalone task retraining and attribution not yet run"},
            "M10_gp": {"status": "WAITING_FOR_DATA", "reason": "matched metabolite biological replicates are absent"},
            "M11_pathway": {"status": "WAITING_FOR_DATA", "reason": "measured metabolite AUC is absent"},
            "M12_resource": {"status": "WAITING_FOR_DATA", "reason": "batch inventories and product mass are absent"},
            "M13_sensitivity": {"status": "WAITING_FOR_DATA", "reason": "resource/cost model inputs are absent"},
            "M14_pareto": {"status": "WAITING_FOR_DATA", "reason": "time-resolved production and resource metrics are absent"},
        },
    }
    output = root / "results/summaries/analysis_status.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return output

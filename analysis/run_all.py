#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.adapters import admet_ai_local, model_cache
from analysis.models import metabolite_gp, multi_model_consensus, resource_metrics
from analysis.plotting import generate_figures, model_result_figures
from analysis.preprocessing import structure_qc
from analysis.validation import analysis_status, link_check, readiness
from analysis import build_site


def source_manifest() -> Path:
    source = ROOT / "data/raw/literature/zhang_2026_source_data.xlsx"
    output = ROOT / "results/summaries/source_file_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    files = []
    if source.exists():
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        files.append({"path": str(source.relative_to(ROOT)), "sha256": digest, "bytes": source.stat().st_size, "source_url": "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM9_ESM.xlsx"})
    output.write_text(json.dumps({"files": files}, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    completed: list[str] = []
    structure_qc.run(ROOT); completed.append("structure validation")
    admet_ai_local.run(force=False); completed.append("ADMET-AI local prediction cache")
    model_cache.run(ROOT); completed.append("cached model import")
    multi_model_consensus.run(ROOT); completed.append("multi-model consensus")
    resource_metrics.run(ROOT); completed.append("resource metrics")
    gp_outputs = metabolite_gp.run(ROOT); completed.append(f"GP figures: {len(gp_outputs)}")
    source_manifest(); completed.append("source manifest")
    readiness.run(ROOT); completed.append("readiness audit")
    generate_figures.run(ROOT); completed.append("evidence and framework figures")
    model_result_figures.run(ROOT); completed.append("real model result figures")
    analysis_status.run(ROOT); completed.append("M0-M14 analysis status")
    build_site.build(); build_site.export_wiki(); completed.append("website and wiki export")
    missing_root = link_check.run(ROOT)
    missing_export = link_check.run(ROOT / "wiki_export", ROOT / "wiki_export/index.html")
    if missing_root or missing_export:
        print(json.dumps({"status":"FAIL", "missing_root":missing_root, "missing_export":missing_export}, indent=2))
        return 1
    print(json.dumps({"status":"PASS", "completed":completed, "external_api_calls":0, "links":"PASS"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.adapters import admet_ai_local, environmental_exports
from analysis.models import metabolite_gp, resource_metrics, panel_coverage
from analysis.plotting import generate_figures, panel_coverage_figure
from analysis.preprocessing import structure_qc
from analysis.validation import analysis_status, link_check, readiness, execution_provenance
from analysis import build_site
from analysis.models import resource_scenarios
from analysis.plotting import wiki_zh, literature_content
from analysis.models import skincare_evaluation
from analysis.plotting import skincare_figures


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
    environmental_exports.run(ROOT); completed.append("executed environmental exports")
    skincare_evaluation.run(ROOT); completed.append("skincare endpoint selection and evidence")
    # Broad drug-development comparisons are historical, not current skincare tasks.
    resource_metrics.run(ROOT); completed.append("resource metrics")
    gp_outputs = metabolite_gp.run(ROOT); completed.append(f"GP figures: {len(gp_outputs)}")
    panel_coverage.run(ROOT); completed.append("metabolite panel coverage")
    panel_coverage_figure.run(ROOT); completed.append("panel coverage figure")
    source_manifest(); completed.append("source manifest")
    readiness.run(ROOT); completed.append("readiness audit")
    for figure in [generate_figures.structure_audit, generate_figures.admetlab_environmental_profiles,
                   generate_figures.admetlab_chemical_space, generate_figures.provenance_matrix,
                   generate_figures.stakeholder_flow, generate_figures.tradeoff_matrix,
                   generate_figures.integrated_dashboard, generate_figures.sdg_map]:
        figure(ROOT)
    completed.append("environmental and process framework figures")
    skincare_figures.run(ROOT); completed.append("five skincare model figures")
    # Validated historical environmental plots remain available; no broad attribution rerun.
    execution_provenance.run(ROOT); completed.append("fresh-run provenance hashes")
    analysis_status.run(ROOT); completed.append("M0-M14 analysis status")
    resource_scenarios.run(ROOT); wiki_zh.run(ROOT); completed.append("Chinese evidence figures and conditional resource analysis")
    literature_content.run(ROOT); completed.append("Eight literature content figures")
    from analysis import expanded_dashboard
    from analysis.plotting import expanded_analysis
    expanded_dashboard.run(ROOT); expanded_analysis.run(ROOT); completed.append("Expanded reference tables and environment/resource figures")
    from analysis.plotting import research_enrichment
    research_enrichment.run(ROOT); completed.append("Source-data efficacy, production and resource figures")
    from analysis.plotting import model_validation
    model_validation.run(ROOT); completed.append("MapLight GIN matched evaluation and chemical neighborhood diagnostics")
    from analysis.plotting import opera_analysis
    opera_analysis.run(ROOT); completed.append("OPERA environmental results, missing values and applicability domains")
    from analysis import human_practices
    human_practices.run(ROOT); completed.append("Professor interview decision map and three sustainability diagrams")
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

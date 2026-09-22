from __future__ import annotations

import csv
import json
from pathlib import Path


def _data_rows(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def run(root: Path) -> tuple[Path, Path]:
    summaries = root / "results" / "summaries"
    summaries.mkdir(parents=True, exist_ok=True)

    structure_rows = _data_rows(root / "results/tables/compound_structure_audit.csv")
    wetlab_rows = _data_rows(root / "data/wetlab/metabolite_timecourse_template.csv")
    material_rows = _data_rows(root / "data/wetlab/material_inventory_template.csv")
    containment_rows = _data_rows(root / "data/wetlab/containment_template.csv")
    stakeholder_rows = _data_rows(root / "data/stakeholder_intervention_log.csv")
    consensus_rows = _data_rows(root / "results/tables/toxicity_consensus.csv")
    admet_rows = _data_rows(root / "data/raw/admetlab/admetlab_predictions.csv")

    evidence = {
        "S1 Problem & Baseline": {
            "status": "PARTIAL",
            "evidence": ["docs/methodology/COMPUTATIONAL_SUSTAINABILITY.md", "data/compounds/compound_manifest.csv"],
            "gap": "matched No-LLPS versus LLPS results are absent",
        },
        "S2 Stakeholder Evidence": {
            "status": "PARTIAL" if stakeholder_rows else "WAITING_FOR_DATA",
            "evidence": ["data/stakeholder_intervention_log.csv"],
            "gap": "Round 2 and process/sustainability expert validation are absent",
        },
        "S3 Wet Lab Benchmark": {
            "status": "WAITING_FOR_DATA" if wetlab_rows == 0 else "PARTIAL",
            "evidence": ["data/wetlab/metabolite_timecourse_template.csv"],
            "gap": "raw biological replicates for G1 versus LLPS are absent",
        },
        "S4 Resource/Energy": {
            "status": "WAITING_FOR_DATA" if material_rows == 0 else "PARTIAL",
            "evidence": ["data/wetlab/material_inventory_template.csv", "data/wetlab/equipment_usage_template.csv"],
            "gap": "actual batch material and equipment-use records are absent",
        },
        "S5 Safety": {
            "status": "WAITING_FOR_DATA" if containment_rows == 0 and consensus_rows == 0 and admet_rows == 0 else "PARTIAL",
            "evidence": ["data/wetlab/containment_template.csv", "data/raw/admetlab/admetlab_predictions.csv", "results/tables/toxicity_consensus.csv"],
            "gap": "ADMETlab is single-model screening evidence; CFU containment data and an independent toxicity model are absent",
        },
        "S6 Trade-off": {
            "status": "PARTIAL",
            "evidence": ["figures/framework/positive_negative_mitigation_matrix.svg"],
            "gap": "trade-offs are structured but not yet quantified",
        },
        "S7 Integrated Impact": {
            "status": "PARTIAL",
            "evidence": ["figures/framework/integrated_impact_dashboard.svg"],
            "gap": "environmental and economic results await measured inputs",
        },
        "S8 Reproducibility": {
            "status": "PARTIAL" if structure_rows else "BLOCKED",
            "evidence": ["analysis/run_all.py", "requirements.txt", "docs/provenance/MODEL_PROVENANCE.md"],
            "gap": "ADMETlab is reproducible, but independent model exports and wet-lab datasets are not yet available",
        },
    }
    readiness = {
        "allowed_statuses": ["COMPLETE", "PARTIAL", "BLOCKED", "WAITING_FOR_DATA"],
        "generated_by": "analysis/validation/readiness.py",
        "evidence": evidence,
    }

    mapping = {
        "Q1": {"evidence_file": "data/stakeholder_intervention_log.csv", "figure": "figures/framework/stakeholder_intervention_flow.svg", "website_section": "stakeholders", "missing_gap": "Round 2 validation"},
        "Q2": {"evidence_file": "docs/methodology/COMPUTATIONAL_SUSTAINABILITY.md", "figure": "figures/framework/integrated_impact_dashboard.svg", "website_section": "integrated-impact", "missing_gap": "measured environmental and economic outcomes"},
        "Q3": {"evidence_file": "docs/limitations/CURRENT_LIMITATIONS.md", "figure": "figures/framework/positive_negative_mitigation_matrix.svg", "website_section": "trade-offs", "missing_gap": "quantified burden and mitigation results"},
        "Q4": {"evidence_file": "analysis/run_all.py", "figure": "figures/framework/evidence_provenance_matrix.svg", "website_section": "toolkit", "missing_gap": "complete model and wet-lab raw data"},
        "Q5": {"evidence_file": "data/wetlab/metabolite_timecourse_template.csv", "figure": "", "website_section": "benchmark", "missing_gap": "matched G1 versus LLPS measured data"},
    }

    readiness_path = summaries / "sustainability_readiness.json"
    mapping_path = summaries / "official_questions_mapping.json"
    readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    mapping_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return readiness_path, mapping_path

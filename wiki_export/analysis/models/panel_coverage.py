"""Design-scenario panel coverage; no inferred reaction edges or wet-lab results."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

PANELS = [("15",), ("11", "15"), ("10", "11", "15"),
          ("9", "10", "11", "14", "15"), ("9", "10", "11", "13", "14", "15")]

def evaluate(compounds, panels=PANELS):
    universe = {row["compound_id"] for row in compounds}
    if not universe or len(universe) != len(compounds):
        raise ValueError("Compound universe must be nonempty and unique")
    rows = []
    previous = set()
    for panel in panels:
        selected = set(panel)
        if not selected or len(selected) != len(panel) or not selected <= universe:
            raise ValueError("Panel must contain unique, known compound IDs")
        if not previous <= selected:
            raise ValueError("Marginal coverage requires nested panels")
        rows.append({"panel": ";".join(panel), "planned_analytes": len(selected),
            "reference_compounds": len(universe), "node_coverage_percent": round(100 * len(selected) / len(universe), 2),
            "added_vs_previous": ";".join(sorted(selected - previous, key=int)),
            "unmeasured_ids": ";".join(sorted(universe - selected, key=int)),
            "evidence_type": "SCENARIO"})
        previous = selected
    return rows

def run(root):
    source = root / "data/compounds/compound_manifest.csv"
    with source.open(encoding="utf-8-sig", newline="") as handle:
        compounds = list(csv.DictReader(handle))
    rows = evaluate(compounds)
    output = root / "results/tables/metabolite_panel_coverage.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {"status": "PARTIAL", "evidence_type": "SCENARIO",
        "source": source.relative_to(root).as_posix(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "definition": "Unique planned analytes / six compounds in the project manifest; not whole-pathway coverage.",
        "panel_origin": "Five candidate designs in the user-supplied GALATEA reference document.",
        "limitations": ["No reaction edges inferred from compound IDs.",
            "Coverage does not measure information gain, observability or bottleneck distinguishability.",
            "No detection limits, recovery, analytical cost, concentration data or authenticated standards are supplied.",
            "Branch and transformation coverage require separately verified reaction provenance.",
            "SCENARIO refers to panel selection; compound identities come from the existing database-derived manifest."],
        "panels": rows}
    target = root / "results/summaries/metabolite_panel_coverage.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output

if __name__ == "__main__":
    print(run(Path(__file__).resolve().parents[2]))

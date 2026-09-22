from __future__ import annotations

import csv
from pathlib import Path


MODEL_FILES = {
    "ADMETlab 3.0": "data/raw/admetlab/admetlab_predictions.csv",
    "ProTox 3.0": "data/raw/protox/protox_predictions.csv",
    "admetSAR 3.0": "data/raw/admetsar/admetsar_predictions.csv",
    "EPA CompTox": "data/raw/comptox/comptox_fate.csv",
    "EPA ECOSAR": "data/raw/ecosar/ecosar_aquatic.csv",
}


def _read(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def run(root: Path) -> tuple[Path, Path]:
    table_dir = root / "results" / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = table_dir / "model_run_inventory.csv"
    consensus_path = table_dir / "toxicity_consensus.csv"

    inventory: list[dict[str, str]] = []
    loaded: dict[str, list[dict[str, str]]] = {}
    for model, rel in MODEL_FILES.items():
        path = root / rel
        records = _read(path)
        loaded[model] = records
        inventory.append(
            {
                "model": model,
                "raw_file": rel,
                "status": "COMPLETE" if records else "BLOCKED",
                "records": str(len(records)),
                "reason": "cached raw export loaded" if records else "raw export not supplied",
            }
        )

    with inventory_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(inventory[0]))
        writer.writeheader()
        writer.writerows(inventory)

    # Consensus is deliberately conservative. It is produced only when both
    # model exports use the explicit normalized schema below.
    fields = [
        "compound_id",
        "endpoint",
        "admetlab_prediction",
        "admetlab_probability",
        "admetlab_uncertainty",
        "protox_prediction",
        "protox_probability",
        "protox_confidence",
        "consensus",
        "evidence_type",
    ]
    admet = loaded["ADMETlab 3.0"]
    protox = loaded["ProTox 3.0"]
    rows: list[dict[str, str]] = []
    required = {"compound_id", "endpoint", "prediction"}
    if admet and protox and required.issubset(admet[0]) and required.issubset(protox[0]):
        a = {(r["compound_id"], r["endpoint"]): r for r in admet}
        p = {(r["compound_id"], r["endpoint"]): r for r in protox}
        for key in sorted(set(a) | set(p)):
            ar, pr = a.get(key), p.get(key)
            if ar and pr:
                av = ar["prediction"].strip().lower()
                pv = pr["prediction"].strip().lower()
                consensus = "CONSENSUS_CONCERN" if av == pv == "concern" else "CONSENSUS_LOW_CONCERN" if av == pv == "low_concern" else "MODEL_DISAGREEMENT"
            else:
                consensus = "SINGLE_MODEL_ONLY"
            rows.append(
                {
                    "compound_id": key[0],
                    "endpoint": key[1],
                    "admetlab_prediction": ar.get("prediction", "") if ar else "",
                    "admetlab_probability": ar.get("probability", "") if ar else "",
                    "admetlab_uncertainty": ar.get("uncertainty", "") if ar else "",
                    "protox_prediction": pr.get("prediction", "") if pr else "",
                    "protox_probability": pr.get("probability", "") if pr else "",
                    "protox_confidence": pr.get("confidence", "") if pr else "",
                    "consensus": consensus,
                    "evidence_type": "PREDICTED",
                }
            )

    with consensus_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return inventory_path, consensus_path


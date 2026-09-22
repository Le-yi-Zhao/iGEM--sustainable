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

ADMETLAB_TOXICITY_ENDPOINTS = {
    "SkinSen": "Skin sensitization",
    "Ames": "Ames mutagenicity",
    "DILI": "Drug-induced liver injury",
    "Carcinogenicity": "Carcinogenicity",
    "Respiratory": "Respiratory toxicity",
    "H-HT": "Human hepatotoxicity",
    "Neurotoxicity-DI": "Neurotoxicity",
    "Nephrotoxicity-DI": "Nephrotoxicity",
    "Genotoxicity": "Genotoxicity",
    "hERG": "hERG inhibition",
}

ADMETLAB_ENVIRONMENT_ENDPOINTS = {
    "logP": "logP",
    "logS": "logS",
    "BCF": "BCF model output",
    "IGC50": "Tetrahymena IGC50 output",
    "LC50DM": "Daphnia LC50 output",
    "LC50FM": "Fathead minnow LC50 output",
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
    selected_path = table_dir / "admetlab_selected_predictions.csv"

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

    # Normalize the native ADMETlab wide export. Rows are joined to the exact
    # input SMILES rather than inferred from names or internal compound IDs.
    selected: list[dict[str, str]] = []
    manifest = _read(root / "data/compounds/compound_manifest.csv")
    by_smiles = {row["canonical_smiles"]: row for row in manifest}
    admet_native = loaded["ADMETlab 3.0"]
    if admet_native and "raw_smiles" in admet_native[0]:
        for row in admet_native:
            compound = by_smiles.get(row["raw_smiles"])
            if not compound:
                continue
            for raw_endpoint, label in {**ADMETLAB_TOXICITY_ENDPOINTS, **ADMETLAB_ENVIRONMENT_ENDPOINTS}.items():
                value = row.get(raw_endpoint, "")
                if value == "":
                    continue
                selected.append({
                    "compound_id": compound["compound_id"],
                    "compound_name": compound["compound_name"],
                    "category": "toxicity_probability" if raw_endpoint in ADMETLAB_TOXICITY_ENDPOINTS else "environmental_property",
                    "endpoint": label,
                    "raw_endpoint": raw_endpoint,
                    "value": value,
                    "model": "ADMETlab 3.0",
                    "evidence_type": "PREDICTED",
                })
    selected_fields = ["compound_id", "compound_name", "category", "endpoint", "raw_endpoint", "value", "model", "evidence_type"]
    with selected_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=selected_fields)
        writer.writeheader()
        writer.writerows(selected)

    # Consensus remains conservative: an ADMETlab-only result is explicitly
    # SINGLE_MODEL_ONLY, never represented as agreement.
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
    if selected:
        for r in selected:
            if r["category"] != "toxicity_probability":
                continue
            probability = float(r["value"])
            rows.append({
                "compound_id": r["compound_id"],
                "endpoint": r["endpoint"],
                "admetlab_prediction": "concern" if probability >= 0.5 else "low_concern",
                "admetlab_probability": r["value"],
                "admetlab_uncertainty": "",
                "protox_prediction": "",
                "protox_probability": "",
                "protox_confidence": "",
                "consensus": "SINGLE_MODEL_ONLY",
                "evidence_type": "PREDICTED",
            })
    elif admet and protox and required.issubset(admet[0]) and required.issubset(protox[0]):
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

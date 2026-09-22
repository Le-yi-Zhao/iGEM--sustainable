from __future__ import annotations

import csv
from pathlib import Path


MASS_TO_G = {"g": 1.0, "mg": 0.001, "kg": 1000.0}
VOLUME_TO_L = {"l": 1.0, "ml": 0.001, "ul": 0.000001}
POWER_TO_KW = {"kw": 1.0, "w": 0.001}


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def run(root: Path) -> Path:
    output = root / "results/tables/resource_metrics.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["experiment_id", "group", "replicate", "pmi_g_per_g", "water_l_per_g", "solvent_l_per_g", "energy_kwh_per_g", "evidence_type", "status"]
    materials = _read(root / "data/wetlab/material_inventory_template.csv")
    equipment = _read(root / "data/wetlab/equipment_usage_template.csv")
    batches = _read(root / "data/wetlab/batch_summary_template.csv")
    batch_map = {(r["experiment_id"], r["group"], r["replicate"]): r for r in batches if r.get("isolated_product_mass_g")}
    results: list[dict[str, str]] = []
    for key, batch in batch_map.items():
        product = float(batch["isolated_product_mass_g"])
        if product <= 0:
            continue
        matched_materials = [r for r in materials if (r["experiment_id"], r["group"], r["replicate"]) == key and r.get("amount")]
        total_mass_g = 0.0
        water_l = 0.0
        solvent_l = 0.0
        complete = True
        for row in matched_materials:
            unit = row["unit"].strip().lower()
            value = float(row["amount"])
            if unit in MASS_TO_G:
                total_mass_g += value * MASS_TO_G[unit]
            elif unit in VOLUME_TO_L:
                liters = value * VOLUME_TO_L[unit]
                name = row["material"].strip().lower()
                if name == "water": water_l += liters
                elif name in {"ethyl acetate", "methanol", "acetonitrile"}: solvent_l += liters
                else: complete = False
            else:
                complete = False
        energy = 0.0
        for row in equipment:
            if (row["experiment_id"], row["group"], row["replicate"]) != key or not row.get("power_value") or not row.get("use_time_h"):
                continue
            unit = row["power_unit"].strip().lower()
            if unit not in POWER_TO_KW:
                complete = False; continue
            allocation = float(row["batch_samples"] or 1)
            energy += float(row["power_value"]) * POWER_TO_KW[unit] * float(row["use_time_h"]) / allocation
        results.append({
            "experiment_id": key[0], "group": key[1], "replicate": key[2],
            "pmi_g_per_g": f"{total_mass_g/product:.6g}" if complete else "",
            "water_l_per_g": f"{water_l/product:.6g}", "solvent_l_per_g": f"{solvent_l/product:.6g}",
            "energy_kwh_per_g": f"{energy/product:.6g}", "evidence_type": batch.get("source_type", "MEASURED"),
            "status": "COMPLETE" if complete else "PARTIAL",
        })
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(results)
    return output


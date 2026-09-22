from __future__ import annotations

import csv
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors


def run(root: Path) -> Path:
    source = root / "data" / "compounds" / "compound_manifest.csv"
    output = root / "results" / "tables" / "compound_structure_audit.csv"
    output.parent.mkdir(parents=True, exist_ok=True)

    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    audited: list[dict[str, str]] = []
    connectivity_seen: dict[str, str] = {}
    for row in rows:
        confirmed = row["structure_confirmed"].strip().lower() == "yes"
        mol = Chem.MolFromSmiles(row["canonical_smiles"]) if confirmed else None
        parsed = mol is not None
        if parsed:
            computed_smiles = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
            connectivity = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=False)
            computed_formula = rdMolDescriptors.CalcMolFormula(mol)
            computed_mw = Descriptors.MolWt(mol)
            computed_inchikey = Chem.InchiToInchiKey(Chem.MolToInchi(mol))
            duplicate_of = connectivity_seen.get(connectivity, "")
            connectivity_seen.setdefault(connectivity, row["compound_id"])
            formula_match = computed_formula == row["molecular_formula"]
            mw_match = abs(computed_mw - float(row["molecular_weight"])) <= 0.15
            inchikey_match = computed_inchikey == row["inchikey"]
            status = "PASS" if formula_match and mw_match and inchikey_match and not duplicate_of else "WARNING"
        else:
            computed_smiles = connectivity = computed_formula = computed_inchikey = duplicate_of = ""
            computed_mw = 0.0
            formula_match = mw_match = inchikey_match = False
            status = "NOT_CONFIRMED" if not confirmed else "FAIL"

        audited.append(
            {
                "compound_id": row["compound_id"],
                "compound_name": row["compound_name"],
                "structure_confirmed": row["structure_confirmed"],
                "parse_success": str(parsed).lower(),
                "computed_canonical_smiles": computed_smiles,
                "computed_molecular_formula": computed_formula,
                "recorded_molecular_formula": row["molecular_formula"],
                "formula_match": str(formula_match).lower(),
                "computed_molecular_weight": f"{computed_mw:.4f}" if parsed else "",
                "recorded_molecular_weight": row["molecular_weight"],
                "molecular_weight_match": str(mw_match).lower(),
                "computed_inchikey": computed_inchikey,
                "recorded_inchikey": row["inchikey"],
                "inchikey_match": str(inchikey_match).lower(),
                "duplicate_connectivity_of": duplicate_of,
                "source": row["structure_source"],
                "source_url": row["structure_source_url"],
                "evidence_type": "DATABASE+COMPUTED",
                "audit_status": status,
            }
        )

    fields = list(audited[0]) if audited else []
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(audited)
    return output


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[2])


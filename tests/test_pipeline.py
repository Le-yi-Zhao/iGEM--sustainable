from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from analysis.validation.link_check import run as check_links


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_structure_audit_passes(self) -> None:
        path = ROOT / "results/tables/compound_structure_audit.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(6, len(rows))
        self.assertTrue(all(r["audit_status"] == "PASS" for r in rows))
        self.assertTrue(all(not r["duplicate_connectivity_of"] for r in rows))

    def test_readiness_uses_allowed_states(self) -> None:
        data = json.loads((ROOT / "results/summaries/sustainability_readiness.json").read_text(encoding="utf-8"))
        allowed = set(data["allowed_statuses"])
        self.assertTrue(all(item["status"] in allowed for item in data["evidence"].values()))

    def test_links(self) -> None:
        self.assertEqual([], check_links(ROOT))
        self.assertEqual([], check_links(ROOT / "wiki_export", ROOT / "wiki_export/index.html"))

    def test_real_admetlab_outputs(self) -> None:
        with (ROOT / "data/raw/admetlab/admetlab_predictions.csv").open(encoding="utf-8-sig", newline="") as handle:
            raw = list(csv.DictReader(handle))
        with (ROOT / "results/tables/admetlab_selected_predictions.csv").open(encoding="utf-8", newline="") as handle:
            selected = list(csv.DictReader(handle))
        metadata = json.loads((ROOT / "data/raw/admetlab/run_metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(6, len(raw))
        self.assertEqual(96, len(selected))
        self.assertEqual("339e57a1a97c24b31790055148", metadata["result_id"])
        for name in ["toxicity_prediction_probability.svg", "environmental_model_outputs.svg", "predicted_chemical_property_landscape.svg"]:
            self.assertGreater((ROOT / "figures/evidence" / name).stat().st_size, 1000)

    def test_no_obsolete_light_fields(self) -> None:
        targets = [ROOT / "data/process_inventory.csv", ROOT / "data/wetlab_gap_audit.csv", ROOT / "index.html"]
        banned = ["LED wavelength", "irradiance", "duty cycle", "Light Paradox", "No LLPS + Light", "LLPS + Light"]
        for target in targets:
            text = target.read_text(encoding="utf-8")
            for phrase in banned:
                self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()

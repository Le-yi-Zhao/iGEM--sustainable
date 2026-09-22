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

    def test_real_admet_ai_outputs(self) -> None:
        with (ROOT / "data/raw/admet_ai/admet_ai_predictions.csv").open(encoding="utf-8", newline="") as handle:
            raw = list(csv.DictReader(handle))
        with (ROOT / "data/raw/admet_ai/ensemble_member_predictions.csv").open(encoding="utf-8", newline="") as handle:
            members = list(csv.DictReader(handle))
        with (ROOT / "data/processed/admet_ai_predictions.csv").open(encoding="utf-8", newline="") as handle:
            processed = list(csv.DictReader(handle))
        self.assertEqual(6, len(raw))
        self.assertEqual(1230, len(members))
        self.assertEqual(246, len(processed))
        self.assertEqual(41, len({row["task"] for row in processed}))
        self.assertTrue(all(sum(1 for member in members if member["compound_id"] == row["compound_id"] and member["task"] == row["task"]) == 5 for row in processed))

    def test_multi_model_outputs_and_figures(self) -> None:
        with (ROOT / "results/tables/multi_model_toxicity_consensus.csv").open(encoding="utf-8", newline="") as handle:
            consensus = list(csv.DictReader(handle))
        self.assertEqual(24, len(consensus))
        self.assertEqual({"AMES mutagenicity", "Drug-induced liver injury", "Carcinogenicity", "hERG inhibition"}, {row["endpoint"] for row in consensus})
        figure_paths = [
            "figures/evidence/toxicity_prediction_probability.svg",
            "figures/evidence/environmental_model_outputs.svg",
            "figures/evidence/predicted_chemical_property_landscape.svg",
            "figures/evidence/multi_model_toxicity_consensus.svg",
            "figures/supporting/admet_ai_endpoint_heatmap.svg",
            "figures/supporting/admet_ai_compound_profiles.svg",
            "figures/supporting/admet_ai_drugbank_reference.svg",
            "figures/supporting/admet_ai_compound_distance.svg",
            "figures/supporting/admet_ai_ensemble_uncertainty.svg",
            "figures/supporting/multi_model_agreement_matrix.svg",
            "figures/supporting/toxicity_model_disagreement.svg",
            "figures/supporting/prediction_vs_uncertainty.svg",
        ]
        self.assertEqual(12, len(figure_paths))
        self.assertTrue(all((ROOT / path).stat().st_size > 1000 for path in figure_paths))

    def test_analysis_status_and_endpoint_harmonization(self) -> None:
        status = json.loads((ROOT / "results/summaries/analysis_status.json").read_text(encoding="utf-8"))
        self.assertEqual(15, len(status["modules"]))
        self.assertTrue(all(item["status"] in {"COMPLETE", "PARTIAL", "BLOCKED", "WAITING_FOR_DATA"} for item in status["modules"].values()))
        harmonization = (ROOT / "docs/methodology/endpoint_harmonization.csv").read_text(encoding="utf-8")
        self.assertIn("Skin", harmonization)
        self.assertIn("no", harmonization)


if __name__ == "__main__":
    unittest.main()

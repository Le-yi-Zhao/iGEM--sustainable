import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from analysis.models.panel_coverage import evaluate, run

class PanelCoverageTests(unittest.TestCase):
    def setUp(self):
        self.compounds=[{"compound_id": str(i)} for i in [9,10,11,13,14,15]]
    def test_counts_and_missing_members(self):
        rows=evaluate(self.compounds)
        self.assertEqual([r["planned_analytes"] for r in rows],[1,2,3,5,6])
        self.assertEqual(rows[3]["unmeasured_ids"],"13")
        self.assertEqual(rows[4]["added_vs_previous"],"13")
        self.assertTrue(all(r["evidence_type"]=="SCENARIO" for r in rows))
    def test_unknown_duplicate_and_nonnested_panels_fail(self):
        for panels in [[("99",)],[("15","15")],[("15",),("11",)]]:
            with self.subTest(panels=panels), self.assertRaises(ValueError):
                evaluate(self.compounds,panels)
    def test_reference_set_validation(self):
        for compounds in [[],self.compounds+self.compounds[:1]]:
            with self.assertRaises(ValueError): evaluate(compounds)
    def test_order_invariance_and_denominator(self):
        self.assertEqual(evaluate(self.compounds),evaluate(self.compounds[::-1]))
        self.assertEqual(evaluate(self.compounds+[{"compound_id":"16"}])[-1]["node_coverage_percent"],85.71)
    def test_provenance_tracks_exact_input_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/"data/compounds/compound_manifest.csv"
            source.parent.mkdir(parents=True)
            source.write_text("compound_id\n9\n10\n11\n13\n14\n15\n")
            run(root)
            summary=json.loads((root/"results/summaries/metabolite_panel_coverage.json").read_text())
            self.assertEqual(summary["source_sha256"],hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(summary["status"],"PARTIAL")

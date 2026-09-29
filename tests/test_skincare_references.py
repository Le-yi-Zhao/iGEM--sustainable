import hashlib
import json
import math
import statistics
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'data/raw/skincare/references'


class ReferenceEvidenceTests(unittest.TestCase):
    def test_frozen_panel_structures_and_source_provenance(self):
        path = ROOT/'data/compounds/skincare_reference_panel.json'
        panel = json.loads(path.read_text())
        meta = json.loads((RAW/'run_metadata.json').read_text())
        self.assertEqual(meta['panel_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(5, len(panel['references']))
        for ref in panel['references']:
            self.assertTrue(ref['source_ids'])
            for source in ref['source_ids']:
                self.assertIn(source, panel['sources'])
        for source in meta['structure_sources']:
            self.assertEqual(source['sha256'], hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest())
        compounds = {c['id']: c for c in json.loads((RAW/'structures.json').read_text())}
        self.assertNotEqual(compounds['alpha_arbutin']['inchikey'], compounds['beta_arbutin']['inchikey'])

    def test_published_aggregates_match_complete_member_evidence(self):
        rows = json.loads((ROOT/'results/tables/skincare/reference_predictions.json').read_text())
        members = json.loads((RAW/'member_predictions.json').read_text())
        self.assertEqual(108, len(rows))
        self.assertEqual(540, len(members))
        keys = set()
        for row in rows:
            key = row['id'], row['model'], row['task']
            self.assertNotIn(key, keys); keys.add(key)
            data = [v['value'] for v in members if (v['id'], v['model'], v['task']) == key]
            self.assertEqual(5, len(data))
            self.assertTrue(all(math.isfinite(v) for v in data))
            self.assertAlmostEqual(row['mean'], statistics.mean(data), places=5)
            self.assertAlmostEqual(row['sd'], statistics.stdev(data), places=5)

    def test_reference_comparison_does_not_claim_independent_safety_validation(self):
        meta = json.loads((RAW/'run_metadata.json').read_text())
        self.assertIsNone(meta['calibrated_low_risk_threshold'])
        self.assertIsNone(meta['safe_glabridin_concentration'])
        audit = {r.get('split'): r for r in meta['membership_audit'] if r['model'] == 'MapLight'}
        self.assertIn('niacinamide', audit['train_val']['overlapping_ids_connectivity'])
        self.assertIn('kojic_acid', audit['test']['overlapping_ids_connectivity'])
        self.assertLess(meta['glabridin_reproduction_max_abs_delta']['ADMET-AI'], 1e-5)
        self.assertLess(meta['glabridin_reproduction_max_abs_delta']['MapLight'], 1e-10)
        self.assertIn('原光甘草定输出复现一致', (ROOT/'index.html').read_text())


if __name__ == '__main__':
    unittest.main()

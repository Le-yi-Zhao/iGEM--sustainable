import csv
import hashlib
import json
import unittest
from pathlib import Path
from analysis.models.skincare_scope import ACTIVE_AI, ATTRIBUTION_TASKS
from analysis.models.skincare_evaluation import validate_rows

ROOT=Path(__file__).resolve().parents[1]
def read(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

class SkincareTests(unittest.TestCase):
    def test_selected_predictions_and_historical_retention(self):
        selected=read('data/processed/skincare/admet_ai_predictions.csv')
        self.assertEqual(6*17,len(selected))
        self.assertEqual(set(ACTIVE_AI),{r['task'] for r in selected})
        self.assertTrue({'AMES','Skin_Reaction','Carcinogens_Lagunin','NR-ER','SR-p53'} <= set(ACTIVE_AI))
        self.assertFalse({'hERG','DILI','BBB_Martins','HIA_Hou'} & set(ACTIVE_AI))
        self.assertEqual(246,len(read('data/processed/admet_ai_predictions.csv')))
        self.assertEqual(510,len(read('data/raw/skincare/admet_ai/ensemble_member_predictions.csv')))

    def test_attribution_matches_current_inference_and_sums(self):
        raw=read('data/raw/skincare/chemprop/integrated_gradients_members.csv')
        checks=read('results/tables/skincare/chemprop_attribution_completeness.csv')
        self.assertEqual(90,len(checks))
        self.assertEqual(set(ATTRIBUTION_TASKS),{r['task'] for r in checks})
        fresh={(r['compound_id'],r['task'],r['ensemble_member']):float(r['prediction']) for r in read('data/raw/skincare/admet_ai/ensemble_member_predictions.csv')}
        sums={}
        for r in raw:
            key=(r['compound_id'],r['task'],r['ensemble_member'])
            sums[key]=sums.get(key,0)+float(r['attribution'])
        for r in checks:
            key=(r['compound_id'],r['task'],r['ensemble_member'])
            self.assertLessEqual(abs(sums[key]-float(r['prediction'])+float(r['baseline_prediction'])),.005)
            self.assertAlmostEqual(fresh[key],float(r['prediction']),places=5)

    def test_scoped_training_and_evaluation(self):
        meta=json.loads((ROOT/'data/raw/skincare/maplight/run_metadata.json').read_text())
        self.assertEqual(['ames'],meta['selected_tasks']);self.assertEqual(5,len(meta['checkpoints']))
        rows=read('results/tables/skincare/maplight_heldout_metrics.csv')
        self.assertEqual(5,len(rows));self.assertTrue(all(r['test_used_for_fit']=='False' for r in rows))
        self.assertEqual(30,len(read('data/raw/skincare/maplight/member_predictions.csv')))

    def test_missing_inputs_never_become_safety_claims(self):
        summary=json.loads((ROOT/'results/summaries/skincare_scope.json').read_text())
        self.assertIsNone(summary['calibrated_low_risk_threshold'])
        self.assertIsNone(summary['systemic_safety_margin'])
        gaps=read('results/tables/skincare/evidence_gaps.csv')
        self.assertTrue(any(r['topic']=='Dermal absorption' and r['status']=='WAITING_FOR_DATA' for r in gaps))
        rows=read('results/tables/skincare/evidence.csv')
        self.assertTrue(any(r['raw_endpoint']=='Skin_irritation' for r in rows))
        self.assertTrue(any(r['raw_endpoint']=='Photoallergy' for r in rows))
        self.assertTrue(any(r['raw_endpoint']=='Repeated_dose_toxicity' for r in rows))
        self.assertTrue(all(r['value_semantics'].startswith('reported_class') for r in rows if r['platform']=='ProTox'))
        self.assertNotIn('multi_model_toxicity_consensus.svg',(ROOT/'index.html').read_text())

    def test_mapping_rejects_duplicate_or_bad_values(self):
        with self.assertRaises(ValueError):validate_rows([{'compound_id':'15','x':'.2'}]*2,{'15'},['x'])
        with self.assertRaises(ValueError):validate_rows([{'compound_id':'15','x':'nan'}],{'15'},['x'])

    def test_selected_source_provenance(self):
        summary=json.loads((ROOT/'results/summaries/skincare_scope.json').read_text())
        for item in summary['files']+summary['fresh_run_files']:
            self.assertEqual(item['sha256'],hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()

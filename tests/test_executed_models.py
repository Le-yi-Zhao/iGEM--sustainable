import csv
import hashlib
import json
import unittest
from pathlib import Path
from analysis.adapters.environmental_exports import ecosar_domain, connectivity

ROOT=Path(__file__).resolve().parents[1]
def read(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

class ExecutedModelsTests(unittest.TestCase):
    def test_attribution_completeness_and_members(self):
        raw=read('data/raw/chemprop/integrated_gradients_members.csv')
        checks=read('results/tables/chemprop_attribution_completeness.csv')
        fresh={(r['compound_id'],r['task'],r['ensemble_member']):float(r['prediction']) for r in read('data/raw/admet_ai/ensemble_member_predictions.csv')}
        self.assertEqual(120,len(checks))
        for r in checks:
            key=(r['compound_id'],r['task'],r['ensemble_member'])
            actual_sum=sum(float(a['attribution']) for a in raw if (a['compound_id'],a['task'],a['ensemble_member'])==key)
            self.assertAlmostEqual(actual_sum,float(r['attribution_sum']),places=5)
            self.assertLessEqual(abs(actual_sum-float(r['prediction'])+float(r['baseline_prediction'])),.005)
            self.assertAlmostEqual(fresh[key],float(r['prediction']),places=5)
        for r in read('results/tables/chemprop_atom_attribution.csv'):self.assertEqual('5',r['count'])

    def test_fresh_checkpoint_provenance(self):
        meta=json.loads((ROOT/'data/raw/admet_ai/run_metadata.json').read_text())
        self.assertIn('fresh checkpoint inference',meta['execution_mode'])
        self.assertEqual(10,len(meta['checkpoint_manifest']))
        self.assertEqual(hashlib.sha256((ROOT/'data/compounds/compound_manifest.csv').read_bytes()).hexdigest(),meta['input_sha256'])
        self.assertTrue(list((ROOT/'data/raw/admet_ai/archive').glob('*/run_metadata.json')))

    def test_vega_coverage_and_warnings(self):
        rows=read('data/processed/vega_predictions.csv')
        self.assertEqual(60,len(rows));self.assertEqual(10,len({r['model_tag'] for r in rows}))
        for model in {r['model_tag'] for r in rows}:
            self.assertEqual({'9','10','11','13','14','15'},{r['compound_id'] for r in rows if r['model_tag']==model})
        self.assertTrue(all(r['connectivity_matches_input']=='True' for r in rows))
        self.assertTrue(any(r['source_molecular_weight_warning']=='True' for r in rows))
        self.assertTrue(all(0<=float(r['applicability_domain_index'])<=1 for r in rows))

    def test_ecosar_domain_edges_and_native_flags(self):
        self.assertEqual('UNKNOWN',ecosar_domain({'Selected Log Kow':'','Max Log Kow':'5'}))
        self.assertEqual('EXCEEDS_MAX_LOGKOW',ecosar_domain({'Selected Log Kow':'6','Max Log Kow':'5','Flags':''}))
        self.assertEqual('SOURCE_FLAG_PRESENT',ecosar_domain({'Selected Log Kow':'4','Max Log Kow':'5','Flags':'*'}))
        rows=read('data/processed/ecosar_predictions.csv');native=read('data/raw/ecosar/ecosar_aquatic.csv')
        self.assertEqual(118,len(rows));self.assertEqual(len(native),len(rows))
        self.assertEqual(24,sum(r['domain_flag']=='EXCEEDS_MAX_LOGKOW' for r in rows))
        by_smiles={r['canonical_smiles']:r['compound_id'] for r in read('data/compounds/compound_manifest.csv')}
        for r in rows:
            self.assertEqual(by_smiles[r['Submitted Chemical']],r['compound_id'])
            self.assertEqual(connectivity(r['Submitted Chemical']),connectivity(r['SMILES']))
            self.assertIn(r['Flags'],[n['Flags'] for n in native if n['Submitted Chemical']==r['Submitted Chemical']])

    def test_protox_predicted_class_confidence(self):
        rows=read('data/raw/protox/protox_predictions.csv')
        self.assertEqual(24,len(rows));self.assertEqual(6,len({r['compound_id'] for r in rows}))
        self.assertTrue(all(r['confidence_semantics']=='confidence_of_reported_class' for r in rows))
        self.assertTrue(all(0<=float(r['confidence'])<=1 for r in rows))

    def test_maplight_heldout_protocol(self):
        meta=json.loads((ROOT/'data/raw/maplight/run_metadata.json').read_text())
        self.assertEqual([1,2,3,4,5],meta['seeds']);self.assertEqual(15,len(meta['checkpoints']))
        rows=read('results/tables/maplight_heldout_metrics.csv')
        self.assertEqual(15,len(rows));self.assertTrue(all(r['test_used_for_fit']=='False' for r in rows))
        members=read('data/raw/maplight/member_predictions.csv')
        self.assertEqual(90,len(members))
        self.assertTrue(all(0<=float(r['positive_class_probability'])<=1 for r in members))
        for entry in meta['datasets']:
            if 'file' in entry:self.assertEqual(entry['sha256'],hashlib.sha256((ROOT/entry['file']).read_bytes()).hexdigest())

    def test_admetsar_structure_mapping_and_domain(self):
        from rdkit import Chem
        canonical=lambda s:Chem.MolToSmiles(Chem.MolFromSmiles(s),isomericSmiles=True)
        manifest={r['compound_id']:canonical(r['canonical_smiles']) for r in read('data/compounds/compound_manifest.csv')}
        rows=read('data/processed/admetsar_predictions.csv')
        self.assertEqual(6,len(rows))
        for r in rows:
            self.assertEqual(manifest[r['compound_id']],canonical(r['SMILES']))
            self.assertEqual('NOT_EXPORTED',r['applicability_domain'])

    def test_raw_provenance_hashes(self):
        meta=json.loads((ROOT/'results/summaries/fresh_execution_manifest.json').read_text())
        for entry in meta['files']:self.assertEqual(entry['sha256'],hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()

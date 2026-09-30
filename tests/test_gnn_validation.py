import json,unittest
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss
from rdkit import Chem
R=Path(__file__).resolve().parents[1]
class GNNValidationTests(unittest.TestCase):
    def test_baseline_reproduction_and_fixed_labels(self):
        p=pd.read_csv(R/'data/raw/skincare/maplight_gnn/heldout_predictions.csv')
        old=pd.read_csv(R/'data/raw/skincare/maplight/ames_test_predictions.csv')
        self.assertEqual(len(p),len(old));self.assertTrue(np.array_equal(p.Y,old.Y));self.assertTrue(np.array_equal(p.Drug,old.Drug))
        for i in range(1,6):self.assertLess(np.max(np.abs(p[f'base_seed_{i}']-old[f'probability_seed_{i}'])),1e-10)
        for model in ['base','gnn']:
            self.assertTrue(np.isfinite(p[f'{model}_mean']).all())
            self.assertTrue(p[f'{model}_mean'].between(0,1).all())
            np.testing.assert_allclose(p[f'{model}_mean'],p[[f'{model}_seed_{i}' for i in range(1,6)]].mean(axis=1))
    def test_metrics_and_overlap_audit(self):
        p=pd.read_csv(R/'data/raw/skincare/maplight_gnn/heldout_predictions.csv')
        train=pd.read_csv(R/'data/raw/skincare/maplight/ames_train_val.csv')
        key=lambda s:Chem.MolToSmiles(Chem.MolFromSmiles(s),isomericSmiles=False)
        trainkeys=set(train.Drug.map(key));overlap=p.Drug.map(key).isin(trainkeys)
        self.assertTrue(np.array_equal(overlap,p.overlaps_training_connectivity))
        m=json.loads((R/'data/raw/skincare/maplight_gnn/run_metadata.json').read_text())
        self.assertFalse(m['test_used_for_fit_tuning_stopping'])
        self.assertEqual(m['feature_count'],2863)
        for r in m['ensemble_metrics']:
            s=p if r['split']=='official_test' else p[~overlap]
            col='base_mean' if r['model']=='MapLight' else 'gnn_mean'
            self.assertEqual(r['n'],len(s))
            for k,fn in [('roc_auc',roc_auc_score),('average_precision',average_precision_score),('brier',brier_score_loss)]:self.assertAlmostEqual(r[k],fn(s.Y,s[col]),places=10)
    def test_all_reference_members_present(self):
        p=pd.read_csv(R/'data/raw/skincare/maplight_gnn/reference_members.csv')
        self.assertEqual(len(p),160);self.assertEqual(len(p.id.unique()),16)
        self.assertTrue((p.groupby(['id','model']).size()==5).all());self.assertTrue(p.score.between(0,1).all())
if __name__=='__main__':unittest.main()

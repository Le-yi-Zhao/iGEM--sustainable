import json,unittest,hashlib
from pathlib import Path
import pandas as pd
from analysis.plotting.opera_analysis import ENDPOINTS
R=Path(__file__).resolve().parents[1]
class OperaTests(unittest.TestCase):
    def test_complete_output_preserves_missing_and_domain(self):
        raw=pd.read_csv(R/'data/raw/skincare/opera/predictions.csv').set_index('MoleculeID')
        d=pd.read_csv(R/'results/tables/research_enrichment/opera_all_endpoints_zh.csv')
        self.assertEqual(len(d),126);self.assertEqual(d.value.notna().sum(),123)
        self.assertEqual(set(d[d.value.isna()].id),{'urea'})
        self.assertEqual(set(d[d.value.isna()].endpoint),{'ReadyBiodeg','KM','Koc'})
        columns={key:col for col,key,*_ in ENDPOINTS}
        for x in d.itertuples():
            self.assertEqual(x.global_ad,raw.loc[x.id,'AD_'+x.endpoint])
            if pd.isna(x.value):self.assertEqual(x.status,'计算缺失')
            else:self.assertEqual(x.value,raw.loc[x.id,columns[x.endpoint]])
        self.assertEqual(raw.loc['glabridin','ReadyBiodeg_pred'],0)
        self.assertEqual(raw.loc['glabridin','LogBCF_pred'],1.7)
    def test_provenance_and_prior_selection(self):
        r=R/'data/raw/skincare/opera';m=json.loads((r/'run_metadata.json').read_text())
        for name,sha in m['checksums'].items():self.assertEqual(hashlib.sha256((r/name).read_bytes()).hexdigest(),sha)
        panel=json.loads((r/'input_manifest.json').read_text())
        self.assertEqual(len(panel['structures']),21);self.assertIn('BioDeg',panel['excluded_endpoints']);self.assertEqual(len(panel['selected_endpoints']),6)
if __name__=='__main__':unittest.main()

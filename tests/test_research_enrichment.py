import csv,unittest
from pathlib import Path
import pandas as pd
from analysis.plotting.research_enrichment import efficacy_data
R=Path(__file__).resolve().parents[1]
class ResearchEnrichmentTests(unittest.TestCase):
    def test_matched_molar_ratios(self):
        rows=efficacy_data()
        self.assertEqual(len({r['doi'] for r in rows}),3)
        self.assertAlmostEqual(rows[1]['glabridin_ic50_uM'],.080)
        self.assertAlmostEqual(rows[1]['kojic_over_glabridin'],412.5)
        self.assertAlmostEqual(rows[2]['kojic_over_glabridin'],17/.294)
    def test_all_production_values_match_workbook_cells(self):
        out=pd.read_csv(R/'results/tables/research_enrichment/production_replicates.csv')
        source={s:pd.read_excel(R/'data/raw/literature/zhang_2026_source_data.xlsx',sheet_name=s,header=None) for s in out.sheet.unique()}
        self.assertEqual(len(out),198);self.assertEqual(out.concentration_mg_L.isna().sum(),1)
        for r in out.itertuples():
            x=source[r.sheet].iloc[r.source_excel_row-1,r.source_excel_column-1]
            if pd.isna(x):self.assertTrue(pd.isna(r.concentration_mg_L))
            else:self.assertEqual(float(x),r.concentration_mg_L)
    def test_summary_respects_missing_repeat(self):
        d=pd.read_csv(R/'results/tables/research_enrichment/production_time_summary.csv')
        x=d[(d.sheet=='Fig. 4d')&(d.time_h==48)&(d.compound_id==10)].iloc[0]
        self.assertEqual(x['count'],2);self.assertAlmostEqual(x['mean'],6.95)
        x=d[(d.sheet=='Fig. 4d')&(d.time_h==120)&(d.compound_id==15)].iloc[0]
        self.assertAlmostEqual(x['mean'],2.8/3)
    def test_resource_units(self):
        d=pd.read_csv(R/'results/tables/research_enrichment/broth_volume_scenarios.csv')
        self.assertEqual(len(d),28)
        for r in d.itertuples():self.assertAlmostEqual(r.broth_L*r.titer_mg_L*r.overall_product_recovery,1000)
        d=pd.read_csv(R/'results/tables/research_enrichment/extraction_purity.csv')
        for r in d.itertuples():self.assertAlmostEqual(r.crude_extract_g_per_g_contained_glabridin*r.purity_wt_percent/100,1)
if __name__=='__main__':unittest.main()

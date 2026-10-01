import csv,hashlib,json,math,statistics,unittest
from collections import Counter
from datetime import datetime
from pathlib import Path
from analysis.plotting.expanded_analysis import solvent_intensity
from analysis.expanded_dashboard import load,ALL

ROOT=Path(__file__).resolve().parents[1]
class ExpandedAnalysisTests(unittest.TestCase):
    def test_complete_member_means_and_standard_deviations(self):
        _,compounds,lookup,meta=load(ROOT)
        members=json.loads((ROOT/'data/raw/skincare/expanded_references/member_predictions.json').read_text())
        self.assertEqual((len(compounds),len(lookup),len(members)),(16,288,1440))
        for c in compounds:
            for m,t in ALL:
                values=[r['value'] for r in members if (r['id'],r['model'],r['task'])==(c['id'],m,t)]
                self.assertEqual(len(values),5)
                self.assertAlmostEqual(lookup[c['id'],m,t]['mean'],statistics.mean(values),places=6)
                self.assertAlmostEqual(lookup[c['id'],m,t]['sd'],statistics.stdev(values),places=6)
    def test_fixed_panel_and_reproduced_historical_results(self):
        _,_,lookup,meta=load(ROOT)
        self.assertLess(datetime.fromisoformat(meta['panel_frozen_utc']),datetime.fromisoformat(meta['started_utc']))
        for p in meta['checkpoints']:
            self.assertEqual(len(p['sha256']),64)
        old=json.loads((ROOT/'results/tables/skincare/reference_predictions.json').read_text())
        for r in old:
            self.assertAlmostEqual(r['mean'],lookup[r['id'],r['model'],r['task']]['mean'],places=5)
        for source in meta['structure_sources']:
            self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
        self.assertIsNone(meta['safe_glabridin_concentration'])
        self.assertIsNone(meta['calibrated_low_risk_threshold'])
    def test_csv_values_keep_precision_and_do_not_drop_endpoints(self):
        _,_,lookup,_=load(ROOT)
        with (ROOT/'results/tables/skincare/expanded_comparison_long_zh.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),288)
        for r in rows:
            original=lookup[r['成分ID'],r['模型'],r['任务']]
            self.assertEqual(float(r['均值']),original['mean'])
            self.assertEqual(float(r['成员标准差']),original['sd'])
    def test_environmental_points_keep_source_values_and_flags(self):
        def rows(p):
            with (ROOT/p).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
        data=rows('results/tables/environment/environmental_plot_data.csv')
        self.assertEqual(Counter(x['figure'] for x in data),{'environmental_fate':24,'aquatic_toxicity':18,'ecosar_screening':18})
        raw=rows('data/processed/ecosar_predictions.csv')
        for r in data:
            self.assertTrue(math.isfinite(float(r['value'])))
            if r['figure']=='ecosar_screening':
                matches=[x for x in raw if x['compound_id']==r['compound_id'] and x['QSAR Class']=='Neutral Organics' and x['Organism']+' '+x['Duration']+' '+x['Endpoint']==r['endpoint']]
                self.assertEqual(len(matches),1);x=matches[0]
                self.assertEqual(float(r['value']),float(x['Concentration (mg/L)']))
                self.assertIn(x['domain_flag'],r['warning'])
                if x['Flags']:self.assertIn(x['Flags'],r['warning'])
    def test_scenarios_are_conditional_and_physically_consistent(self):
        self.assertEqual(solvent_intensity(0,1),1)
        self.assertEqual(solvent_intensity(1,2),0)
        self.assertAlmostEqual(solvent_intensity(.8,2),.1)
        for r,p in [(-.1,1),(1.1,1),(.5,0),(.5,float('nan'))]:
            with self.assertRaises(ValueError):solvent_intensity(r,p)
        with (ROOT/'results/tables/environment/resource_plot_scenarios.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
        for r in rows:
            self.assertEqual(r['evidence_type'],'CONDITIONAL_NOT_MEASURED')
            expected=float(r['batch_resource_ratio'])/float(r['product_ratio']) if r['scenario']=='resource_intensity' else solvent_intensity(float(r['recovery_fraction']),float(r['product_ratio']))
            self.assertAlmostEqual(float(r['relative_intensity']),expected)
        meta=json.loads((ROOT/'results/summaries/environment_visuals.json').read_text())
        self.assertIsNone(meta['actual_resource_results'])
        self.assertFalse(meta['new_cosmetic_reference_environment_predictions'])
    def test_literature_counts_are_deduplicated_without_quality_filter(self):
        d=json.loads((ROOT/'results/tables/environment/literature_topics.json').read_text())
        self.assertEqual((d['record_count'],d['doi_count']),(20567,1397))
        self.assertFalse(d['quality_filter_applied'])
        for theme,counts in d['counts'].items():
            rows=[r for r in d['records'] if r['theme']==theme]
            self.assertEqual(len(rows),len({r['doi'] for r in rows}))
            self.assertEqual(len(rows),counts['any_match'])
            self.assertEqual(sum(r['title_match'] for r in rows),counts['title_match'])
    def test_site_contains_all_four_tables_and_new_figures(self):
        p=(ROOT/'index.html').read_text()
        self.assertEqual(p.count('data-model-row'),64)
        for key in ['model-core','model-phys','model-nr','model-sr']:self.assertIn('id="'+key+'"',p)
        self.assertEqual(p.count('src="figures/expanded_analysis/'),8)
        self.assertNotIn('figures/expanded_analysis/environment_literature.svg',p)
        self.assertNotIn('高于全部五种参照',p)
        self.assertNotIn('查看全部 17 项主要模型结果及 MapLight 对照',p)
        self.assertIn('低于 15 种参照中的 11 种',p)
        self.assertIn('高于 14 种参照',p)

if __name__=='__main__':unittest.main()

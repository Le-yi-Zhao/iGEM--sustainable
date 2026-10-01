import json
import unittest
from collections import Counter
from pathlib import Path
from analysis.models.literature_landscape import primary,reaction

ROOT=Path(__file__).resolve().parents[1]
class LiteratureContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.papers=json.loads((ROOT/'results/tables/literature_content/papers.json').read_text())
        cls.s=json.loads((ROOT/'results/summaries/literature_content.json').read_text())
        cls.flows=json.loads((ROOT/'results/tables/literature_content/sankey_flows.json').read_text())
    def test_complete_corpus_and_no_quality_filter(self):
        self.assertFalse(self.s['quality_filter_applied'])
        self.assertEqual(len(self.papers),1397)
        self.assertEqual(len({p['doi'] for p in self.papers}),1397)
        self.assertEqual(sum(p['record_count'] for p in self.papers),20567)
        self.assertEqual(sum(self.s['overlap'].values()),1397)
        for field in ('host','family','system'):self.assertEqual(sum(self.s['counts'][field].values()),1397)
    def test_sankey_flow_is_conserved_at_every_node(self):
        for a,b in [('host','family'),('family','system')]:
            flow=[r for r in self.flows if r['source_stage']==a and r['target_stage']==b]
            self.assertEqual(sum(r['value'] for r in flow),1397)
            for label,n in Counter(p[a] for p in self.papers).items():
                self.assertEqual(sum(r['value'] for r in flow if r['source']==label),n)
            for label,n in Counter(p[b] for p in self.papers).items():
                self.assertEqual(sum(r['value'] for r in flow if r['target']==label),n)
    def test_multilabel_counts_and_title_subset(self):
        for i,topic in enumerate(self.s['strategy_order']):
            self.assertEqual(self.s['cooccurrence'][i][i],self.s['counts']['strategies'][topic])
            self.assertLessEqual(self.s['counts']['title_strategies'][topic],self.s['counts']['strategies'][topic])
            for j in range(len(self.s['strategy_order'])):
                self.assertEqual(self.s['cooccurrence'][i][j],self.s['cooccurrence'][j][i])
        self.assertTrue(all(set(p['title_strategies']).issubset(p['strategies']) for p in self.papers))
        self.assertEqual(sum(p['phase_title'] for p in self.papers),16)
    def test_category_normalization_and_ties(self):
        self.assertEqual(reaction('fed-batch fermentation'),'发酵／反应器')
        self.assertEqual(reaction('cell_free'),'无细胞／分离酶')
        self.assertEqual(primary(['未标注','酵母','细菌'],lambda x:x),'多类别并列')
    def test_content_is_featured_on_site(self):
        page=(ROOT/'index.html').read_text()
        self.assertNotIn('figures/wiki_zh/literature_audit.svg',page)
        self.assertEqual(page.count('src="figures/literature_content/'),8)
        self.assertNotIn('lit-data',page)
        self.assertNotIn('assets/literature_explorer.js',page)
        self.assertIn('源表主宿主',page)
        for removed in ['保留外部生产参照','按主题查阅文献','光甘草定的研究必要性与路线依据']:
            self.assertNotIn(removed,page)
    def test_example_uses_within_study_comparator(self):
        case=json.loads((ROOT/'results/tables/literature_content/quantitative_examples.json').read_text())
        self.assertEqual(case['control'],3.4)
        self.assertEqual(case['condensate'],5)
        self.assertAlmostEqual(case['condensate']/case['control'],1.4705882352941178)
        self.assertTrue(any('35-fold' in r['fold_change_evidence'] for r in case['raw_records']))

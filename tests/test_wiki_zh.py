import csv
import json
import tempfile
import unittest
from pathlib import Path
from analysis.models.resource_scenarios import relative_intensity
from analysis.models.literature_audit import screen
from analysis.validation.link_check import run as check_links

ROOT=Path(__file__).resolve().parents[1]

class ChineseEvidenceTests(unittest.TestCase):
    def test_resource_gain_does_not_automatically_mean_savings(self):
        self.assertAlmostEqual(relative_intensity(1.1,1.2),11/12)
        self.assertEqual(relative_intensity(1.5,1.2),1.25)
        self.assertEqual(relative_intensity(2,2),1)
        for invalid in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):relative_intensity(1,invalid)
        summary=json.loads((ROOT/'results/summaries/resource_scenarios.json').read_text())
        self.assertIsNone(summary['actual_project_resource_intensity'])

    def test_screening_is_not_metric_name_based(self):
        self.assertFalse(screen({'primary_result_metric':'glabridin_titer','title_clean':'Artemisinin production'}))
        self.assertTrue(screen({'primary_result_evidence':'GLABRIDIN was detected'}))

    def test_candidate_audit_reconciles_to_source(self):
        stats=json.loads((ROOT/'results/summaries/literature_audit.json').read_text())
        rows=json.loads((ROOT/'results/tables/literature/candidate_audit.json').read_text())
        self.assertEqual(stats['source_sha256_uncompressed'],'e3d9939c72c38013e17a23867c3be71bc984613b93c065fd623b01ba12dd4314')
        self.assertEqual((stats['records'],stats['columns'],stats['unique_nonempty_doi']),(20567,551,1397))
        self.assertEqual(len(rows),stats['candidate_records'])
        self.assertEqual(len({r['doi'] for r in rows}),stats['candidate_dois'])
        self.assertEqual(sum(stats['review_categories'].values()),len(rows))
        self.assertFalse(any(r['approved_for_titer'] for r in rows))
        self.assertEqual(len({r['source_record'] for r in rows}),len(rows))
        locants=[r for r in rows if r['doi']=='10.1016/j.bbrc.2025.152143']
        self.assertEqual(len(locants),7)
        self.assertTrue(all("4" in r['evidence'] and not r['extracted_unit'] for r in locants))

    def test_chinese_site_and_full_analytical_template(self):
        page=(ROOT/'index.html').read_text()
        self.assertIn('lang="zh-CN"',page)
        self.assertNotIn('figures/skincare/',page)
        self.assertIn('等待实测',page)
        self.assertEqual([],check_links(ROOT))
        self.assertEqual([],check_links(ROOT/'wiki_export'))
        with (ROOT/'data/wetlab/metabolite_timecourse_template.csv').open() as f:
            fields=next(csv.reader(f))
        for n in (9,10,11,13,14):self.assertIn(f'compound_{n}_concentration',fields)
        self.assertIn('glabridin_concentration',fields)

if __name__=='__main__':unittest.main()

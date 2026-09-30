"""Audit the supplied extraction table without treating extracted metrics as measurements."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATTERN = re.compile(r"glabridin", re.I)

def screen(row):
    return bool(PATTERN.search(' '.join(row.get(k, '') for k in ('title_clean', 'best_canonical_product', 'primary_result_evidence'))))

def audit(source: Path, root: Path = ROOT):
    csv.field_size_limit(20_000_000)
    opener = gzip.open if source.suffix == '.gz' else open
    with opener(source, 'rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    with opener(source, 'rt', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    candidates, papers = [], defaultdict(list)
    for number, row in enumerate(rows, 1):
        doi = row['doi'].strip().lower()
        papers[doi].append(row)
        if not screen(row):
            continue
        if doi == '10.1016/j.bbrc.2025.152143':
            category = '化学位次误抽取'
            reason = '证据中的 4′ 为化合物名称位次；单位缺失，不能解释为转化率。'
        elif doi == '10.1007/s00216-011-5061-9':
            category = '分离或活性研究待回查'
            reason = '甘草分离组分与雌激素活性研究；抽取数字不能直接作为目标产物滴度。'
        else:
            category = '产物或指标映射待回查'
            reason = '论文主题、产物标注与指标存在错配风险；未核准为光甘草定生产定量证据。'
        candidates.append(dict(source_record=number, record_id=row['optimized_record_id'], doi=doi,
            title=row['title_clean'], extracted_product=row['best_canonical_product'],
            extracted_metric=row['primary_result_metric'], extracted_value=row['primary_result_value'],
            extracted_unit=row['primary_result_unit'], evidence=row['primary_result_evidence'],
            review_category=category, review_reason=reason, approved_for_titer=False))
    out = root/'results/tables/literature'
    out.mkdir(parents=True, exist_ok=True)
    (out/'candidate_audit.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with (out/'candidate_audit.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(candidates[0]), lineterminator='\n'); w.writeheader(); w.writerows(candidates)
    doi_rows = []
    for doi in sorted({r['doi'] for r in candidates}):
        subset = [r for r in candidates if r['doi'] == doi]
        doi_rows.append({'doi':doi,'title':subset[0]['title'],'candidate_records':len(subset),
                         'review_category':subset[0]['review_category'],'approved_for_titer':False})
    (out/'candidate_papers.json').write_text(json.dumps(doi_rows, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    supplement_dois = ['10.1038/s41467-026-68881-8','10.1038/s41467-026-72579-2']
    stats = {'source_sha256_uncompressed':digest, 'source_filename':source.name.removesuffix('.gz'),
             'records':len(rows),'columns':len(fields),'unique_nonempty_doi':len(set(papers)-{''}),
             'missing_doi_records':len(papers.get('',[])),
             'needs_human_review':Counter(r['needs_human_review'] for r in rows),
             'extraction_qc':Counter(r['llm_qc_status'] for r in rows),
             'metric_labels':Counter(r['primary_result_metric'] for r in rows),
             'candidate_records':len(candidates),'candidate_dois':len(doi_rows),
             'title_hit_dois':len({r['doi'] for r in candidates if PATTERN.search(r['title'])}),
             'review_categories':Counter(r['review_category'] for r in candidates),
             'approved_target_titer_records':0,
             'supplement_dois_present_in_input':{d:d in papers for d in supplement_dois},
             'screen_fields':['title_clean','best_canonical_product','primary_result_evidence'],
             'screen_regex':'glabridin (case insensitive)',
             'limitations_zh':['记录数不是论文数或独立重复数。','检索命中不是产物真实性验证。',
                 '未核准不等于原论文没有有效数据；必须回查原始表格、单位和实验条件。',
                 '该数据库不是穷尽检索，不能据此估计全球研究量或证明研究稀缺。',
                 '两篇外部补充论文单独登记，不混入原数据库计数。']}
    dest = root/'results/summaries/literature_audit.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return stats

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('source',type=Path)
    a=p.parse_args(); print(json.dumps(audit(a.source),ensure_ascii=False,indent=2))

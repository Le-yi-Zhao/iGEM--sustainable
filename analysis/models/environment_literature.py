"""One-time, content-only thematic extraction from the supplied screened database."""
import csv,gzip,hashlib,json,re
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

RULES={
 '可再生／植物资源':r'renewable|plant.based|plant biomass|agricultural (?:waste|residue)|lignocellulos|licorice root|liquorice root',
 '水与废水':r'wastewater|waste water|water consumption|water use|water footprint|aqueous effluent',
 '溶剂使用':r'solvent|ethanol extract|methanol extract|ethyl acetate extract',
 '能量与碳排放':r'energy consum|energy efficien|energy demand|electricity|carbon footprint|greenhouse gas|carbon emission',
 '废物与副产物利用':r'waste.valori|waste.utiliz|waste.utilis|by.product.valori|by.product.utiliz|by.product.utilis|waste treatment|waste stream',
 '可持续性／生命周期':r'sustainab|life.cycle assess|environmental impact|green extraction|green chemistr',
}
FIELDS=['primary_result_evidence','best_enzyme_name_evidence','best_main_product_name_evidence','best_reaction_system_type_evidence','best_llps_component_evidence','catalytic_efficiency_fold_change_evidence']
def analyze(SOURCE):
    csv.field_size_limit(20_000_000)
    titles={};evidence=defaultdict(set);n=0
    with gzip.open(SOURCE,'rt',encoding='utf-8-sig',newline='') as f:
     for row in csv.DictReader(f):
        n+=1;doi=row['doi'].strip().lower();titles.setdefault(doi,row['title_clean'])
        for k in FIELDS:
            if row.get(k,'').strip():evidence[doi].add(row[k])
    records=[];counts={}
    for theme,pattern in RULES.items():
        hits=[]
        for doi,title in sorted(titles.items()):
            title_match=bool(re.search(pattern,title,re.I));snippet=None
            for text in [title]+sorted(evidence[doi]):
                m=re.search(pattern,text,re.I)
                if m:
                    snippet=text[max(0,m.start()-100):m.end()+180];break
            if snippet is not None:
                hits.append({'doi':doi,'title':title,'title_match':title_match,'matched_snippet':snippet})
        counts[theme]={'any_match':len(hits),'title_match':sum(x['title_match'] for x in hits)}
        records.extend({'theme':theme,**x} for x in hits)
    source_hash=hashlib.sha256()
    with gzip.open(SOURCE,'rb') as f:
     for block in iter(lambda:f.read(1024*1024),b''):source_hash.update(block)
    doc={'source_sha256_uncompressed':source_hash.hexdigest(),'record_count':n,'doi_count':len(titles),'quality_filter_applied':False,
     'text_fields':['title_clean']+FIELDS,'rules':RULES,'counts':counts,'records':records,
     'interpretation':'Counts are DOI-level mentions in available title/extracted evidence text, not exhaustive fulltext searches or measured environmental benefits. Topics overlap.'}
    out=ROOT/'results/tables/environment/literature_topics.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'records':n,'papers':len(titles),'counts':counts},ensure_ascii=False,indent=2))

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("source",type=Path);analyze(p.parse_args().source)

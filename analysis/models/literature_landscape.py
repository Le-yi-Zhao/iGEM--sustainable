"""Content analysis of the complete supplied literature corpus, without QC filtering."""
import csv,gzip,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FAMILIES={'flavonoid':'黄酮类','isoflavonoid':'异黄酮类','prenylflavonoid':'异戊烯基黄酮',
 'isoprenoid':'萜类／异戊二烯类','terpenoid':'萜类／异戊二烯类','stilbene':'芪类',
 'phenylpropanoid':'苯丙素类','natural_product':'其他天然产物','llps_system':'凝聚体相关体系',
 'other':'其他研究对象','unknown':'未标注'}
HOSTS={'yeast':'酵母','bacteria':'细菌','plant':'植物','mammalian':'哺乳动物／细胞',
 'cell_free':'无细胞体系','cyanobacteria':'蓝细菌','other':'其他宿主','unknown':'未标注'}
# Terms identify textual mentions, not experimentally established causal effects.
RULES={
 '代谢与通路工程':r'metabolic engineer|pathway engineer|pathway optim|metabolic rewiring|flux optim|rewiring.*metabol',
 '酶与蛋白工程':r'enzyme engineer|protein engineer|directed evolution|site.directed mutagen|enzyme variant|rational design|enzyme mutant|ancestral.*reconstruct',
 '前体与辅因子供给':r'precursor suppl|precursor avail|cofactor|NADPH|NADH|malonyl.CoA|DMAPP',
 '表达与动态调控':r'overexpress|promoter|dynamic regulat|dynamic control|gene dosage|copy number|transcription.factor',
 '竞争途径与转运':r'competing pathway|competitive pathway|efflux|transporter|transport engineer|metabolic burden|by.product formation',
 '空间组织与区室化':r'compartmentaliz|compartmentalis|colocaliz|co.localiz|co.localis|substrate.channel|phase.separat|biomolecular condensate|synthetic condensate|membraneless|enzyme.scaffold',
 '发酵与过程优化':r'fed.batch|bioreactor|fermentation optim|process optim|medium optim|culture.*optimi|ferment.*strateg',
 '资源与环境':r'sustainab|renewable|wastewater|waste.valori|carbon footprint|life.cycle assessment|green extraction|solvent.recycl|environmental impact'
}
PHASE=r'phase.separat|condensate|coacervat'
CHEMICAL=r'flavonoid|isoflav|prenylflav|naringenin|genistein|daidzein|quercetin|kaempferol|liquiritigenin|glabridin'
EVIDENCE_FIELDS=['primary_result_evidence','best_enzyme_name_evidence','best_main_product_name_evidence',
 'best_reaction_system_type_evidence','best_llps_component_evidence','catalytic_efficiency_fold_change_evidence']

def primary(values,mapping):
    counts=Counter(mapping(v) for v in values)
    known={k:v for k,v in counts.items() if k not in ('未标注','其他／未归类')}
    if not known:return '未标注'
    maximum=max(known.values());winners=sorted(k for k,v in known.items() if v==maximum)
    return winners[0] if len(winners)==1 else '多类别并列'

def reaction(value):
    v=value.lower().replace('_',' ').strip()
    if re.search(r'ferment|bioreactor|fed.batch|shake.flask|^batch$',v):return '发酵／反应器'
    if re.search(r'cell.free|purified enzyme|cell.lysate',v):return '无细胞／分离酶'
    if re.search(r'whole.cell|in.vivo|in.planta|cell.cultur|cell.based|callus|root.cultur|suspension.cultur',v):return '细胞／活体反应'
    if re.search(r'in.vitro|enzyme.assay|spectrophot|colorimetric',v):return '体外测定'
    return '其他／未归类'

def analyze(source:Path,root:Path=ROOT):
    csv.field_size_limit(20_000_000)
    opener=gzip.open if source.suffix=='.gz' else open
    with opener(source,'rt',encoding='utf-8-sig',newline='') as f:
        rs=list(csv.DictReader(f))
    groups=defaultdict(list)
    for i,r in enumerate(rs,1):groups[r['doi'].strip().lower()].append((i,r))
    papers=[]
    for doi,group in sorted(groups.items()):
        rows=[r for _,r in group]
        title=Counter(r['title_clean'] for r in rows).most_common(1)[0][0]
        snippets=list(dict.fromkeys(r.get(k,'').replace('\x00',' ') for r in rows for k in EVIDENCE_FIELDS if r.get(k,'').strip()))
        text=title+'\n'+'\n'.join(snippets)
        tags=[name for name,pattern in RULES.items() if re.search(pattern,text,re.I)]
        title_tags=[name for name,pattern in RULES.items() if re.search(pattern,title,re.I)]
        matched={name:next((s[:700] for s in [title]+snippets if re.search(RULES[name],s,re.I)), '') for name in tags}
        family=primary([r['best_product_family'] for r in rows],lambda v:FAMILIES.get(v.strip(),'未标注'))
        host=primary([r['best_host_group'] for r in rows],lambda v:HOSTS.get(v.strip(),'未标注'))
        system=primary([r['best_reaction_system_type_value'] for r in rows],reaction)
        phase_title=bool(re.search(PHASE,title,re.I))
        if phase_title:
            if re.search(r'biosynth|amino.acid production',title,re.I):phase_class='生物合成应用'
            elif re.search(r'engineer|designer|toolkit|biotechnology',title,re.I):phase_class='工程平台与方法'
            elif re.search(r'drug delivery|protocell',title,re.I):phase_class='递送与仿生材料'
            else:phase_class='细胞机制与疾病'
        else:phase_class='非标题相分离主题'
        papers.append(dict(doi=doi,title=title,host=host,family=family,system=system,record_count=len(rows),
            source_record_ids=[i for i,_ in group],strategies=tags,title_strategies=title_tags,matched_evidence=matched,
            flavonoid_related=family in ('黄酮类','异黄酮类','异戊烯基黄酮') or bool(re.search(CHEMICAL,title,re.I)),
            yeast_related=any(r['best_host_group']=='yeast' for r in rows),
            spatial_related='空间组织与区室化' in tags,phase_title=phase_title,phase_class=phase_class,
            glabridin_title=bool(re.search('glabridin',title,re.I))))
    n=len(papers)
    counts={f:dict(Counter(p[f] for p in papers).most_common()) for f in ['host','family','system','phase_class']}
    counts['strategies']={t:sum(t in p['strategies'] for p in papers) for t in RULES}
    counts['title_strategies']={t:sum(t in p['title_strategies'] for p in papers) for t in RULES}
    overlap=Counter(''.join('1' if p[k] else '0' for k in ['flavonoid_related','yeast_related','spatial_related']) for p in papers)
    flows=[]
    for left,right in [('host','family'),('family','system')]:
        for (a,b),v in Counter((p[left],p[right]) for p in papers).items():flows.append(dict(source_stage=left,target_stage=right,source=a,target=b,value=v))
    summary={'n_papers':n,'n_records':len(rs),'quality_filter_applied':False,'unit_zh':'不同 DOI 对应的文献条目',
        'counts':counts,'overlap':dict(overlap),'phase_title_n':sum(p['phase_title'] for p in papers),
        'glabridin_title_n':sum(p['glabridin_title'] for p in papers),
        'flow_totals':{f'{a}->{b}':sum(r['value'] for r in flows if r['source_stage']==a and r['target_stage']==b) for a,b in [('host','family'),('family','system')]},
        'cooccurrence':[[sum(a in p['strategies'] and b in p['strategies'] for p in papers) for b in RULES] for a in RULES],
        'strategy_order':list(RULES),
        'rules':RULES,'evidence_fields':EVIDENCE_FIELDS,
        'method_zh':['纳入完整输入表，不按质量分数、人工复核标记或上一轮候选清单过滤。',
          '同一 DOI 归为一篇条目；桑基图使用每篇的源表主标签，统一类别后取非缺失记录众数，并列单列。',
          '主题命中按 DOI 计一次，允许一篇有多个主题；共现表示同篇提及，不表示两个方法联用或有效。',
          '主题分为标题命中与标题加已抽取证据句命中；后者也可能包含背景或引文。',
          '比例仅描述这个项目收集的语料，不代表全球文献比例。没有可靠年份字段，未从 DOI 字符串推断年度趋势。',
          '元数据类别用于研究布局描述，不对不同产物、单位和工艺的滴度作合并平均。']}
    out=root/'results/tables/literature_content';out.mkdir(parents=True,exist_ok=True)
    cases=[]
    case_dois={'10.1016/j.jcou.2025.103269','10.1016/j.enzmictec.2026.110928','10.1186/s12934-025-02773-2'}
    for i,r in enumerate(rs,1):
        if r['doi'].strip().lower() in case_dois and (r['doi'].strip().lower()=='10.1016/j.jcou.2025.103269' or re.search(r'120\.3|50 g/L',r['primary_result_evidence'],re.I)):
            cases.append({'source_record':i,'doi':r['doi'],'evidence':r['primary_result_evidence'],
                'fold_change_evidence':r['catalytic_efficiency_fold_change_evidence'],
                'extracted_metric':r['primary_result_metric'],'extracted_value':r['primary_result_value'],'extracted_unit':r['primary_result_unit']})
    glycine='\n'.join(r['evidence'] for r in cases if r['doi'].lower()=='10.1016/j.jcou.2025.103269')
    example={'doi':'10.1016/j.jcou.2025.103269','product_zh':'甘氨酸','time_h':1,'unit':'mmol/L',
        'control':float(re.search(r'control group \(([\d.]+) mM\)',glycine).group(1)),
        'condensate':float(re.search(r'gave rise to ([\d.]+) mM glycine in 1 h',glycine).group(1)),
        'raw_records':cases,'interpretation_zh':'同研究的 1 小时浓度比较；其他路径的 35 倍结果不用于相分离单因素增益。'}
    (out/'quantitative_examples.json').write_text(json.dumps(example,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name,data in [('papers',papers),('sankey_flows',flows)]:
        (out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/'paper_landscape.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['doi','title','host','family','system','record_count','strategies','title_strategies','phase_class']
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
        for p in papers:w.writerow({k:'；'.join(p[k]) if isinstance(p[k],list) else p[k] for k in fields})
    (root/'results/summaries/literature_content.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k in ['n_papers','counts','overlap','phase_title_n','glabridin_title_n']},ensure_ascii=False,indent=2))
    return summary

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args();analyze(a.source)

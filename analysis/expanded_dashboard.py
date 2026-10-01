"""Chinese tables and website sections for the frozen expanded cosmetic panel."""
import csv
import hashlib
import html
import json
import re
from pathlib import Path
from analysis.plotting.wiki_zh import TASKS

CORE=[('ADMET-AI','Skin_Reaction'),('ADMET-AI','AMES'),('ADMET-AI','Carcinogens_Lagunin'),('MapLight','AMES')]
PHYS=[('ADMET-AI','Lipophilicity_AstraZeneca'),('ADMET-AI','Solubility_AqSolDB')]
NR=[('ADMET-AI',t) for t in TASKS if t.startswith('NR-')]
SR=[('ADMET-AI',t) for t in TASKS if t.startswith('SR-')]
ALL=CORE+PHYS+NR+SR
esc=lambda s:html.escape(str(s))

def load(root):
    panel=json.loads((root/'data/compounds/skincare_reference_panel_expanded.json').read_text())
    data=json.loads((root/'results/tables/skincare/expanded_reference_predictions.json').read_text())
    meta=json.loads((root/'data/raw/skincare/expanded_references/run_metadata.json').read_text())
    assert meta['panel_sha256']==hashlib.sha256((root/'data/compounds/skincare_reference_panel_expanded.json').read_bytes()).hexdigest()
    compounds=[{'id':'glabridin','name':'Glabridin','name_zh':'光甘草定','group_zh':'研究对象','cas':'59870-68-7'}]+panel['references']
    lookup={(r['id'],r['model'],r['task']):r for r in data}
    assert len(lookup)==len(compounds)*18==len(data)
    return panel,compounds,lookup,meta

def run(root):
    panel,compounds,lookup,meta=load(root)
    out=root/'results/tables/skincare'
    long=[];wide=[]
    for c in compounds:
        w={'成分':c['name_zh'],'用途组':c['group_zh'],'CAS':c['cas']}
        for m,t in ALL:
            r=lookup[c['id'],m,t]
            unit='模型原生回归值' if t.startswith('Lipophilicity') else 'log10(mol/L)' if t.startswith('Solubility') else '0–1模型分数'
            long.append({'成分':c['name_zh'],'成分ID':c['id'],'用途组':c['group_zh'],'模型':m,'任务':t,'中文解释':TASKS[t],
                '输出类型或单位':unit,'均值':r['mean'],'成员标准差':r['sd'],'成员数':r['n_members'],'证据类型':'结构预测'})
            for key,field in [('均值','mean'),('标准差','sd')]:w[f'{m}｜{t}｜{key}']=r[field]
        wide.append(w)
    for name,rows in [('expanded_comparison_long_zh.csv',long),('expanded_comparison_wide_zh.csv',wide)]:
        with (out/name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    s={'reference_count':len(compounds)-1,'compound_count':len(compounds),'output_count':len(long),
       'member_count':meta['member_prediction_rows'],'fresh_inference_host':meta['execution_host'],
       'comparisons':{},'actual_resource_results':None,'safe_glabridin_concentration':None}
    for m,t in ALL:
        g=lookup['glabridin',m,t]['mean'];vals=[lookup[c['id'],m,t]['mean'] for c in compounds[1:]]
        s['comparisons'][m+'|'+t]={'target':g,'reference_min':min(vals),'reference_max':max(vals),
            'reference_scores_above_target':sum(v>g for v in vals),'reference_scores_below_target':sum(v<g for v in vals)}
    (root/'results/summaries/expanded_comparison.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
    return s

def fig(name,caption):
    return f'<figure class="figure"><a href="figures/expanded_analysis/{name}.png"><img loading="lazy" src="figures/expanded_analysis/{name}.svg" alt="{esc(caption)}"></a><figcaption>{esc(caption)}</figcaption></figure>'

def matrix(compounds,lookup,tasks,title,key):
    body=f'<h3>{esc(title)}</h3><div class="table-wrap model-scroll" tabindex="0" role="region" aria-label="{esc(title)}，可横向滚动"><table class="model-matrix" id="{key}"><thead><tr><th scope="col">成分与用途</th>'
    for m,t in tasks:body+=f'<th scope="col">{esc(TASKS[t])}<small>{esc(m)} · {esc(t)}</small></th>'
    body+='</tr></thead><tbody>'
    for c in compounds:
        target=c['id']=='glabridin'
        body+=f'<tr data-model-row data-id="{c["id"]}" data-group="{esc(c["group_zh"])}" data-search="{esc(c["name_zh"]+" "+c["name"]+" "+c["cas"])}" class="{"target-row" if target else ""}"><th scope="row">{esc(c["name_zh"])}<small>{esc(c["group_zh"])}</small></th>'
        for m,t in tasks:
            r=lookup[c['id'],m,t]
            body+=f'<td title="均值 {r["mean"]:.8f}；成员标准差 {r["sd"]:.8f}"><b>{r["mean"]:.3f}</b><span class="model-sd"> ± {r["sd"]:.3f}</span></td>'
        body+='</tr>'
    return body+'</tbody></table></div>'

def render_models(root,old):
    panel,c,lookup,meta=load(root)
    s=json.loads((root/'results/summaries/expanded_comparison.json').read_text())
    carc=s['comparisons']['ADMET-AI|Carcinogens_Lagunin'];skin=s['comparisons']['ADMET-AI|Skin_Reaction']
    body='''<section class="section" id="models"><div class="kicker">03 / 护肤模型</div><h2>光甘草定与 15 种护肤成分：同一模型，逐项比较</h2><p class="lead">保留原有五种参照，新增十种常见成分。名单在新一轮预测前固定，并已在 Matvision 实际运行 ADMET-AI 的 17 项护肤相关任务与 MapLight 的细菌回复突变任务。</p><div class="comparison-stats"><span><b>16</b>种分子</span><span><b>18</b>项模型／任务组合</span><span><b>288</b>项汇总结果</span><span><b>1,440</b>项成员输出</span></div>'''
    body+=f'''<p><b>支持继续开发的线索：</b>光甘草定的 ADMET-AI 致癌性筛查分数为 {carc['target']:.3f}，低于 15 种参照中的 {carc['reference_scores_above_target']} 种；两套细菌回复突变预测均落在本组参照分数范围内。<b>需要优先验证的方面：</b>皮肤反应／致敏分数 {skin['target']:.3f}，高于 {skin['reference_scores_below_target']} 种参照，并保留受体及细胞应答信号。这些是各终点的模型观察，不能合成为“整体安全排名”。</p>'''
    body+='''<p>用途分组让比较更有解释力：提亮与抗氧化原料提供活性成分背景；保湿调理、酸类和其他活性展示日常配方的成分范围。甘油等并非与光甘草定等功效的替代品，也不是标准阴性对照。全部结果均为结构预测，未输入添加量、配方或经皮暴露。</p><div class="model-controls"><label>按用途查看<select id="model-group"><option value="全部">全部成分</option>'''
    for group in dict.fromkeys(x['group_zh'] for x in c[1:]):body+=f'<option value="{esc(group)}">{esc(group)}</option>'
    body+='''</select></label><label>查找成分<input id="model-search" placeholder="中文、英文或 CAS" type="search"></label><label class="check-label"><input id="model-show-sd" type="checkbox" checked>显示成员标准差</label><button id="model-reset" type="button">重置筛选</button></div><p id="model-count" aria-live="polite">当前显示 15 种参照，光甘草定固定保留。</p><p class="table-help">每个数值为五成员均值 ± 标准差；仅在同一列比较。标准差表示模型成员差异，不是生物重复或人体风险置信区间。小屏幕可在表格内横向滑动。</p>'''
    body+=matrix(c,lookup,CORE,'表 1｜主要危害筛查','model-core')
    body+='<p>这四列是阳性类别模型分数，数值高低不等于真实人体发生率；没有通用安全分界线，0.5 也不是护肤品安全线。</p>'
    body+=matrix(c,lookup,PHYS,'表 2｜配方相关性质','model-phys')
    body+='<p>这两项为回归预测：亲脂性保留原数据集定义；水溶解度为 log10(mol/L)，数值更负表示预测溶解度更低。两者均不按毒性分数解读。</p>'
    body+=matrix(c,lookup,NR,'表 3｜七项受体与酶活性信号','model-nr')
    body+=matrix(c,lookup,SR,'表 4｜五项细胞应答信号','model-sr')
    body+='<p>表 3、4 表示特定试验中的活性信号；不能直接认定人体内分泌干扰、致癌或美白功效。完整保留所有预选任务，不按结果删列。</p>'
    body+=fig('expanded_core','16 种成分的四项主要筛查结果。固定原料顺序，误差线为五成员标准差；不设置安全线。')
    body+=fig('expanded_mechanisms','全部十二项机理任务，颜色仅编码各列模型分数。用途分组不代表安全等级。')
    body+='<div class="downloads"><a href="results/tables/skincare/expanded_comparison_wide_zh.csv">下载中文横向比较表</a><a href="results/tables/skincare/expanded_comparison_long_zh.csv">下载中文完整明细表</a><a href="results/tables/skincare/expanded_reference_predictions.json">288 项原始精度输出</a><a href="data/raw/skincare/expanded_references/run_metadata.json">本轮运行记录</a></div>'
    body+='<details><summary>15 种参照的用途、分子身份和安全资料</summary><div class="table-wrap"><table><thead><tr><th>成分／CAS</th><th>用途组</th><th>评估条件与来源</th></tr></thead><tbody>'
    for r in panel['references']:
        sources='；'.join(f'<a href="{esc(panel["sources"][k]["url"])}">{esc(panel["sources"][k]["title"])}</a>' for k in r['source_ids'])
        body+=f'<tr><td>{esc(r["name_zh"])}<br>{r["cas"]}</td><td>{r["group_zh"]}</td><td>{esc(r["evidence_summary_zh"])}<br>{sources}</td></tr>'
    body+='</tbody></table></div><p>评估或历史使用浓度不是光甘草定的安全浓度，也不替代目标市场的成品评估。水杨酸 2023 意见还指出眼刺激及儿童暴露问题，不能将其视为无条件安全参照。α／β 熊果苷结构分别保留；MapLight 特征相同不代表生物学等效。</p></details>'
    names={x['id']:x['name_zh'] for x in c}
    overlaps=[]
    for a in meta['membership_audit']:
        if 'split' in a:overlaps.append(('训练／验证集' if a['split']=='train_val' else '测试集')+'：'+'、'.join(names[x] for x in a['overlapping_ids_connectivity']))
    body+='<details><summary>如何复现，以及参照组的适用边界</summary><p>本轮复用原有模型检查点，未重新训练或调整阈值。光甘草定与原结果的最大差异小于 0.000001。MapLight 数据重叠按去除立体信息后的连接结构核查：'+esc('；'.join(overlaps))+'。ADMET-AI 训练重叠未完整核实；本组不是独立验证集。</p><p>新增参照尚未运行 ADMETlab、admetSAR、VEGA、ECOSAR 或 ProTox，眼刺激和光毒性参照比较仍缺失。下载表中没有将缺失结果填成阴性。</p><p><a href="data/compounds/skincare_reference_panel_expanded.json">预测前固定的参照名单</a> · <a href="data/raw/skincare/expanded_references/member_predictions.json">1,440 项成员输出</a></p></details>'
    # Preserve the already checked cross-platform and atomic-interpretation explanations.
    start=old.index('<figure class="figure"><a href="figures/wiki_zh/platform_comparison.png"')
    end=old.index('<figure class="figure"><a href="figures/wiki_zh/mechanistic_signals.png"')
    body+='<h3>光甘草定的其他平台结果与原子解释</h3>'+old[start:end]
    return body+'</section>'

def render_environment(root,old):
    head='''<section class="section" id="environment"><div class="kicker">04 / 环境与资源</div><h2>把生产价值落实到可检验的环境与资源指标</h2><p class="lead">光甘草定的开发价值可以从“可生产、可回收、单位产物少消耗资源”三个方向验证。下面区分既有模型预测和条件计算；目前没有用假设图代替项目实测结果。</p>'''
    head+='<h3>已有预测｜先看生产路径中的分子会去哪里</h3><p>以下三图使用已完成的 VEGA、EPI Suite 与 ECOSAR 导出数据，覆盖光甘草定和五个路径相关化合物；这些化合物不是已检出的排放物，也不是上面的 15 种护肤参照。</p>'
    head+=fig('environmental_fate','EPI Suite 预测的亲脂性、水溶解度、生物富集及降解模型分数。每个小图使用自己的单位；水溶解度和富集因子使用对数坐标。未导出正式适用域。')
    head+=fig('aquatic_toxicity','VEGA 水生急性毒性筛查。仅在同一小图内比较，浓度越低表示模型预测效应越强。颜色标注原报告可靠性；藻类报告均有分子量相关警告，不据此设排放限值。')
    head+=fig('ecosar_screening','ECOSAR 中性有机物类别的淡水急性终点。叉号保留原始标志；未触发亲脂性上限也不等于已通过完整适用域检验。水蚤 LC50 与 VEGA 的 EC50 不合并。')
    head+='<p><b>路径比较带来的开发线索：</b>在同一套 EPI Suite 预测中，光甘草定的亲脂性和生物富集因子低于后段化合物 10、11、14，水溶解度则较高；早段化合物 9、13 的预测富集因子更低。因此，推进末端转化并同步测量中间体残留是可检验的工艺方向，不能仅凭目标产物增加就认定排放更安全。</p>'
    # Reuse checked target-specific discussion and functional-unit definition.
    start=old.index('<div class="table-wrap">')
    body=head+old[start:old.rfind('</section>')]
    body+='<h3>新增资源图｜把优势主张变成实验目标</h3>'
    body+=fig('resource_sensitivity','条件计算：纯产物增加多少，才能抵消批次资源增加？每条曲线代表一个假设资源消耗比，可分别用于水、溶剂或电耗，不能跨单位相加。')
    body+=fig('solvent_recovery','理想化稳态情景：在批次总溶剂需求不变、回收液满足复用要求时，计算新鲜溶剂需求。未计回收能耗、纯化损失或启动库存，不能解释为实际净减排。')
    body+=fig('production_boundary','项目资源核算边界与数据流。箭头表示应追踪的流程，不表示已测质量或能量流量。纯产物、回收流和处理负担须同步记录。')
    body+='<p><b>有了这些实测结果后的效果：</b>匹配组纯产物质量与材料清单可以生成单位产物水耗、溶剂耗和材料投入强度图；电表数据与回收记录可以检验是否存在能耗转移；废物流浓度与处理前后数据可以评估排放控制。只有同一功能单位、同一边界的比较，才能支持具体的“节约多少”。</p><div class="downloads"><a href="results/tables/environment/environmental_plot_data.csv">环境图逐点数据及警告</a><a href="results/tables/environment/resource_plot_scenarios.csv">资源情景图数据</a><a href="results/summaries/environment_visuals.json">图表范围与公式</a></div></section>'
    return body

def integrate(root,page):
    for key,renderer in [('models',render_models),('environment',render_environment)]:
        pattern=f'<section class="section" id="{key}">.*?</section>'
        page=re.sub(pattern,lambda m:renderer(root,m.group()),page,flags=re.S)
    page=page.replace('</head>','<link rel="stylesheet" href="assets/expanded_analysis.css"><script defer src="assets/model_tables.js"></script></head>')
    page=page.replace('光甘草定与原结果的最大差异小于 0.000001。','原光甘草定输出复现一致（最大差异小于 0.000001）。')
    page=page.replace('<a href="results/tables/skincare/reference_predictions.json">完整参照模型结果</a>','<a href="results/tables/skincare/expanded_comparison_wide_zh.csv">16 种成分中文比较表</a><a href="results/tables/skincare/expanded_reference_predictions.json">288 项完整参照结果</a><a href="results/tables/skincare/reference_predictions.json">原五种参照历史结果</a>')
    page=page.replace('本轮继续完成的是数据分析和实验设计。模型记录来自已实际执行并保存的运行；本次重建页面读取这些结果，没有把读取缓存写成重新运行模型，也没有把实验计划写成湿实验完成。','本轮已在 Matvision 为 16 种分子实际运行 ADMET-AI／MapLight，新增中文比较表和七张环境与资源图。文献分析覆盖全部 1,397 篇；其他平台读取既有已保存结果，湿实验仍等待实测。')
    return page

"""Build the Chinese GALATEA wiki from audited evidence and explicit missing-data states."""
import csv
import html
import json
import shutil
from pathlib import Path
from analysis.plotting.wiki_zh import NAMES, TASKS

ROOT=Path(__file__).resolve().parents[1]
def esc(v):return html.escape(str(v if v is not None else ''))
def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def csv_rows(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def table(rows,columns):
    return '<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+esc(label)+'</th>' for _,label in columns)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(r.get(k,''))+'</td>' for k,_ in columns)+'</tr>' for r in rows)+'</tbody></table></div>'
def figure(name,caption):
    return f'<figure class="figure"><a href="figures/wiki_zh/{name}.png"><img loading="lazy" src="figures/wiki_zh/{name}.svg" alt="{esc(caption)}"></a><figcaption>{caption}</figcaption></figure>'
def link(path,label):return f'<a href="{esc(path)}">{esc(label)}</a>'

def build():
    audit=load('results/summaries/literature_audit.json')
    plan=load('data/experiment_plan_zh.json')
    benchmarks=load('data/literature/verified_benchmarks.json')['records']
    refs=load('data/compounds/skincare_reference_panel.json')
    preds=load('results/tables/skincare/reference_predictions.json')
    nav=[('overview','项目与证据'),('literature','文献挖掘'),('models','护肤模型'),('environment','环境与资源'),('experiments','实验与所需结果'),('interviews','访谈与反馈'),('conclusion','当前结论'),('downloads','数据与复现')]
    body='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="GALATEA 光甘草定项目：文献证据、护肤模型、实验计划与可持续性评价"><title>GALATEA｜光甘草定与可持续生产</title><link rel="stylesheet" href="assets/styles.css"><link rel="stylesheet" href="assets/wiki_zh.css"></head><body>
<a class="skip" href="#overview">跳转正文</a><div class="draft"><b>中文初稿 · 2026 年 9 月 30 日</b>　模型预测、文献实测、条件计算和本项目待测结果分别标注。</div>
<header class="hero"><div class="wrap"><div class="eyebrow">清华大学团队 · 国际基因工程机器大赛 · 2026</div><h1>让光甘草定的生产<br>更高效，也更可验证</h1><p>我们探索液液相分离能否改善微生物生产光甘草定，并用可追溯证据检验护肤用途、资源消耗和环境影响。</p><div class="sdgs"><span class="sdg-pill">目标 3 · 健康与福祉</span><span class="sdg-pill">目标 9 · 产业与创新</span><span class="sdg-pill">目标 12 · 负责任生产</span></div></div></header>
<div class="layout"><aside class="sidebar" aria-label="页面导航"><b>阅读导航</b>'''+''.join(link('#'+i,t) for i,t in nav)+'''</aside><main>
<section class="section" id="overview"><div class="kicker">01 / 项目与证据</div><h2>先定义要证明的改变</h2><p class="lead">核心实验比较是：低表达 OC/DMT、无相分离的基线组 G1，与相同背景的相分离组。我们希望检验生产效率是否改善，以及改善是否足以抵消额外的表达、培养和纯化负担。</p>
<div class="grid2"><article class="card"><span class="status">已完成 · 计算</span><h3>护肤相关筛查</h3><p>使用固定的五种护肤成分参照，比较同一模型、同一终点；保留跨平台分歧。</p></article><article class="card"><span class="status">已完成 · 文献</span><h3>文献研究版图</h3><p>按 1,397 篇文献分析研究对象、宿主、工程策略与相分离应用，新增八张内容图。</p></article><article class="card"><span class="status">已完成 · 条件计算</span><h3>资源收支平衡</h3><p>计算纯产物增益与资源增量之间的关系，帮助确定实验目标。</p></article><article class="card"><span class="status missing">等待实测</span><h3>生产与成品效果</h3><p>尚无本项目匹配组产率、纯度、资源清单和配方安全结果。</p></article></div>
<p>本轮继续完成的是数据分析和实验设计。模型记录来自已实际执行并保存的运行；本次重建页面读取这些结果，没有把读取缓存写成重新运行模型，也没有把实验计划写成湿实验完成。</p></section>
<section class="section" id="literature"><div class="kicker">02 / 文献挖掘</div><h2>先排除错误数字，再建立生产参照</h2>'''
    body+=f'<p class="lead">原始数据库含 {audit["records"]:,} 条记录、{audit["columns"]} 个字段和 {audit["unique_nonempty_doi"]:,} 个不同 DOI。其中 {audit["needs_human_review"]["true"]:,} 条（{100*audit["needs_human_review"]["true"]/audit["records"]:.1f}%）被源数据库标记为需要人工复核。</p>'
    body+='''<p>以标题、最终产物字段和结果证据句中的“glabridin”为候选检索条件，得到 108 条记录、18 个 DOI；仅标题命中涉及 1 个 DOI。这只是当前数据库的覆盖情况，不能推出全球只有一篇研究，也不能证明光甘草定研究总体稀少。</p>'''
    body+=figure('literature_audit','数据库审计结果。源表的“已接受”是抽取质量标签，不是人工核实或独立实验验证。')
    body+='''<div class="note"><b>关键纠错：</b>名为“光甘草定滴度／产率”的列中混有其他产物、培养基成分和化合物编号。例如，化合物名称中的 4′ 不能作为 4% 转化率；酵母提取物浓度也不是产物浓度。本轮尚未从这 108 条抽取记录中核准可直接用于光甘草定生产汇总的数值，相关记录保留并标注回查原因。</div>
<h3>补充的原始研究：可以证明可行性，不能代替我们的产量</h3><p>以下两篇论文均不在本次输入数据库中，单独作为外部补充。按生产路线和尺度分列；没有进行跨条件优劣排名或合并平均。</p>'''
    body+=table(benchmarks,[('study_zh','研究'),('route_zh','生产条件类别'),('titer_mg_l','文献滴度（mg/L）'),('use_zh','本项目如何使用')])
    body+='<p>原始来源：'+link(benchmarks[0]['url'],'生物合成网络研究（2026）')+'；'+link(benchmarks[2]['url'],'酵母模块组装研究（2026）')+'。表中滴度不是分离产物质量、质量收率或本项目生产结果。</p>'
    body+='''<h3>文献挖掘接下来回答三个问题</h3><ol><li><b>为什么值得研究：</b>整理护肤用途、作用机制与适用条件的原始证据；用途价值与安全性分别讨论。</li><li><b>生产困难在哪里：</b>按宿主、底物来源、生产尺度、分析方法和单位提取可核实结果，关注中间体泄漏与纯化负担。</li><li><b>环境影响来自哪里：</b>比较植物提取与发酵的原料、水、溶剂、能耗和废物处理边界。当前没有同一边界的清单，因此不写“发酵已经更环保”。</li></ol><p>候选筛选不是系统综述。下一轮需预先记录检索库、完整检索式、检索日期和纳排规则，补充“光甘草定／甘草／提取／发酵／溶剂／生命周期”等中英文词，并进行引用追踪和重复核查。</p></section>
<section class="section" id="models"><div class="kicker">03 / 护肤模型</div><h2>用一致的参照回答具体问题</h2><p class="lead">暂按非喷雾、留敷型面部护肤原料评价。ADMET-AI 作为主要计算框架，理由是本地五成员结果可复现、任务覆盖明确；其他平台用于补充终点和检查分歧。选择依据与结果是否有利无关。</p>
<p>保留 17 项任务：3 项主要危害、2 项配方性质和 12 项受体／细胞应答。口服吸收、血脑屏障和常规药代任务退出当前主要叙事；长期和全身效应仍需结合经皮暴露评估。参照组在比较结果前按用途、分子身份和公开安全资料确定，不因分数不利而更换。</p>'''
    body+=table(refs['references'],[('name_zh','参照成分'),('evidence_summary_zh','已有安全资料及适用边界')])
    body+='<p>资料来源：'+link(refs['sources']['SCCS_ARBUTINS_2023']['url'],'熊果苷评估')+'、'+link(refs['sources']['CIR_NIACINAMIDE_2005']['url'],'烟酰胺评估')+'、'+link(refs['sources']['CIR_ASCORBYL_GLUCOSIDE_2020']['url'],'抗坏血酸葡糖苷评估')+'、'+link(refs['sources']['SCCS_KOJIC_2022']['url'],'曲酸评估')+'。这些浓度是特定资料的使用／评估条件，不是光甘草定的安全浓度，也不是中国市场的合规结论。</p>'
    body+=figure('reference_comparison','固定参照组的主要结果。误差线为五个模型成员的标准差，不是生物学重复或人体风险置信区间。每个小图内比较；没有设置“安全线”。')
    body+='''<p><b>目前的实际结论：</b>光甘草定的 ADMET-AI 致癌性分数为 0.053，低于部分参照；细菌回复突变分数为 0.298，处于参照范围内。但皮肤反应／致敏分数为 0.755，高于全部五种参照。结果支持确定后续验证重点，不能概括为“比常见护肤成分更安全”。</p>
<div class="note"><b>参照不是无毒标准品。</b>α 与 β 熊果苷属于相关家族；MapLight 对两者使用的特征相同。烟酰胺与 MapLight 训练／验证数据存在重叠，曲酸与其测试数据存在重叠；ADMET-AI 的训练重叠尚未完整核实。因此，这组比较不构成独立外部验证。原光甘草定输出复现一致。</div>'''
    body+=figure('platform_comparison','相近终点的平台原生结果并列展示。试验定义、训练数据和校准不同，分数不能直接相加、平均或投票决定安全。')
    body+='''<h3>其他模型分别贡献了什么？</h3>'''
    others=[
      dict(model='Chemprop 原子解释',result='已解释细菌回复突变、皮肤反应和致癌性三项任务；六分子 × 三任务 × 五成员，共 90 项数值完整性检查。',meaning='显示原子特征对指定模型输出的相对贡献；不是另一份独立毒性证据，也不是因果致毒基团。'),
      dict(model='MapLight（无图神经网络版本）',result='光甘草定细菌回复突变分数 0.217，五成员标准差 0.044。使用分子指纹／描述符和 CatBoost。',meaning='补充另一种建模框架。图神经网络扩展尚未运行，不记作已完成。'),
      dict(model='ADMETlab',result='光甘草定皮肤致敏 0.851、细菌回复突变 0.715、眼刺激 0.983。',meaning='致突变判断与 ADMET-AI／MapLight 存在分歧；眼刺激应纳入验证。'),
      dict(model='admetSAR',result='光甘草定皮肤致敏 0.743、眼刺激 0.797、细菌回复突变 0.234；另有光毒、光致刺激和光过敏任务。',meaning='补充局部接触及光相关终点；三个光相关任务不能混为同一结论。'),
      dict(model='ProTox',result='致癌和致突变均报告非活性、类别置信度各 0.67；生态毒性报告活性、置信度 0.59。',meaning='置信度对应所报告类别，不能当作阳性概率；生态信号仍需暴露信息。'),
      dict(model='VEGA、EPI Suite、ECOSAR',result='提供降解、富集和水生毒性预测；多项存在适用域或结构范围限制。',meaning='用于设计排放控制与验证优先级，详见环境部分。')]
    body+=table(others,[('model','模型／工具'),('result','实际输出'),('meaning','如何解释')])
    body+='''<p>ADMET-AI 与 Chemprop 解释属于同一预测链，不能计作两个独立模型的一致证据。ADMETlab、admetSAR、ProTox、VEGA 和 EPA 工具在本次页面更新中使用已核实的既有导出结果。</p>'''
    body+=figure('atom_attribution','三项任务分别解释。红色提高、蓝色降低相对于零特征基线的模型输出；误差线为成员标准差。零特征图不是无毒参照分子，贡献不能直接解释为可删除的致毒基团。')
    body+=figure('mechanistic_signals','全部十二项机理任务均保留。绿色线段为五种参照的分数范围，不是正常范围或安全区间；高分反映特定试验活性线索。')
    body+='''<p>光甘草定在线粒体膜电位、抗氧化应答及多项受体任务上高于当前参照组。需要通过相关实验区分特定作用、细胞毒性和试验干扰；不能直接推出人体内分泌干扰或美白功效。</p><details><summary>查看全部 17 项主要模型结果及 MapLight 对照</summary>'''
    full=[{'name':NAMES[r['id']],'model':r['model'],'task':TASKS[r['task']],
           'score':f"{r['mean']:.6f}",'sd':f"{r['sd']:.6f}"} for r in preds]
    body+=table(full,[('name','化合物'),('model','模型'),('task','任务'),('score','原生输出均值'),('sd','五成员标准差')])
    body+='''<p>亲脂性和水溶解度为回归任务，不按 0–1 的阳性分数解释；水溶解度以 mol/L 为单位取对数。没有统一的低风险阈值，0.5 也不是护肤品安全线。</p></details><p>评价范围参考 '''+link('https://health.ec.europa.eu/publications/sccs-notes-guidance-testing-cosmetic-ingredients-and-their-safety-evaluation-12th-revision_en','化妆品原料安全评价指南')+' 与 '+link('https://www.oecd.org/en/publications/guideline-no-497-defined-approaches-on-skin-sensitisation_b92879a4-en.html','皮肤致敏整合评价方法')+'。</p></section>'
    body+='''<section class="section" id="environment"><div class="kicker">04 / 环境与资源</div><h2>环境危害与生产效率分别检验</h2><p class="lead">护肤品使用后的污水路径，以及生产中的溶剂、残余产物和活菌处理，都需要纳入讨论。原料来自微生物，并不自动意味着更容易降解或更少环境负担。</p>'''
    env=[
      {'topic':'降解','result':'VEGA：不易快速生物降解，适用域为中等。','use':'保留难降解关注；不能把模型类别换算成实际环境半衰期。'},
      {'topic':'生物富集','result':'EPI Suite 生物富集因子约 1,542 L/kg 湿重；VEGA 多项富集结果适用域较低。','use':'是筛查预测，不与不同方法的生物积累因子取平均。'},
      {'topic':'水生毒性','result':'VEGA 预测藻类半数效应浓度 1.34 mg/L，水蚤 2.48 mg/L，鱼类半数致死浓度 2.54 mg/L。','use':'藻类与鱼类结果适用域较低，水蚤为中等；不同物种和试验终点不能直接排名。'},
      {'topic':'类别与范围警告','result':'ECOSAR 中性有机物类别鱼类 96 小时半数致死浓度约 0.268 mg/L，但超过该模型的亲脂性适用范围。','use':'保留原始警告，不据此设排放限值；多类别输出不平均。'},
      {'topic':'实际环境风险','result':'尚无项目排放浓度、处理去除率及受纳水体暴露数据。','use':'不能计算可靠风险商，也不能宣称实际水环境安全。'}]
    body+=table(env,[('topic','问题'),('result','已有结果'),('use','结论边界')])
    body+='<p>方法来源：'+link('https://www.epa.gov/tsca-screening-tools/epi-suitetm-estimation-program-interface','美国环保署环境归趋筛查工具')+'、'+link('https://www.epa.gov/tsca-screening-tools/ecological-structure-activity-relationships-ecosar-predictive-model','美国环保署水生毒性模型')+'。</p>'
    body+='''<h3>缺少产率时，先计算资源收支平衡条件</h3><p>统一功能单位为 <b>1 g 经纯度校正的分离光甘草定</b>。先匹配培养、分离纯化和废物处理边界；上游原料与设备制造尚未纳入，所以当前不是完整生命周期评价。</p><div class="formula">单位产物资源强度比 = 批次资源消耗比 ÷ 纯产物质量比</div><p>纯产物质量 = 分离样品质量 × 光甘草定质量分数。若已经使用分离后的质量，不再重复乘回收率。水、溶剂、总投入质量、电耗和成本分别计算，只有相同单位的数值才可相比。</p>'''
    body+=figure('resource_break_even','明确标注为条件计算：绿色表示单位纯产物资源下降，棕色表示上升。图中没有项目实测点。')
    body+='''<p>举例：如果纯产物质量提高 20%，某项批次资源只增加 10%，则该项单位产物资源减少 8.3%。如果产物提高 20%、资源增加 50%，强度反而提高 25%。这两者都是假设情景，不能写成实验节约量。</p><div class="note">尚无项目实测材料投入强度、电耗、成本或碳排放结果。投入质量核算须包含水和溶剂，体积转换质量需要密度及来源；实际电表与额定功率估算分列。碳排放还需要地域、时间和边界一致的排放因子。</div></section>
<section class="section" id="experiments"><div class="kicker">05 / 实验与所需结果</div><h2>每项结果都对应一个可检验的结论</h2><p class="lead">先取得可信的身份、定量、匹配组生产结果及纯化清单，再决定是否扩大验证。下表是下一阶段的工作清单，不是已完成的实验记录。</p>'''
    for item in plan:
        body+=f'<article class="experiment"><span class="priority">{esc(item["priority"])}</span><h3>{esc(item["topic"])}</h3><dl><dt>需要什么</dt><dd>{esc(item["required"])}</dd><dt>展示什么</dt><dd>{esc(item["figure"])}</dd><dt>能够说明什么</dt><dd>{esc(item["effect"])}</dd><dt>结论边界</dt><dd>{esc(item["limit"])}</dd></dl></article>'
    body+='''<p>时间序列模板已补入化合物 13，避免只记录部分中间体而遗漏关键节点。正式采样时间和重复数应由先导数据、测定灵敏度与功效分析确定，不凭空生成拟合曲线或显著性。</p></section>
<section class="section" id="interviews"><div class="kicker">06 / 访谈与反馈</div><h2>把意见变成可追踪的设计修改</h2><p>当前收到的是讨论截图，尚未收到提到的三份访谈原文。截图提出的“一致护肤成分参照”和“补充环境视角”已进入本轮设计。展示重点依据用途和证据质量确定；不利指标及模型分歧保留。</p><p>待取得原文后，逐条登记受访者角色、匿名标识、时间、问题、原文定位、引用许可、主题代码、建议的设计修改和验证方式。区分受访者原话与团队解释，通过复核和回访检查修改是否回应了原始关切。</p></section>
<section class="section" id="conclusion"><div class="kicker">07 / 当前结论</div><h2>现阶段能够写进项目结论的内容</h2><p><b>技术可行性：</b>已有外部文献支持酵母合成光甘草定，本项目可以据此建立分析与生产比较；相分离带来的改进仍待匹配实验验证。</p><p><b>护肤用途：</b>已完成多模型筛查和固定参照比较。部分分数相对较低，但致敏、眼刺激及机理信号提示后续重点；目前不足以证明光甘草定比参照更安全或确定安全添加浓度。</p><p><b>可持续性：</b>已明确单位纯产物的资源比较方法和收支平衡条件。只有实际生产增益超过对应资源增量，且排放得到验证，才能支持具体的效率或环境改善结论。</p><p><b>下一次更新：</b>优先接入身份确认、匹配组生产重复和纯化／资源记录；有了这些数据，才能将条件图替换为带不确定性的实测比较图。</p></section>
<section class="section" id="downloads"><div class="kicker">08 / 数据与复现</div><h2>从页面结论回到原始证据</h2><p>图表中的模型名称、化合物编号和计量单位保留标准写法。下载的原始模型字段保留平台标识，中文解释见本页及说明文件。原始文献数据库保留校验值，审计结果另存，未覆盖源文件。</p><div class="downloads">'''
    downloads=[('docs/methodology/wiki_zh_20260930.md','中文初稿与实验结果清单'),('results/tables/literature/candidate_audit.csv','108 条候选的核查记录'),('results/summaries/literature_audit.json','数据库统计与校验'),('data/literature/verified_benchmarks.json','外部文献生产参照'),('results/tables/skincare/reference_predictions.json','完整参照模型结果'),('results/tables/skincare/evidence.csv','各模型选定输出'),('results/tables/skincare/chemprop_atom_attribution.csv','原子归因数据'),('results/tables/skincare/chemprop_attribution_completeness.csv','原子解释的数值检查'),('data/processed/episuite_predictions.csv','环境归趋预测'),('data/processed/ecosar_predictions.csv','水生毒性及原始警告'),('results/tables/resource_scenarios.csv','资源条件计算数据'),('data/wetlab/metabolite_timecourse_template.csv','代谢物时间序列模板'),('data/wetlab/batch_summary_template.csv','批次产物与纯化模板'),('data/wetlab/material_inventory_template.csv','材料投入模板'),('data/wetlab/equipment_usage_template.csv','设备与电耗模板'),('data/wetlab/cost_inventory_template.csv','成本模板'),('data/wetlab/containment_template.csv','处理与控制模板'),('data/skincare_exposure.csv','配方暴露信息模板')]
    body+=''.join(link(p,t) for p,t in downloads)
    body+='''</div><p>复现入口：以下命令读取已保存预测、重算派生表格及中文图表，并检查页面链接。完整文献审计可通过独立脚本及原始文件复算，页面默认重建不要求下载 154 MB 的源数据库。</p><pre><code>python analysis/run_all.py</code></pre></section></main></div><footer><b>GALATEA｜光甘草定与可持续生产</b><br>数据截至 2026 年 9 月 30 日 · 缺失结果保持缺失，推断范围随证据更新。</footer></body></html>'''
    import re
    from analysis.literature_section import render as render_literature
    body=re.sub(r'<section class="section" id="literature">.*?</section>',lambda _:render_literature(ROOT,table),body,flags=re.S)
    from analysis.expanded_dashboard import integrate
    body=integrate(ROOT,body)
    from analysis.enrichment_section import integrate as enrich
    body=enrich(ROOT,body)
    from analysis.plotting.model_validation import integrate as add_validation
    body=add_validation(ROOT,body)
    from analysis.plotting.opera_analysis import integrate as add_opera
    body=add_opera(ROOT,body)
    from analysis.human_practices import integrate as add_interview
    body=add_interview(ROOT,body)
    index=ROOT/'index.html'; index.write_text(body,encoding='utf-8');return index

def export_wiki():
    destination=ROOT/'wiki_export'
    if destination.exists():shutil.rmtree(destination)
    destination.mkdir()
    shutil.copy2(ROOT/'index.html',destination/'index.html')
    for directory in ['assets','figures/human_practices','data/human_practices','figures/research_enrichment','figures/expanded_analysis','figures/wiki_zh','figures/literature_content','figures/evidence','figures/supporting','figures/framework','figures/skincare',
        'analysis/adapters','analysis/models','results/tables','results/summaries','data/literature','data/wetlab',
        'data/raw/admet_ai','data/raw/skincare','data/raw/admetlab','data/raw/chemprop','data/raw/vega','data/raw/episuite',
        'data/raw/admetsar','data/raw/ecosar','data/raw/protox','data/raw/maplight',
        'data/processed','docs/methodology','docs/provenance','docs/limitations']:
        shutil.copytree(ROOT/directory,destination/directory,dirs_exist_ok=True)
    (destination/'data/compounds').mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'data/compounds/skincare_reference_panel.json',destination/'data/compounds/skincare_reference_panel.json')
    shutil.copy2(ROOT/'data/compounds/skincare_reference_panel_expanded.json',destination/'data/compounds/skincare_reference_panel_expanded.json')
    for p in (destination/'data/wetlab').glob('*.csv'):
        p.write_bytes(p.read_bytes().rstrip(b'\r\n')+b'\n')
    shutil.copy2(ROOT/'data/skincare_exposure.csv',destination/'data/skincare_exposure.csv')
    shutil.copy2(ROOT/'data/experiment_plan_zh.json',destination/'data/experiment_plan_zh.json')
    (destination/'.nojekyll').touch()
    return destination

if __name__=='__main__':build();export_wiki()

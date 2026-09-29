"""Website account of the current cosmetic-ingredient scope."""
import json
from analysis.models.skincare_references import render_html as render_references
from analysis.models.skincare_evaluation import read

def render(root,table):
    summary=json.loads((root/'results/summaries/skincare_scope.json').read_text())
    evidence=read(root,'results/tables/skincare/evidence.csv')
    glabridin=[r for r in evidence if r['compound_id']=='15' and r['scope']=='CORE_HAZARD']
    for row in glabridin:
        try:row['value']=f"{float(row['value']):.4f}"
        except ValueError:pass
    metrics=read(root,'results/tables/skincare/maplight_heldout_metrics.csv')
    for row in metrics:
        for field in ['roc_auc','average_precision','brier_score']:row[field]=f"{float(row[field]):.4f}"
    body='''<section class="section" id="screening"><div class="kicker">护肤品原料评价 · Skincare ingredient scope</div>
<h2>围绕皮肤接触、光照和长期使用筛选模型任务</h2>
<p class="lead">光甘草定（15）是目标原料；其余五个通路化合物作为前体及潜在杂质参照。当前暂按非喷雾、留敷型面部护肤品组织证据，具体产品类型、浓度和配方仍待提供。分子预测不能代替成品评价。</p>
<div class="note"><b>按用途选任务，不按结果好坏选任务。</b>主要保留皮肤致敏、刺激/腐蚀、眼部接触、光毒性、遗传毒性与致癌性筛查，结合溶解度和亲脂性。保留内分泌及细胞应答信号供后续暴露评估；全身安全性不能因“外用”直接豁免。</div>
<p>口服吸收、生物利用度、肠道/人工膜通透性、血脑屏障、药物代谢酶、药代清除等退出常规任务；DILI、hERG 和口服 LD50 不再作为本轮主要模型。以往结果保留为历史记录。后续若产品为喷雾、唇部或眼周用途，需要相应调整暴露范围。</p>
<h3>本轮实际运行与已有证据</h3>'''
    body+=table(read(root,'results/tables/skincare/model_inventory.csv'),[('platform','平台'),('selected_records','当前选定记录数'),('execution','执行来源'),('status','证据范围')])
    body+='''<p>ADMET-AI 重新推理并提取 17 个相关任务：3 个主要危害、2 个配方性质、12 个机理信号。官方多任务网络共用前向计算，未使用的输出不进入当前分析。Chemprop 重新解释 AMES、Skin_Reaction 和 Carcinogens_Lagunin；MapLight 仅重新训练 AMES 的五个成员。网页模型与 VEGA/EPA 使用已核实的既有结果，未将读取缓存表述为重新运行。</p>
<figure class="figure"><img src="figures/skincare/local_and_photo_endpoints.svg" alt="护肤品相关皮肤、眼部、光毒性及遗传毒性预测"><figcaption>PREDICTED。admetSAR 原生分数分别展示；Photoinduced toxicity、Phototoxicity / photoirritation、Photoallergy 是不同终点，不能混为一个光安全结论。适用域和校准不确定性未导出。</figcaption></figure>
<figure class="figure"><img src="figures/skincare/glabridin_platform_comparison.svg" alt="光甘草定关键终点的平台结果差异"><figcaption>只作并列比较，不平均概率、不投票。皮肤与致癌性试验定义可能不同，不能把相似名称当作完全相同的终点。</figcaption></figure>
<h3>光甘草定的主要筛查证据</h3>'''
    body+=table(glabridin,[('platform','平台'),('endpoint','终点'),('value','原生结果'),('uncertainty','成员差异 / 原生类别置信度'),('applicability','适用性信息')])
    body+='''<h3>Chemprop 原子解释只围绕三个相关危害终点</h3>
<figure class="figure"><img src="figures/skincare/glabridin_atom_attribution.svg" alt="光甘草定致突变、皮肤反应和致癌性原子归因"><figcaption>红色提高、蓝色降低相对于零特征基线的模型输出。三图共用对称色标，原子编号对应下图。零特征图不是无毒对照分子。</figcaption></figure>
<figure class="figure"><img src="figures/skincare/atom_attribution_spread.svg" alt="原子归因均值及五成员差异"><figcaption>均值 ± 五成员标准差；不是实验置信区间或因果致毒基团。六分子 × 三任务 × 五成员的 90 项数值完整性检查保留。</figcaption></figure>
<h3>MapLight：AMES 训练与留出集验证</h3><p>官方无 GNN 指纹/描述符 + CatBoost 方法，五个随机种子。固定测试集未参与训练、选阈值或调参。当前不再运行 DILI/hERG，也没有把尚未运行的 GNN 扩展记作完成。</p>'''
    body+=table(metrics,[('seed','种子'),('train_n','训练行数'),('test_n','测试行数'),('roc_auc','ROC-AUC'),('average_precision','AP'),('brier_score','Brier')])
    body += render_references(root, table)
    body+='''<h3>如何读分数与基线</h3><p>当前没有经护肤品数据校准的“低风险”阈值。0.5 只能作为模型分类分界，不是产品安全线。没有将 DrugBank 已批准药物分布当作无毒对照，也未把皮肤致敏分数等同于皮肤刺激或经皮吸收。六个通路分子之间的比较不能证明最终配方安全；已知阳性/阴性对照组和外部校准仍待补充。</p>
<details class="supporting"><summary>长期及全身暴露相关信号</summary><p>重复给药、生殖毒性和内分泌相关信号保留为后续评估线索。它们尚未构成经皮暴露评估或人体效应证据；需要实际配方、浓度和经皮吸收信息。</p><figure class="figure"><img src="figures/skincare/mechanistic_followup.svg" alt="保留的受体与细胞应答模型信号"><figcaption>预测的是特定试验活性；不能直接推断实际人体毒性、内分泌干扰或功效。</figcaption></figure></details>
<h3>环境归趋和生态毒性继续保留</h3><p>护肤品使用后进入污水及生产排放仍与可持续性有关。VEGA、EPI Suite 和 ECOSAR 保留原生单位、适用域和警告。环境危害与真实环境风险之间仍缺排放和暴露数据。</p>
<figure class="figure"><img src="figures/evidence/vega_applicability_domain.svg" alt="VEGA 模型适用域"><figcaption>ADI 是模型适用程度，不是无毒概率。原生可靠性及结构警告见结果表。</figcaption></figure>
<figure class="figure"><img src="figures/evidence/ecosar_fish_screening.svg" alt="ECOSAR 鱼类生态毒性预测"><figcaption>保留类别差异与源警告；不作跨类别平均。</figcaption></figure>
<h3>成品与暴露证据缺口</h3>'''
    body+=table(read(root,'results/tables/skincare/evidence_gaps.csv'),[('topic','评价项目'),('status','状态'),('reason','缺口')])
    body+='''<p>范围参考 <a href="https://health.ec.europa.eu/publications/sccs-notes-guidance-testing-cosmetic-ingredients-and-their-safety-evaluation-12th-revision_en">SCCS 化妆品原料评价指南第 12 版</a>。这是科学范围依据，不是特定市场的法规合规结论。</p>
<div class="downloads"><a href="results/tables/skincare/evidence.csv">护肤品选定结果</a><a href="results/tables/skincare/admet_task_selection.csv">41 项任务取舍</a><a href="results/tables/skincare/platform_comparison.csv">平台并列比较</a><a href="results/tables/skincare/chemprop_atom_attribution.csv">原子归因</a><a href="results/tables/skincare/chemprop_attribution_completeness.csv">90 项数值检查</a><a href="results/summaries/skincare_scope.json">范围与来源校验</a><a href="docs/methodology/skincare_evaluation.md">方法与限制</a><a href="data/skincare_exposure.csv">待补的产品暴露信息</a><a href="data/processed/episuite_predictions.csv">环境归趋数据</a><a href="data/processed/ecosar_predictions.csv">生态毒性与警告</a></div></section>'''
    return body

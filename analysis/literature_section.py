"""Chinese literature-content narrative and an in-browser DOI explorer."""
import html,json
from pathlib import Path

def render(root,table):
    def load(p):return json.loads((root/p).read_text(encoding='utf-8'))
    s=load('results/summaries/literature_content.json');p=load('results/tables/literature_content/papers.json')
    n=len(p); c=s['counts']; esc=html.escape
    def fig(name,caption):return f'<figure class="figure"><a href="figures/literature_content/{name}.png"><img loading="lazy" src="figures/literature_content/{name}.svg" alt="{esc(caption)}"></a><figcaption>{caption}</figcaption></figure>'
    related=sum(x['flavonoid_related'] for x in p);yeast=sum(x['yeast_related'] for x in p)
    intersect=[x for x in p if x['flavonoid_related'] and x['yeast_related'] and x['spatial_related']]
    major_flav=sum(c['family'].get(k,0) for k in ['黄酮类','异黄酮类','异戊烯基黄酮'])
    major_flav_yeast=sum(x['family'] in ['黄酮类','异黄酮类','异戊烯基黄酮'] and x['host']=='酵母' for x in p)
    out='''<section class="section" id="literature"><div class="kicker">02 / 文献内容分析</div><h2>从文献研究版图，解释光甘草定项目为什么值得做</h2><p class="lead">这次直接使用已经筛选的完整数据库，围绕“研究什么、用什么底盘、采用什么策略、哪些方法能够迁移”展开分析。八张图把项目放回已有研究网络，再将证据连接到我们的实验问题。</p>'''
    out+=f'<div class="lit-metrics"><div><b>{n:,}</b><span>不同 DOI 文献条目</span></div><div><b>{related}</b><span>黄酮／异黄酮相关</span></div><div><b>{yeast}</b><span>酵母相关</span></div><div><b>{c["strategies"]["空间组织与区室化"]}</b><span>空间组织主题提及</span></div></div>'
    out+='''<p>统计单位为不同 DOI，20,567 条提取记录归并为 1,397 篇文献条目，避免把同篇论文的多行结果计成多篇。主类别图每篇只计一次；主题图允许一篇进入多个集合。以下比例描述本项目文献库。</p>
<h3>一、研究对象与底盘：我们的路线有怎样的知识基础？</h3>'''
    out+=fig('corpus_sankey','图 1｜宿主—研究对象—反应体系桑基图。流带宽度是文献数，每一列均合计 1,397；用于观察研究布局，不是物质流。')
    out+=f'<p><b>读图结论：</b>以源表主宿主标签统计，酵母为 {c["host"]["酵母"]} 篇（{c["host"]["酵母"]/n:.1%}）。黄酮、异黄酮及异戊烯基黄酮主类别共 {major_flav} 篇，其中 {major_flav_yeast} 篇的主宿主是酵母。它们为本项目选择酵母和黄酮类通路提供可借鉴的底盘与方法文献，而不是直接给出光甘草定的最佳宿主排名。</p>'
    out+=fig('research_distribution','图 2｜研究对象与宿主的主类别分布。条末为文献数及占完整文献库的比例。')
    out+=fig('host_object_matrix','图 3｜研究对象与宿主的组合。格内为不同 DOI 数；圆面积随数量增加，帮助寻找最接近项目的对照文献。')
    out+='''<h3>二、工程策略：从“提高表达”走向“协调反应”</h3>'''
    out+=fig('strategy_mentions','图 4｜八类工程与环境主题。深色为标题明确提及，浅色为标题或已抽取证据句提及；两者是嵌套口径，不相加。')
    out+=f'<p>表达与动态调控涉及 {c["strategies"]["表达与动态调控"]} 篇，发酵与过程优化 {c["strategies"]["发酵与过程优化"]} 篇，前体与辅因子供给 {c["strategies"]["前体与辅因子供给"]} 篇，空间组织与区室化 {c["strategies"]["空间组织与区室化"]} 篇。<b>我们的推断是：</b>项目可以在已有表达和过程优化基础上，进一步检验酶与底物的空间组织是否改善多步反应；文献频数用于选择可借鉴的方法，不代表方法的成功率。</p>'
    out+=fig('strategy_cooccurrence','图 5｜主题共现矩阵。对角线是单主题文献数，非对角线是同篇共同提及数；共现不自动意味着联用或协同增效。')
    out+='''<p>这张图帮助安排组合实验：空间组织需要同时考虑表达水平、前体／辅因子供给和培养条件。因此，相分离组应配有表达匹配的无相分离对照，避免将表达量变化误认为空间组织效果。</p>
<h3>三、研究交叉：项目的增量问题在哪里？</h3>'''
    out+=fig('project_intersections','图 6｜三个研究集合的互斥交集。黄酮相关使用主类别或标题命中，酵母相关使用任一源记录标签，空间组织使用标题及已抽取证据句命中。')
    out+=f'<p>本库黄酮相关 {related} 篇、酵母相关 {yeast} 篇、空间组织相关 {c["strategies"]["空间组织与区室化"]} 篇；三者交集为 {len(intersect)} 篇：一篇是酵母过氧化物酶体合成二氢槲皮素的研究，一篇是酵母酶共定位综述。<b>这个交叉位置支持一个明确的问题：能否将已有空间组织思路迁移到光甘草定的多酶反应？</b>“空间组织”涵盖有膜区室与无膜凝聚体，两者不能等同。</p>'
    out+='<ul>'+''.join(f'<li><a href="https://doi.org/{esc(x["doi"])}">{esc("二氢槲皮素的酵母过氧化物酶体生产研究" if "taxifolin" in x["title"].lower() else "酵母酶共定位策略综述")}</a>（{esc(x["doi"])}）</li>' for x in intersect)+'</ul>'
    out+='''<p>该交集说明当前语料中的方法连接较窄，适合提出进一步验证的研究方向。它不等同于全球只有两篇相关研究，也不用于宣称项目已被证明有效或具有全球首创性。</p>
<h3>四、相分离已有怎样的应用经验？</h3>'''
    out+=fig('condensate_sankey','图 7｜16 篇标题明确提及相分离、凝聚体或复凝聚的文献。生物合成、工程方法、细胞机制与材料应用分列。')
    out+='''<p>其中 3 篇归入生物合成应用，5 篇归入工程平台与方法，6 篇为细胞机制与疾病，2 篇为递送与仿生材料。这为项目提供不同层次的知识：形成和调控凝聚体的方法、酶招募机制，以及其他产物中的生产应用。</p>'''
    cases=[
       {'case':'无细胞甘氨酸合成','evidence':'数据库记录：1 小时游离酶对照 3.4 mmol/L，凝聚体体系 5.0 mmol/L，约为对照的 1.47 倍。','implication':'提供同研究内的定量方法例证；该增益不能直接转移到酵母光甘草定。','doi':'10.1016/j.jcou.2025.103269'},
       {'case':'依克多因的凝聚体工程','evidence':'数据库记录：工程菌在 5 L 反应器中 24 小时约 50 g/L；原研究结合祖先酶重建与空间组织。','implication':'说明凝聚体可进入生产体系研究；最终滴度不能全归因于相分离，也不与光甘草定直接排名。','doi':'10.1016/j.enzmictec.2026.110928'},
       {'case':'酵母过氧化物酶体合成二氢槲皮素','evidence':'数据库记录：摇瓶从头合成滴度 120.3 ± 2.4 mg/L；属于有膜细胞器区室化。','implication':'比其他产物更接近黄酮与酵母组合，支持空间组织的迁移思路；不作为液液相分离的直接验证。','doi':'10.1186/s12934-025-02773-2'}]
    out+=table(cases,[('case','可迁移案例'),('evidence','文献结果'),('implication','与项目的联系'),('doi','文献 DOI')])
    out+=fig('matched_condensate_example','图 8｜来自数据库的单研究定量例证。比较的是甘氨酸浓度，非光甘草定产率；仅展示原记录明确给出的两组数值，不补造误差条。')
    out+='''<p>案例来源：<a href="https://doi.org/10.1016/j.jcou.2025.103269">甘氨酸研究</a>、<a href="https://doi.org/10.1016/j.enzmictec.2026.110928">依克多因研究</a>、<a href="https://doi.org/10.1186/s12934-025-02773-2">二氢槲皮素研究</a>。这是方法例示，不是全部研究的效果量综述。</p>
<h3>五、光甘草定的研究必要性与路线依据</h3><div class="grid2"><article class="card"><h4>需要解决的生产问题</h4><p>既有光甘草定通路研究指出氧化成环步骤和中间体胞外分布值得关注。项目应检验生产是否受酶级联协调和局部反应环境限制，而不只追求更强表达。</p></article><article class="card"><h4>可借鉴的技术基础</h4><p>本库提供酵母、黄酮通路、酶共定位、区室化和凝聚体工程的相邻证据。选择这条路线具有可解释的方法基础。</p></article><article class="card"><h4>值得验证的交叉问题</h4><p>将空间组织方法放入光甘草定通路，检验产物形成、关键中间体分布和细胞负担是否一起改善。</p></article><article class="card"><h4>项目应交付的新增证据</h4><p>在匹配表达与培养条件下，获得产物及中间体时间序列、空间组织证据和纯产物资源强度。这些结果才能评价路线是否有效。</p></article></div>
<p>上述结论中，“路线具有研究依据”是文献支持的判断，“相分离能提高本项目生产效率”仍是实验假设。必要性建立在具体生产问题及可检验的改进空间上，而非单凭论文数量少。</p>
<h4>保留外部生产参照</h4>'''
    bench=load('data/literature/verified_benchmarks.json')['records']
    out+=table(bench,[('study_zh','研究'),('route_zh','条件'),('titer_mg_l','滴度（mg/L）')])
    out+='''<p>来源：<a href="https://www.nature.com/articles/s41467-026-68881-8">光甘草定生物合成网络研究</a>、<a href="https://www.nature.com/articles/s41467-026-72579-2">酵母模块组装研究</a>。两篇外部补充不计入 1,397 篇数据库统计；不同条件分列。</p>
<h3>按主题查阅文献</h3><p>可以按宿主、工程主题或关键词筛选，直接查看对应 DOI。论文题名保留原文，便于检索。</p><div class="lit-controls"><label>研究宿主<select id="lit-host"><option value="">全部宿主</option>'''
    out+=''.join(f'<option>{esc(h)}</option>' for h in c['host'])+'</select></label><label>工程主题<select id="lit-topic"><option value="">全部主题</option>'
    out+=''.join(f'<option>{esc(t)}</option>' for t in s['strategy_order'])+'</select></label><label>题名或 DOI<input id="lit-search" type="search" placeholder="例如 glabridin、peroxisome"></label></div><p id="lit-count" aria-live="polite"></p><div class="table-wrap"><table><thead><tr><th>文献原题与 DOI</th><th>宿主／对象</th><th>主题</th></tr></thead><tbody id="lit-results"></tbody></table></div><button id="lit-more" type="button">显示更多文献</button>'
    compact=[{k:x[k] for k in ['doi','title','host','family','strategies']} for x in p]
    payload=json.dumps(compact,ensure_ascii=False).replace('<','\\u003c')
    out+=f'<script id="lit-data" type="application/json">{payload}</script><script src="assets/literature_explorer.js" defer></script>'
    out+='<details><summary>统计口径与下载</summary><ul>'+''.join('<li>'+esc(x)+'</li>' for x in s['method_zh'])+'</ul>'
    out+='''<div class="downloads"><a href="results/tables/literature_content/paper_landscape.csv">逐篇文献分类与主题表</a><a href="results/tables/literature_content/sankey_flows.json">桑基图流量数据</a><a href="results/tables/literature_content/papers.json">逐篇主题命中与证据句</a><a href="results/summaries/literature_content.json">汇总计数与匹配规则</a><a href="docs/methodology/literature_content_zh.md">文献内容分析说明</a></div></details></section>'''
    return out

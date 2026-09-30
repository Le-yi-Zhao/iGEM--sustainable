"""One-interview qualitative evidence map, figures and Chinese website section."""
import csv
import html
import json
import re
from pathlib import Path

DATA='data/human_practices/professor_feedback.json'
FIG='figures/human_practices'
e=html.escape

def run(root:Path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    data=json.loads((root/DATA).read_text(encoding='utf-8'))
    out=root/FIG;out.mkdir(parents=True,exist_ok=True)
    folder=root/'results/tables/human_practices';folder.mkdir(parents=True,exist_ok=True)
    with (folder/'feedback_actions_zh.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','theme','source_section','speaker','excerpt','response','measure','effect','boundary','status','related_anchor']
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(data['records'])
    font=Path('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')
    font_manager.fontManager.addfont(str(font))
    plt.rcParams.update({'font.family':['DejaVu Sans',font_manager.FontProperties(fname=font).get_name()],
        'svg.fonttype':'path','svg.hashsalt':'galatea-interview-v1','axes.unicode_minus':False,
        'figure.facecolor':'#fcfaf7','savefig.facecolor':'#fcfaf7'})
    ink='#243c36';green='#356e5e';muted='#596861';soft='#edf2e9';sand='#f1e7dc'
    def canvas(title,subtitle):
        fig,ax=plt.subplots(figsize=(14,9));fig.subplots_adjust(0,0,1,1)
        ax.set(xlim=(0,14),ylim=(0,9));ax.axis('off')
        ax.text(.6,8.45,title,fontsize=23,color=ink,weight='bold')
        ax.text(.6,7.98,subtitle,fontsize=12,color=muted)
        return fig,ax
    def box(ax,x,y,w,h,title,body,fill=soft,size=13):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.015,rounding_size=0.10',
                                   facecolor=fill,edgecolor='none'))
        ax.text(x+.17,y+h-.22,title,fontsize=size,color=ink,weight='bold',va='top')
        ax.text(x+.17,y+h-.61,body,fontsize=size-1,color=ink,va='top',linespacing=1.55)
    def arrow(ax,a,b,curve=0):
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=15,linewidth=1.3,
                                    color=green,connectionstyle=f'arc3,rad={curve}'))
    def save(fig,name):
        svg=out/(name+'.svg');fig.savefig(svg,metadata={'Date':None})
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n',encoding='utf-8')
        fig.savefig(out/(name+'.png'),dpi=160);plt.close(fig)

    fig,ax=canvas('把教授建议变成可检验的项目决策','一份访谈的定性梳理 · 箭头表示回应关系，宽度不代表人数、权重或效果大小')
    for x,title in [(.65,'教授关注'),(4.8,'本次设计回应'),(9.2,'需要验证的结果')]:
        ax.text(x,7.43,title,color=green,fontsize=16,weight='bold')
    rows=[
        ('H02  让酶靠近','提高接触机会','验证酶招募与分配','加入表达匹配和破坏凝聚对照','机制是否成立','共定位、动态性、活性\n胞内外中间体分布'),
        ('H06  关注底物杂泛性','比较去甲基化时序','研究 OC / DMT 配合','同时记录目标产物和副产物','选择性是否改善','产物组成、纯度\n分离回收率'),
        ('H03–04  让计算参与迭代','用数据选择下一轮条件','候选配比 → 实验 → 更新','区分外部资料与项目实测','推荐能否复现','批次验证、预测偏差\n不确定性'),
        ('H05  拿出真实产物','身份与数量比概念更有说服力','标准品和分析证据链','按样品条件提供谱图','得到什么、得到多少','色谱、质谱、核磁\n纯度与产物质量'),
        ('H01  为自然保留空间','降低对植物资源的压力','比较相同功能单位的路线','记录原料、水、溶剂与能耗','资源优势是否成立','每 g 纯产物的投入\n排放与实际替代')]
    for i,row in enumerate(rows):
        y=5.98-i*1.20
        box(ax,.6,y,3.78,1.04,row[0],row[1],size=12)
        box(ax,4.75,y,3.9,1.04,row[2],row[3],size=12)
        box(ax,9.02,y,4.36,1.04,row[4],row[5],fill=sand,size=12)
        arrow(ax,(4.4,y+.52),(4.69,y+.52));arrow(ax,(8.68,y+.52),(8.96,y+.52))
    ax.text(.6,.48,'当前：已完成访谈整理与方案映射；右列均为需要取得或进一步验证的结果。',fontsize=12,color=muted)
    save(fig,'feedback_to_evidence')

    fig,ax=canvas('干湿迭代：让每一轮实验回答更具体的问题','教授建议形成的工作流程 · 尚未完成本项目生产配比的干湿闭环')
    boxes=[
        (.65,5.05,'01  外部知识','已有文献与生产时间序列\n动力学参数须注明来源\n缺失参数使用待检验范围',soft),
        (4.95,5.05,'02  提出候选条件','OC∶DMT 配比与总活性量\n时序、招募方式和培养条件\n先明确目标与约束',sand),
        (9.25,5.05,'03  匹配实验','游离酶、支架和凝聚体系\n表达匹配、破坏凝聚对照\n独立培养批次与分析校准',sand),
        (9.25,1.6,'04  同时测量','身份、纯度与产物质量\n中间体、底物消耗和生长\n水、溶剂、能耗与废物',sand),
        (4.95,1.6,'05  更新与检查','用项目实测更新响应模型\n检查预测偏差和不确定性\n护肤毒性模型不替代此步骤',sand),
        (.65,1.6,'06  新一批验证','选择信息量高且可行的条件\n用新的独立批次检验推荐\n保留失败条件与结果',sand)]
    for x,y,title,body,fill in boxes:box(ax,x,y,4.0,2.13,title,body,fill=fill,size=14)
    for a,b in [((4.69,6.1),(4.9,6.1)),((8.99,6.1),(9.2,6.1)),((11.25,5.0),(11.25,3.79)),
                ((9.2,2.7),(9.0,2.7)),((4.9,2.7),(4.69,2.7))]:arrow(ax,a,b)
    ax.plot([2.65,2.65,6.95],[3.77,4.45,4.45],color=green,lw=1.3)
    arrow(ax,(6.95,4.45),(6.95,4.98))
    ax.text(4.85,4.03,'下一轮：回到候选条件',fontsize=12,color=green,ha='center')
    ax.text(.65,.71,'外部数据用于提出问题；项目数据用于学习；新的实验批次用于检验。',fontsize=13,color=ink)
    save(fig,'dry_wet_iteration')

    fig,ax=canvas('从生产改进到可持续性，需要哪些证据？','共同功能单位：1 g 经纯度校正的分离光甘草定 · 比较路线须保持范围和质量要求一致')
    for x,title in [(.65,'希望实现的改变'),(4.95,'要收集的清单'),(9.0,'这些结果能支持什么')]:
        ax.text(x,7.43,title,color=green,fontsize=16,weight='bold')
    chains=[
        ('植物原料需求下降','连接访谈中的自然保护愿景','原料用量、来源与提取回收率\n对照路线及实际替代比例','判断原料需求变化\n生态获益还需土地与供应链证据'),
        ('分离负担下降','连接时序、选择性与纯度','目标产物、副产物及纯度\n溶剂用量、回收与废物处理','判断单位产物的分离投入\n高纯度不自动等于低能耗'),
        ('单位生产投入下降','连接酶比例与生产效率','纯产物质量、糖与总投入\n水、能源、培养时间及成本','分别比较单位产物资源强度\n滴度增加不能替代完整清单'),
        ('排放得到控制','连接环境模型与过程设计','排放浓度、去除率、残余物\n废液和活菌处理记录','在暴露信息支持下评价风险\n模型分数不等于实际排放安全')]
    for i,(title,sub,inventory,effect) in enumerate(chains):
        y=5.78-i*1.47
        box(ax,.6,y,3.95,1.22,title,sub,size=13)
        box(ax,4.9,y,3.68,1.22,'测量／记录',inventory,size=12)
        box(ax,8.93,y,4.47,1.22,'可以支持的判断',effect,fill=sand,size=12)
        arrow(ax,(4.58,y+.6),(4.85,y+.6));arrow(ax,(8.61,y+.6),(8.88,y+.6))
    ax.text(.6,.48,'本图为评价设计：尚未获得可用于宣称节水、减碳、减少采挖或生态恢复的项目结果。',fontsize=12,color=muted)
    save(fig,'sustainability_evidence_chain')
    return out

def integrate(root,page):
    data=json.loads((root/DATA).read_text(encoding='utf-8'))
    def fig(name,caption):
        return f'<figure class="figure"><a href="{FIG}/{name}.png"><img loading="lazy" src="{FIG}/{name}.svg" alt="{e(caption)}"></a><figcaption>{e(caption)}</figcaption></figure>'
    body='''<section class="section" id="interviews"><div class="kicker">06 / 人类实践与可持续发展</div><h2>从教授的建议，到可以检验的改变</h2>
<p class="lead">一次技术交流让我们把问题从“怎样提高产量”，推进到“为什么这样设计、用什么结果证明、改善是否值得付出资源”。这里展示建议如何进入研究方案，以及下一步需要取得的证据。</p>
<p>材料为团队提供的一份教授访谈转写，围绕项目决策整理为八个主题。访谈日期未提供，未核对录音；摘录与本次设计回应分开展示。它反映这次交流，不代表公众共识或市场调查。</p>
<blockquote class="hp-quote">“通过微生物细胞工厂满足人类需求，让自然有更多空间，让植物享受自己的生活。”<cite>教授访谈转写 · 策略价值与应用前景</cite></blockquote>
<p>团队已确认以酿酒酵母为项目生产宿主。我们将这一愿景转化为具体问题：在获得相同质量和数量的光甘草定时，微生物生产能否减少植物来源原料需求，并控制培养、纯化和排放负担？答案需要匹配的工艺数据。</p>
<h3>一、建议如何改变研究方案</h3>'''
    body+=fig('feedback_to_evidence','图 1｜访谈建议—设计回应—验证结果。属于定性决策图，箭头不代表统计流量；实验效果仍待验证。')
    body+='<p>点击主题，查看转写原话、本次回应及需要的结果。<b>“已纳入方案”表示文档和评价框架已更新，不表示菌株构建、实验验证或专家回访已经完成。</b></p><div class="hp-feedback-list">'
    for r in data['records']:
        body+=f'''<details class="hp-feedback" id="hp-{r['id']}"><summary>{r['id']} · {e(r['theme'])}</summary>
<p class="hp-source">转写定位：{e(r['source_section'])} · {e(r['speaker'])}</p><blockquote>“{e(r['excerpt'])}”</blockquote>
<dl><dt>本次设计回应</dt><dd>{e(r['response'])}</dd><dt>需要什么结果</dt><dd>{e(r['measure'])}</dd>
<dt>有了结果能说明什么</dt><dd>{e(r['effect'])}</dd><dt>当前进度</dt><dd>{e(r['status'])}</dd>
<dt>解释边界</dt><dd>{e(r['boundary'])}</dd></dl><a href="#{r['related_anchor']}">查看相关分析与实验计划</a></details>'''
    body+='</div><h3>二、干湿迭代如何落地</h3><p>计算首先帮助选择值得测的条件；实验提供真实响应；下一批实验检验推荐能否成立。当前已有的毒性、环境和原子归因模型服务于性质筛查，不承担生产酶比例优化。</p>'
    body+=fig('dry_wet_iteration','图 2｜拟开展的干湿迭代流程。已有外部文献数据可用于提出问题；项目生产配比模型、湿实验响应及迭代验证尚待完成。')
    body+='''<div class="hp-readable"><h4>实验与模型各自交付什么</h4><ol>
<li><b>外部知识：</b>目前已有文献生产曲线；Km、kcat 等参数只有与具体酶、底物和条件匹配时才采用，缺失保持待估计。</li>
<li><b>候选条件：</b>比较 OC∶DMT 有活性酶的比例、总量、时序与招募方式，说明哪些因素固定、哪些改变。</li>
<li><b>匹配测量：</b>取得表达匹配对照、产物身份、纯度、中间体、底物消耗和资源记录。</li>
<li><b>更新与验证：</b>用项目数据建立响应模型，将不确定性纳入下一轮条件选择，再以新批次验证。</li></ol></div>
<h3>三、把“可持续”拆成能分别核算的问题</h3>'''
    body+=fig('sustainability_evidence_chain','图 3｜可持续性证据链。原料需求、纯化投入、生产资源与排放分别评价，尚无项目节约率或生态获益数值。')
    body+='''<div class="table-wrap"><table><thead><tr><th>评价方向</th><th>建议记录</th><th>对应已有内容</th></tr></thead><tbody>
<tr><td>植物原料压力</td><td>原料质量、来源、纯度、回收率及真实替代比例</td><td><a href="#environment">提取纯度与处理规模</a></td></tr>
<tr><td>选择性与分离负担</td><td>目标产物、中间体、副产物、溶剂与回收</td><td><a href="#production">文献生产时间序列</a></td></tr>
<tr><td>单位产物资源强度</td><td>总投入、水、能源、时间和成本／g 纯产物</td><td><a href="#environment">资源收支平衡条件图</a></td></tr>
<tr><td>排放和环境风险</td><td>排放浓度、处理去除率、受纳环境与残余物</td><td><a href="#opera">环境性质与适用域</a></td></tr>
</tbody></table></div>
<p><b>这些是团队对访谈愿景的评价转化。</b>当前单位产物资源比较尚不是完整生命周期评价。碳排放还需要边界一致的清单与排放因子；生物多样性还需要土地利用及供应链证据。</p>
<h3>四、把“相邻关卡”的比喻写得准确</h3><p>可以把级联反应想象成多道相邻关卡：我们希望通过招募让相邻步骤的酶更容易遇到合适的反应物。但液滴会与周围环境交换分子，并非密封管道，底物也不一定按固定次序传递。需要结合分配、活性和中间体数据判断效果。</p>
<details class="hp-feedback"><summary>科学术语与转写核对</summary><ul>
<li>“LOPS”在本页统一为液液相分离（LLPS）。</li>
<li>该通路文献中 DMT 指去甲基化酶，OC 指氧化环化酶。原论文指出 OC 相关瓶颈，并以模型研究去甲基化时序，支持后续检验方向。</li>
<li>“OC 蛋白疏水”与“底物／产物疏水”不是同一命题；没有具体序列分析、定位与分配证据时，不将其作为已证实的招募原因。</li>
<li>转写中的宿主名称已由团队确认：本项目使用酿酒酵母。外部酵母研究不等于本项目已完成构建。</li>
</ul><p>核对来源：<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC12963581/">Zhang 等（2026），光甘草定生物合成网络，Fig. 4 与结果部分</a>。</p></details>
<h3>五、团队学习与下一次回访</h3><p>访谈称团队当时有 12 名成员。可以用手绘通路、独立解释模型假设、复核原始记录和贡献日志呈现学习过程；目前没有学习测评或个人贡献数据，因此不作排名或提升率统计。</p>
<p>待获得匹配组产物、纯度和资源记录后，带着“哪些建议已实施、哪些未奏效、还存在什么问题”回访教授。第二种天然产物、人工催化剂与多结构域分子机器留作后续探索，先通过独立实例验证适用范围。</p>
<div class="hp-vision"><p>让分子改善生活，让生产为自然保留空间。</p><small>项目愿景：以可验证的生产与环境结果逐步实现。</small></div>
<div class="downloads"><a href="results/tables/human_practices/feedback_actions_zh.csv">下载八项反馈与验证清单</a><a href="data/human_practices/professor_feedback.json">查看摘录、来源定位和整理口径</a></div></section>'''
    page,n=re.subn(r'<section class="section" id="interviews">.*?</section>',lambda _:body,page,count=1,flags=re.S)
    if n!=1:raise ValueError('Expected one interviews section')
    page=page.replace('<a href="#interviews">访谈与反馈</a>','<a href="#interviews">人类实践与可持续性</a>',1)
    page=page.replace('</head>','<link rel="stylesheet" href="assets/human_practices.css"></head>',1)
    return page

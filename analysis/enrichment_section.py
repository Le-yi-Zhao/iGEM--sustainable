"""Integrate traceable Chinese efficacy, production and validation results."""
import csv,json,re
from html import escape as e

def fig(name,caption):
    return f'<figure class="figure"><a href="figures/research_enrichment/{name}.png"><img loading="lazy" src="figures/research_enrichment/{name}.svg" alt="{e(caption)}"></a><figcaption>{caption}</figcaption></figure>'
def table(headers,rows):
    return '<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table></div>'
def link(doi,label):return f'<a href="https://doi.org/{doi}" target="_blank" rel="noopener">{label}</a>'

def integrate(root,page):
    m=json.loads((root/'results/summaries/research_enrichment.json').read_text())
    body='''<section class="section" id="efficacy"><div class="kicker">新增 / 功效证据</div><h2>选择光甘草定，有哪些正面证据？</h2><p class="lead">同一酶试验中的活性比较，能够支持光甘草定作为护肤活性候选的研究价值。下面将酶、细胞、动物和人体复方研究分开解释，不把酶抑制倍数写成成品美白倍数。</p><div class="note">本轮定向补充原始研究与公开源数据，未重新按质量删选原有 1,397 篇文献，也不是穷尽式系统综述。数据库内研究稀少，只描述该数据库的覆盖，不能替代全球研究数量统计。</div>'''
    body+=fig('efficacy_ic50','三篇原始研究的四组同试验比较，统一为 μmol/L。IC50 表示抑制一半酶活性的浓度。2022 年两组来自同一论文；点图不假装具有统一的误差定义。')
    body+=fig('efficacy_ratio','四组描述性比值约为 176、413、58 和 259。只比较各自试验中的光甘草定与曲酸，不合并成一个总体倍数，也不用于推导人体剂量。')
    body+='<p>原始定位：'+link('10.1016/j.saa.2016.06.008','2016 年 Fig. 2／结果段')+'；'+link('10.1016/j.foodchem.2022.133423','2022 年摘要与酶动力学')+'；'+link('10.3389/fphar.2024.1422310','2024 年 Table 4')+'。2016 年与 2022 年对抑制类型的解释也不同，说明实验方法和底物条件必须保留。</p>'
    body+='<h3>从酶活性到皮肤用途，还需要跨过哪些证据层级？</h3>'
    evidence=[
      ['酶试验','三篇研究中，光甘草定 IC50 均低于各自曲酸对照。','支持高活性候选；蘑菇酶不等于人体皮肤。','上方三篇原始研究'],
      ['细胞与豚鼠皮肤','1998 年研究报告细胞酪氨酸酶抑制；0.5% 外用条件下豚鼠 UVB 色沉／红斑减轻。','属于外部动物研究，0.5% 不是建议的人体安全添加量。',link('10.1111/j.1600-0749.1998.tb00494.x','Yokota 1998')],
      ['细胞／斑马鱼的分歧','2023 年研究中，B16F1 细胞黑色素减少，但斑马鱼未显示同向效果。2016 年还报告斑马鱼胚胎毒性。','跨物种不能直接外推；效力、暴露与安全须分别验证。',link('10.3390/molecules28030958','Dej-adisai 2023')+'；'+link('10.1016/j.saa.2016.06.008','Chen 2016')],
      ['人体复方探索','40 名女性使用含光甘草定、穿心莲内酯和脱铁乳铁蛋白的复方凝胶 6 个月，研究报告改善；3 例轻度短暂干燥。','无对照、开放研究；改善无法单独归因于光甘草定。',link('10.1111/jocd.13161','Cantelli 2020（2019 年在线）')]
    ]
    body+=table(['研究层级','观察到什么','对项目意味着什么','原始来源'],evidence)
    body+='<p><b>可以写入 Wiki 的结论：</b>光甘草定具有值得开发的酶抑制活性和皮肤用途研究基础，支持继续开展生产与配方研究。局部安全、有效暴露和独立人体功效仍是必须验证的部分。</p><div class="downloads"><a href="results/tables/research_enrichment/efficacy_matched_assays.csv">同试验功效数值、单位、原文定位</a></div></section>'

    body+='''<section class="section" id="production"><div class="kicker">新增 / 生产瓶颈</div><h2>从文献原始重复中，找到值得改造的环节</h2><p class="lead">已有研究证明可以合成光甘草定，时间序列则进一步显示中间体积累和目标产物出现的时机。这为酶比例、空间组织和回收优化提供检验方向。</p>'''
    body+=f'<p>读取 Zhang 等（2026）公开 Source Data 的 Fig. 4d、4e，共 {m["time_series_observed_values"]} 个有效浓度值，另有 {m["missing_values"]} 个空缺保持缺失。点为原文重复，误差线为样本标准差；不是本项目湿实验。'+link('10.1038/s41467-026-68881-8','查看原论文')+'。</p>'
    body+=fig('production_multiroute','NhPDA1 多路径体系。各小图纵轴独立；多数时点 n=3，化合物 10 在 48 h 只有两个记录。原文零值保留，不把零解释为已证明绝对不存在。')
    body+=fig('production_singleroute','GgDMT1 单路径体系。同样保留早期密集采样；不平滑拟合成未测曲线，不做缺失值插补。')
    body+=fig('production_composition','统一到 120 h 的描述性截面。分母分别是各面板覆盖的 6 种与 4 种化合物质量浓度之和，不能作为两路线的转化率、总碳收率或环境排放比例。')
    body+='''<p><b>实际线索：</b>120 h 的光甘草定均值分别为 0.933 和 0.476 mg/L；多路径体系的化合物 10、14 仍有积累，单路径体系则主要积累 13、14。这支持把末端转化、酶比例和中间体残留作为重点，而不是只测最终产物。两种体系的采样与路径不同，不能把浓度差直接归因于某一个因子。</p><p><b>相分离设计能够检验什么：</b>以匹配的游离酶、支架、完整凝聚体系及破坏凝聚对照，测量中间体和产物的胞内／胞外分布；只有这些对照才能区分空间组织、表达量和总生物量的贡献。当前文献曲线不构成相分离已提高光甘草定生产的证据。</p><div class="downloads"><a href="results/tables/research_enrichment/production_replicates.csv">逐重复数据与 Excel 行列定位</a><a href="results/tables/research_enrichment/production_time_summary.csv">时间序列均值、标准差与样本量</a><a href="results/tables/research_enrichment/production_pool_composition.csv">120 h 已测物构成</a></div></section>'''
    page=page.replace('<section class="section" id="models">',body+'<section class="section" id="models">',1)
    env='''<h3>提取与纯化｜用文献实测说明分离负担</h3><p>Cho 等（2004）的同研究七种提取条件中，粗提物光甘草定纯度为 0.53%–4.27%。这项历史研究用于说明纯度与分离负担的关系，不能代表当前最优工业工艺。</p>'''
    env+=fig('extraction_purity','左侧是文献实测均值 ± SD（n=3）；右侧由平均纯度计算，约 23.4–188.7 g 粗提物中含有 1 g 光甘草定。尚未加入后续纯化损失，不是最终纯品产率。')
    env+='''<p>来源：<a href="https://www.jstage.jst.go.jp/article/apcche/2004/0/2004_0_587/_pdf">Cho 等，Table 1，PDF 第 3 页</a>。此图未依据纯度推荐溶剂，也未据此计算碳足迹；原表另一项“原料中浓度”的脚注单位存在不一致，本轮没有用该项换算原料消耗。</p><h3>生物生产｜浓度与回收率共同决定处理规模</h3>'''
    env+=fig('broth_volume','条件图：发酵液体积（L）= 1000 ÷ [浓度（mg/L）× 总回收率]。各格都是假设，不是实际生产量、经济性或用水量。')
    env+='''<p>例如浓度为 1 mg/L、总回收率 70% 时，得到 1 g 纯光甘草定需处理约 1,429 L 发酵液；提高到 10 mg/L 且保持同一回收率时，约为 143 L。这说明提高浓度与回收率的价值，也说明“能生物合成”尚不等于“已实现资源优势”。不能将发酵液体积直接当作净用水量。</p><div class="downloads"><a href="results/tables/research_enrichment/extraction_purity.csv">提取纯度及派生计算</a><a href="results/tables/research_enrichment/broth_volume_scenarios.csv">28 个处理规模条件场景</a><a href="results/summaries/research_enrichment.json">新增分析范围与来源校验</a></div>'''
    pattern=r'(<section class="section" id="environment">.*?)(</section>)'
    page=re.sub(pattern,lambda x:x[1]+env+x[2],page,flags=re.S)
    # Navigation additions preserve existing anchors and all earlier analyses.
    page=page.replace('<a href="#models">','<a href="#efficacy">功效证据</a><a href="#production">生产瓶颈</a><a href="#models">',1)
    page=page.replace('本轮已在 Matvision 为 16 种分子实际运行 ADMET-AI／MapLight，新增中文比较表和七张环境与资源图。文献分析覆盖全部 1,397 篇；其他平台读取既有已保存结果，湿实验仍等待实测。','本页已加入同研究功效比较、文献生产时间序列、提取与回收分析；原有 1,397 篇文献内容分析和 16 种成分模型对照全部保留。新图区分外部实测、模型预测与条件计算，项目湿实验仍待取得。')
    page=page.replace('<h2>现阶段能够写进项目结论的内容</h2>','<h2>现阶段能够写进项目结论的内容</h2><p><b>选题价值：</b>同研究酶试验比较支持光甘草定的活性优势；公开生产数据中的中间体积累支持进一步研究末端转化和回收。实际新增的 GNN 模型只带来很小的测试表现变化，OPERA 仍提示非易降解，不能概括为已经证实全面安全或环境友好。</p>')
    return page

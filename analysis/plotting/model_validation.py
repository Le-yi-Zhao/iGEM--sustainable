"""Cached validation visuals; never retrain models in the page build."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from sklearn.metrics import roc_curve,precision_recall_curve
from sklearn.calibration import calibration_curve
from analysis.enrichment_section import table,fig

def run(root):
    raw=root/'data/raw/skincare/maplight_gnn'
    meta=json.loads((raw/'run_metadata.json').read_text())
    pred=pd.read_csv(raw/'heldout_predictions.csv');refs=pd.read_csv(raw/'reference_members.csv')
    structures=json.loads((root/'data/raw/skincare/expanded_references/structures.json').read_text());names={x['id']:x['name_zh'] for x in structures}
    out=root/'results/tables/research_enrichment'
    summary=refs.groupby(['id','model']).score.agg(['mean','std','count']).reset_index()
    summary['name_zh']=summary.id.map(names);summary.to_csv(out/'gnn_reference_summary.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(meta['ensemble_metrics']).to_csv(out/'gnn_heldout_metrics.csv',index=False,encoding='utf-8-sig')
    f=Path('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')
    if f.exists():font_manager.fontManager.addfont(str(f));plt.rcParams['font.family']=['DejaVu Sans',font_manager.FontProperties(fname=str(f)).get_name()]
    plt.rcParams.update({'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path','svg.hashsalt':'galatea-model-validation-v1','axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fcfaf7','axes.facecolor':'#fcfaf7','savefig.facecolor':'#fcfaf7'})
    def save(figure,name):
        p=root/'figures/research_enrichment'/f'{name}.svg';figure.savefig(p,bbox_inches='tight',metadata={'Date':None});p.write_text('\n'.join(l.rstrip() for l in p.read_text().splitlines())+'\n')
        figure.savefig(p.with_suffix('.png'),dpi=170,bbox_inches='tight');plt.close(figure)
    valid=pred[~pred.overlaps_training_connectivity].copy()
    fig0,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for model,col,color in [('MapLight','base_mean','#788e96'),('MapLight＋GIN','gnn_mean','#275f49')]:
        fpr,tpr,_=roc_curve(valid.Y,valid[col]);pr,re,_=precision_recall_curve(valid.Y,valid[col])
        axes[0].plot(fpr,tpr,label=model,color=color);axes[1].plot(re,pr,label=model,color=color)
    axes[0].plot([0,1],[0,1],ls='--',color='#bdb9ad');axes[1].axhline(valid.Y.mean(),ls='--',color='#bdb9ad',label='测试集阳性比例')
    axes[0].set(xlabel='假阳性率',ylabel='真阳性率',title='ROC｜区分阳性与阴性的能力')
    axes[1].set(xlabel='召回率',ylabel='精确率',title='PR｜检出与误报的关系')
    for ax in axes:ax.legend();ax.set(xlim=(0,1),ylim=(0,1.02))
    fig0.suptitle(f'AMES 固定测试集｜排除训练连接结构重叠后 n={len(valid)}',fontsize=14);save(fig0,'gnn_discrimination')
    fig0,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    calrows=[]
    for model,col,color in [('MapLight','base_mean','#788e96'),('MapLight＋GIN','gnn_mean','#275f49')]:
        pp=valid[col].to_numpy();bins=np.minimum((pp*10).astype(int),9)
        for j in range(10):
            keep=bins==j
            if keep.any():calrows.append(dict(model=model,bin_lower=j/10,bin_upper=(j+1)/10,n=int(keep.sum()),mean_score=float(pp[keep].mean()),observed_positive_fraction=float(valid.Y.to_numpy()[keep].mean())))
        rr=[r for r in calrows if r['model']==model]
        axes[0].plot([r['mean_score'] for r in rr],[r['observed_positive_fraction'] for r in rr],'o-',label=model,color=color)
        axes[1].hist(pp,bins=np.linspace(0,1,11),histtype='step',linewidth=2,color=color,label=model)
    axes[0].plot([0,1],[0,1],ls='--',color='#bdb9ad');axes[0].set(xlim=(0,1),ylim=(0,1),xlabel='分箱内平均模型分数',ylabel='该箱实际 AMES 阳性比例',title='可靠性曲线｜只作诊断，不在测试集校准')
    axes[1].set(xlabel='模型分数',ylabel='测试化合物数',title='分数分布｜理解每个区间的数据量')
    for ax in axes:ax.legend()
    pd.DataFrame(calrows).to_csv(out/'gnn_reliability_bins.csv',index=False,encoding='utf-8-sig');save(fig0,'gnn_reliability')
    fig0,ax=plt.subplots(figsize=(12,8),layout='constrained');ids=[x['id'] for x in structures]
    for model,offset,color in [('MapLight',-.17,'#788e96'),('MapLight+GIN',.17,'#275f49')]:
        s=summary[summary.model==model].set_index('id').loc[ids]
        ax.barh(np.arange(16)+offset,s['mean'],xerr=s['std'],height=.3,label=model,color=color,capsize=2)
    ax.set(yticks=range(16),yticklabels=[names[i] for i in ids],xlim=(0,1),xlabel='AMES 阳性模型分数｜五成员均值 ± SD',title='同一批 16 种分子｜加入冻结 GIN 特征后发生了什么？');ax.invert_yaxis();ax.legend();save(fig0,'gnn_references')
    near=json.loads((raw/'training_neighbors.json').read_text());lookup={x['id']:x for x in near}
    fig0,ax=plt.subplots(figsize=(12,8),layout='constrained')
    vals=[lookup[i]['max_tanimoto'] for i in ids]
    ax.barh([names[i] for i in ids],vals,color=['#ac7858' if v>.99999 else '#739582' for v in vals]);ax.invert_yaxis()
    for i,v in enumerate(vals):ax.text(v+.014,i,f'{v:.3f}',va='center')
    ax.set(xlim=(0,1.13),xlabel='与训练集最近分子的 Morgan 指纹 Tanimoto 相似度',title='结构邻域诊断｜相似度不是正式适用域或安全阈值')
    save(fig0,'model_neighbors')
    page='''<section class="section" id="validation"><div class="kicker">新增 / 模型实际运行</div><h2>MapLight＋GNN 已运行：用测试表现判断新增模型的价值</h2><p class="lead">本次在 Matvision 提取冻结的 GIN 图神经网络表示，再与原 MapLight 的 2,563 个指纹／描述符拼接，训练五个 CatBoost 成员。它遵循官方扩展的特征思路，属于冻结图表示加分类器。</p>'''
    page+=f'<p>训练／验证池 {meta["train_n"]:,} 行，固定测试集 {meta["test_n"]:,} 行；测试集未用于拟合、调参、早停或阈值选择。为公平比较，基础特征和原模型检查点保持一致，基础模型测试输出复现误差小于 10⁻¹⁰。'+f'发现 {meta["test_training_connectivity_overlap_rows"]} 行测试分子与训练集连接结构重叠，因此同时报告原测试集与剔除重叠后的结果。</p>'
    rows=[]
    for r in meta['ensemble_metrics']:rows.append([r['model'],'原固定测试集' if r['split']=='official_test' else '去除训练重叠',r['n'],f"{r['roc_auc']:.4f}",f"{r['average_precision']:.4f}",f"{r['brier']:.4f}"])
    page+=table(['模型','测试范围','样本数','ROC-AUC ↑','平均精确率 AP ↑','Brier 分数 ↓'],rows)
    page+='<p>Brier 同时受区分与校准影响，不能单独证明概率校准良好。下图均使用剔除训练连接结构重叠后的子集；完整结果一并下载。</p>'
    page+=fig('gnn_discrimination','模型区分能力比较；PR 图的横线是该测试子集阳性比例，不是安全线。')
    page+=fig('gnn_reliability','10 个等宽分箱的诊断曲线与分数分布。没有据此对测试集重新拟合校准器；各箱样本量可下载。')
    page+='<h3>新增 GNN 的收益有多确定？</h3>'
    rows=[]
    for k,r in meta['paired_bootstrap']['results'].items():rows.append([{'roc_auc':'ROC-AUC','average_precision':'AP','brier':'Brier'}[k],f"{r['delta_gnn_minus_base_mean']:+.4f}",f"[{r['percentile95'][0]:+.4f}, {r['percentile95'][1]:+.4f}]"])
    page+=table(['指标','配对重采样的平均差（GIN－基础）','95% 百分位区间'],rows)
    page+='<p>对去重叠测试子集按化学连接结构分组，进行 1,000 次配对重采样。区间包含零时，不能宣称稳定优于基础模型；这反映测试样本抽样变化，不覆盖全部训练或外推不确定性。</p>'
    page+=fig('gnn_references','参照分子包含训练集成员，不能把本图当作独立外部验证。误差线为五成员标准差，不是人体风险区间。')
    target=summary[summary.id=='glabridin'].set_index('model')
    page+=f'<p>光甘草定的 AMES 分数由基础 MapLight 的 {target.loc["MapLight","mean"]:.3f} 变为加入 GIN 后的 {target.loc["MapLight+GIN","mean"]:.3f}。变化反映模型表示差异，不等于毒性发生改变，也不能通过挑选较低值确定安全添加浓度。</p>'
    page+=fig('model_neighbors','基于 2,048 位、半径 2 的 Morgan 指纹。显示最近邻并提供前五个训练邻居；相似度高仍不能排除活性突变或数据偏差。')
    page+='<p>GIN 的预训练分子与基准数据的重叠尚不明确；参照组的训练重叠仍然存在。该运行增加一种表示方法与可复查的验证，未新增任何人体安全实测。</p><div class="downloads"><a href="data/raw/skincare/maplight_gnn/run_metadata.json">运行参数、版本、校验与配对重采样</a><a href="data/raw/skincare/maplight_gnn/heldout_predictions.csv">逐测试分子预测与重叠标记</a><a href="results/tables/research_enrichment/gnn_reference_summary.csv">16 成分双模型汇总</a><a href="results/tables/research_enrichment/gnn_reliability_bins.csv">可靠性分箱数据</a><a href="data/raw/skincare/maplight_gnn/training_neighbors.json">前五个训练邻居</a></div></section>'
    (root/'results/summaries/validation_section.html').write_text(page,encoding='utf-8')
    return meta

def integrate(root,page):
    section=(root/'results/summaries/validation_section.html').read_text()
    page=page.replace('<section class="section" id="environment">',section+'<section class="section" id="environment">',1)
    page=page.replace('<a href="#environment">','<a href="#validation">模型验证</a><a href="#environment">',1)
    page=page.replace('图神经网络扩展尚未运行，不记作已完成。','图神经网络扩展已完成，本轮结果见模型验证部分。')
    return page

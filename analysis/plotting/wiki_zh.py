"""Chinese figures from audited source tables; no model inference or wet-lab simulation."""
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

NAMES={'glabridin':'光甘草定','alpha_arbutin':'α-熊果苷','niacinamide':'烟酰胺',
       'ascorbyl_glucoside':'抗坏血酸葡糖苷','kojic_acid':'曲酸','beta_arbutin':'β-熊果苷'}
TASKS={'AMES':'细菌回复突变','Skin_Reaction':'皮肤反应／致敏','Carcinogens_Lagunin':'致癌性筛查',
 'NR-AR':'雄激素受体','NR-AR-LBD':'雄激素受体配体结合域','NR-AhR':'芳烃受体','NR-Aromatase':'芳香化酶',
 'NR-ER':'雌激素受体','NR-ER-LBD':'雌激素受体配体结合域','NR-PPAR-gamma':'过氧化物酶体增殖物激活受体γ',
 'SR-ARE':'抗氧化应答元件','SR-ATAD5':'基因组稳定性应答','SR-HSE':'热休克应答',
 'SR-MMP':'线粒体膜电位','SR-p53':'肿瘤抑制蛋白 p53 应答',
 'Lipophilicity_AstraZeneca':'亲脂性数据集预测值','Solubility_AqSolDB':'水溶解度（以 mol/L 为单位取对数）'}

def read(root,path):
    with (root/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def run(root:Path):
    font=Path('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')
    if font.exists():
        font_manager.fontManager.addfont(str(font))
        plt.rcParams['font.family']=['DejaVu Sans',font_manager.FontProperties(fname=str(font)).get_name()]
    plt.rcParams.update({'axes.unicode_minus':False,'svg.fonttype':'path','svg.hashsalt':'galatea-zh-20260930','font.size':11,
        'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fcfaf7',
        'axes.facecolor':'#fcfaf7','savefig.facecolor':'#fcfaf7'})
    out=root/'figures/wiki_zh';out.mkdir(parents=True,exist_ok=True)
    def save(fig,name):
        svg=out/(name+'.svg')
        fig.savefig(svg,bbox_inches='tight',metadata={'Date':None})
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n',encoding='utf-8')
        fig.savefig(out/(name+'.png'),dpi=170,bbox_inches='tight');plt.close(fig)
    stats=json.loads((root/'results/summaries/literature_audit.json').read_text())
    fig,axs=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
    axs[0].barh(['需人工复核','未标记需人工复核'],[stats['needs_human_review']['true'],stats['needs_human_review']['false']],color=['#bc704f','#70938b'])
    axs[0].set(title='原数据库质量标记',xlabel='抽取记录数（不是论文数）')
    for i,v in enumerate([stats['needs_human_review']['true'],stats['needs_human_review']['false']]):axs[0].text(v+120,i,f'{v:,}',va='center')
    axs[0].set_xlim(0,16000)
    cats=list(stats['review_categories']); vals=[stats['review_categories'][k] for k in cats]
    axs[1].barh(cats,vals,color=['#bc704f','#9571a6','#70938b'])
    for i,v in enumerate(vals):axs[1].text(v+1,i,str(v),va='center')
    axs[1].set(xlim=(0,65),title='108 条候选记录的核查处置',xlabel='抽取记录数（来自 18 个 DOI）')
    fig.suptitle('文献抽取质量审计｜20,567 条记录，1,397 个 DOI',fontsize=16)
    save(fig,'literature_audit')
    rows=json.loads((root/'results/tables/skincare/reference_predictions.json').read_text())
    def get(cid,model,task):return next(r for r in rows if (r['id'],r['model'],r['task'])==(cid,model,task))
    ids=list(NAMES);colors=['#a54d44']+['#748e88']*5
    fig,axs=plt.subplots(2,2,figsize=(12,9),layout='constrained')
    for ax,(model,task) in zip(axs.flat,[('ADMET-AI','Skin_Reaction'),('ADMET-AI','AMES'),('ADMET-AI','Carcinogens_Lagunin'),('MapLight','AMES')]):
        v=[get(i,model,task) for i in ids]; means=[r['mean'] for r in v]
        ax.barh(list(NAMES.values()),means,xerr=[r['sd'] for r in v],color=colors,capsize=3)
        ax.invert_yaxis();ax.set(xlim=(0,1.05),xlabel='阳性类别模型分数',title=model+' · '+TASKS[task])
        for j,r in enumerate(v):ax.text(min(r['mean']+r['sd']+.02,.95),j,f"{r['mean']:.3f}",va='center',fontsize=10)
    fig.suptitle('固定护肤成分参照组｜均值与五成员标准差',fontsize=16)
    save(fig,'reference_comparison')
    p=[r for r in read(root,'results/tables/skincare/platform_comparison.csv') if r['compound_id']=='15']
    fig,axs=plt.subplots(1,3,figsize=(12,4.4),layout='constrained')
    for ax,task in zip(axs,['AMES','Skin_Reaction','Carcinogens_Lagunin']):
        r=next(x for x in p if x['endpoint']==task)
        keys=[k for k in ['admet_ai','admetlab','admetsar','maplight'] if r[k]]
        labels={'admet_ai':'ADMET-AI','admetlab':'ADMETlab','admetsar':'admetSAR','maplight':'MapLight'}
        vals=[float(r[k]) for k in keys]
        ax.barh([labels[k] for k in keys],vals,color='#8d739c');ax.invert_yaxis()
        for i,v in enumerate(vals):ax.text(v+.025,i,f'{v:.3f}',va='center')
        ax.set(xlim=(0,1.06),title=TASKS[task],xlabel='各平台原生分数')
    fig.suptitle('光甘草定｜平台分歧需保留，不能平均或投票',fontsize=16)
    save(fig,'platform_comparison')
    tasks=[t for t in TASKS if t.startswith(('NR-','SR-'))]
    fig,ax=plt.subplots(figsize=(12,7),layout='constrained')
    for j,t in enumerate(tasks):
        refs=[get(i,'ADMET-AI',t)['mean'] for i in ids[1:]]
        ax.plot([min(refs),max(refs)],[j,j],color='#748e88',lw=8,solid_capstyle='round',label='五种参照的最小至最大值' if j==0 else None)
        g=get('glabridin','ADMET-AI',t)
        ax.errorbar(g['mean'],j,xerr=g['sd'],fmt='o',color='#a54d44',capsize=3,label='光甘草定均值与成员标准差' if j==0 else None)
    ax.set(yticks=range(len(tasks)),yticklabels=[TASKS[t] for t in tasks],xlim=(-.02,1.12),xlabel='特定试验活性模型分数',title='ADMET-AI｜全部十二项受体与细胞应答信号')
    ax.invert_yaxis();ax.legend(loc='lower right',fontsize=10)
    save(fig,'mechanistic_signals')
    from analysis.models.resource_scenarios import relative_intensity
    products=np.linspace(.6,3,100); resources=np.linspace(.6,2.5,100)
    z=np.array([[100*(1-relative_intensity(r,p)) for p in products] for r in resources])
    fig,ax=plt.subplots(figsize=(10,6.6),layout='constrained')
    m=ax.contourf(products,resources,z,levels=np.arange(-150,85,5),cmap='BrBG',
        norm=matplotlib.colors.TwoSlopeNorm(vmin=-150,vcenter=0,vmax=80),extend='both')
    ax.plot([.6,2.5],[.6,2.5],color='#292929',lw=2,label='持平线：资源比 = 纯产物质量比')
    ax.scatter([1.2],[1.1],color='black',s=40);ax.annotate('示例：产物 ×1.2，资源 ×1.1\n单位产物资源减少 8.3%',xy=(1.2,1.1),xytext=(1.62,.74),arrowprops={'arrowstyle':'->'},fontsize=11)
    ax.set(xlabel='相分离组 / 基线组：纯产物质量比',ylabel='相分离组 / 基线组：某一资源消耗比',title='条件分析｜什么情况下单位产物资源消耗才会下降？')
    ax.legend(loc='upper left');fig.colorbar(m,ax=ax,label='单位纯产物资源减少比例（%）；负值表示增加')
    save(fig,'resource_break_even')
    attr=[r for r in read(root,'results/tables/skincare/chemprop_atom_attribution.csv') if r['compound_id']=='15']
    fig,axs=plt.subplots(3,1,figsize=(12,9),layout='constrained',sharex=True,sharey=True)
    for ax,t in zip(axs,['AMES','Skin_Reaction','Carcinogens_Lagunin']):
        r=sorted([r for r in attr if r['task']==t],key=lambda r:int(r['atom_index']))
        means=np.array([float(v['mean']) for v in r]);sd=[float(v['std']) for v in r]
        ax.bar([int(v['atom_index']) for v in r],means,yerr=sd,color=['#a54d44' if m>=0 else '#416f87' for m in means],capsize=2)
        ax.axhline(0,color='#666',lw=.8);ax.set(title=TASKS[t],ylabel='对模型输出的贡献')
    axs[-1].set(xlabel='原子编号（对应保存的分子结构，起始编号为 0）',xticks=sorted({int(r['atom_index']) for r in attr}))
    fig.suptitle('Chemprop｜光甘草定原子归因均值与五成员差异',fontsize=16)
    save(fig,'atom_attribution')
    return out

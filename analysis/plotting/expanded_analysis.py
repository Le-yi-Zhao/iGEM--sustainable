"""Reproducible figures from cached predictions, literature counts and labeled scenarios."""
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from analysis.expanded_dashboard import load,CORE,NR,SR
from analysis.plotting.wiki_zh import TASKS

IDS=['9','10','11','13','14','15']
LABELS=['化合物 9','化合物 10','化合物 11','化合物 13','化合物 14','光甘草定']
COLORS=['#82958e']*5+['#aa5945']
def read(root,path):
    with (root/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def solvent_intensity(recovery,product_ratio):
    if not np.isfinite(recovery) or not 0<=recovery<=1 or not np.isfinite(product_ratio) or product_ratio<=0:raise ValueError('Invalid scenario')
    return (1-recovery)/product_ratio

def run(root):
    font=Path('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')
    if font.exists():
        font_manager.fontManager.addfont(str(font))
        plt.rcParams['font.family']=['DejaVu Sans',font_manager.FontProperties(fname=str(font)).get_name()]
    plt.rcParams.update({'axes.unicode_minus':False,'svg.fonttype':'path','svg.hashsalt':'galatea-expanded-20260930',
        'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fcfaf7','axes.facecolor':'#fcfaf7','savefig.facecolor':'#fcfaf7'})
    out=root/'figures/expanded_analysis';out.mkdir(parents=True,exist_ok=True)
    tables=root/'results/tables/environment';tables.mkdir(parents=True,exist_ok=True)
    def save(fig,name):
        p=out/(name+'.svg');fig.savefig(p,bbox_inches='tight',metadata={'Date':None})
        p.write_text('\n'.join(l.rstrip() for l in p.read_text().splitlines())+'\n')
        fig.savefig(out/(name+'.png'),dpi=170,bbox_inches='tight');plt.close(fig)
    _,compounds,lookup,_=load(root)
    names=[c['name_zh'] for c in compounds]
    fig,axes=plt.subplots(2,2,figsize=(13,13),layout='constrained')
    for ax,(m,t) in zip(axes.flat,CORE):
        rows=[lookup[c['id'],m,t] for c in compounds];mean=np.array([r['mean'] for r in rows]);sd=np.array([r['sd'] for r in rows])
        ax.barh(names,mean,xerr=np.stack([np.minimum(sd,mean),np.minimum(sd,1-mean)]),color=['#aa5945']+['#82958e']*15,capsize=2)
        ax.invert_yaxis();ax.set(xlim=(0,1.12),title=m+'｜'+TASKS[t],xlabel='阳性类别模型分数（非人体发生率）')
        for i,r in enumerate(rows):ax.text(min(r['mean']+r['sd']+.018,1.01),i,f'{r["mean"]:.3f}',va='center',fontsize=9)
    fig.suptitle('光甘草定与 15 种常见护肤原料｜模型均值与成员标准差',fontsize=16)
    save(fig,'expanded_core')
    tasks=NR+SR
    arr=np.array([[lookup[c['id'],m,t]['mean'] for m,t in tasks] for c in compounds])
    fig,ax=plt.subplots(figsize=(14,9.5),layout='constrained')
    im=ax.imshow(arr,vmin=0,vmax=1,cmap='YlOrBr',aspect='auto')
    for i in range(len(compounds)):
        for j in range(len(tasks)):ax.text(j,i,f'{arr[i,j]:.2f}',ha='center',va='center',fontsize=9,color='white' if arr[i,j]>.65 else '#302b27')
    ax.set(yticks=range(len(names)),yticklabels=names,xticks=range(len(tasks)),xticklabels=[t for _,t in tasks],title='ADMET-AI｜十二项受体与细胞应答信号，全部保留')
    ax.tick_params(axis='x',rotation=35);ax.axhline(.5,color='#aa5945',lw=2);ax.axvline(6.5,color='#fff',lw=3)
    fig.colorbar(im,ax=ax,label='特定试验活性模型分数（不构成综合安全等级）',shrink=.75)
    save(fig,'expanded_mechanisms')

    literature=json.loads((tables/'literature_topics.json').read_text())
    themes=list(literature['counts']);title=[literature['counts'][t]['title_match'] for t in themes];rest=[literature['counts'][t]['any_match']-title[i] for i,t in enumerate(themes)]
    fig,ax=plt.subplots(figsize=(11,5.4),layout='constrained')
    ax.barh(themes,title,color='#467e75',label='标题命中');ax.barh(themes,rest,left=title,color='#a6c1b5',label='仅抽取证据句命中')
    for i,t in enumerate(themes):n=literature['counts'][t]['any_match'];ax.text(n+.5,i,str(n),va='center')
    ax.set(xlabel='不同 DOI 数（多标签，同一篇可进入多个主题）',title=f'环境与资源主题｜全部 {literature["doi_count"]:,} 篇文献的可用文本')
    ax.set_xlim(0,max([a+b for a,b in zip(title,rest)]+[1])*1.2);ax.invert_yaxis();ax.legend(loc='lower right');save(fig,'environment_literature')

    epi=read(root,'data/processed/episuite_predictions.csv');vega=read(root,'data/processed/vega_predictions.csv');eco=read(root,'data/processed/ecosar_predictions.csv')
    plotted=[]
    def ep(cid,task):return float(next(r['value'] for r in epi if r['compound_id']==cid and r['endpoint']==task))
    panels=[('Predicted Log Kow','亲脂性｜log Kow','log10 比值',False),('Predicted Water Solubility, WSKow (mg/L)','水溶解度｜WSKow','mg/L，对数坐标',True),('Bioconcentration Factor (L/kg wet-wt)','生物富集因子｜BCF','L/kg 湿重，对数坐标',True),('BioWin6 (MITI Non-Linear Model Prediction)','快速生物降解｜BioWin6','模型分数，不是降解率',False)]
    fig,axes=plt.subplots(2,2,figsize=(13,8),layout='constrained')
    for ax,(task,title,label,log) in zip(axes.flat,panels):
        vals=[ep(i,task) for i in IDS];ax.scatter(vals,LABELS,c=COLORS,s=65);ax.invert_yaxis()
        if log:ax.set_xscale('log');ax.set_xlim(min(vals)/1.7,max(vals)*4)
        else:ax.set_xlim(min(0,min(vals))-.05,max(vals)*1.25+.05)
        for i,v in enumerate(vals):ax.annotate(f'{v:.3g}',(v,i),xytext=(8,0),textcoords='offset points',va='center',fontsize=10)
        ax.set(title=title,xlabel=label);ax.grid(axis='x',alpha=.2)
        plotted.extend({'figure':'environmental_fate','model':'EPI Suite','compound_id':i,'endpoint':task,'value':v,'unit':label,'warning':'适用域未导出','source':'data/processed/episuite_predictions.csv'} for i,v in zip(IDS,vals))
    fig.suptitle('环境归趋｜光甘草定与五个路径相关化合物（结构预测）',fontsize=16);save(fig,'environmental_fate')

    fig,axes=plt.subplots(1,3,figsize=(13,5.7),layout='constrained')
    rel={'LOW reliability':('#b46c50','低'),'MODERATE reliability':('#548b83','中等'),'HIGH reliability':('#395b74','高')}
    for ax,tag,title in zip(axes,['ALGAE_EC50','DAPHNIA_EC50','FISH_LC50'],['藻类 EC50','水蚤 EC50','鱼类 LC50']):
        vals=[]
        for i,cid in enumerate(IDS):
            r=next(r for r in vega if r['compound_id']==cid and r['model_tag']==tag)
            fields=json.loads(r['prediction_fields_json']);value=float(next(v for k,v in fields.items() if k.endswith('[mg/l]')))
            color,label=rel[r['reliability']];ax.scatter(value,i,c=color,s=90 if cid=='15' else 55,marker='D' if cid=='15' else 'o');vals.append(value)
            ax.annotate(f'{value:.3g} / {label}',(value,i),xytext=(7,0),textcoords='offset points',va='center',fontsize=9)
            plotted.append({'figure':'aquatic_toxicity','model':'VEGA','compound_id':cid,'endpoint':tag,'value':value,'unit':'mg/L','warning':r['reliability']+'; MW warning='+r['source_molecular_weight_warning'],'source':r['raw_report']})
        ax.set(xscale='log',xlim=(min(vals)/1.5,max(vals)*7),yticks=range(6),yticklabels=LABELS,title=title,xlabel='mg/L，对数坐标');ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
    fig.suptitle('VEGA 水生急性毒性｜数字后的“低／中等”是原报告可靠性',fontsize=15);save(fig,'aquatic_toxicity')

    fig,axes=plt.subplots(1,3,figsize=(13,5.7),layout='constrained')
    for ax,org,endpoint,title in zip(axes,['Fish','Daphnid','Green Algae'],['LC50','LC50','EC50'],['鱼类 96 h LC50','水蚤 48 h LC50','绿藻 96 h EC50']):
        vals=[]
        for i,cid in enumerate(IDS):
            r=next(r for r in eco if r['compound_id']==cid and r['QSAR Class']=='Neutral Organics' and r['Organism']==org and r['Endpoint']==endpoint)
            value=float(r['Concentration (mg/L)']);vals.append(value);flag=bool(r['Flags'])
            ax.scatter(value,i,c=COLORS[i],marker='x' if flag else 'o',s=70)
            ax.annotate(f'{value:.3g}',(value,i),xytext=(8,0),textcoords='offset points',va='center',fontsize=10)
            plotted.append({'figure':'ecosar_screening','model':'ECOSAR Neutral Organics','compound_id':cid,'endpoint':org+' '+r['Duration']+' '+endpoint,'value':value,'unit':'mg/L','warning':r['Flags']+'; '+r['domain_flag'],'source':'data/processed/ecosar_predictions.csv'})
        ax.set(xscale='log',xlim=(min(vals)/1.6,max(vals)*4),yticks=range(6),yticklabels=LABELS,title=title,xlabel='mg/L，对数坐标');ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
    fig.suptitle('ECOSAR｜同一化学类别内比较；叉号表示触发原始警告',fontsize=15);save(fig,'ecosar_screening')

    scenarios=[]
    fig,ax=plt.subplots(figsize=(10,6),layout='constrained');p=np.linspace(.75,3,91)
    for ratio in [.8,1,1.2,1.5,2]:
        y=ratio/p;ax.plot(p,y,lw=2,label=f'批次资源 ×{ratio:g}')
        scenarios.extend({'scenario':'resource_intensity','product_ratio':float(x),'batch_resource_ratio':ratio,'recovery_fraction':'','relative_intensity':float(v),'evidence_type':'CONDITIONAL_NOT_MEASURED'} for x,v in zip(p,y))
    ax.axhline(1,color='#343c39',ls='--',label='单位产物资源持平');ax.set(xlabel='纯产物质量比（新方案 / 基线）',ylabel='单位纯产物资源强度比',title='条件分析｜增产与资源增量的竞争',ylim=(0,2.8));ax.legend(ncol=2);ax.grid(alpha=.15);save(fig,'resource_sensitivity')
    fig,ax=plt.subplots(figsize=(10,6.6));fig.subplots_adjust(bottom=.22);recovery=np.linspace(0,.95,96)
    for ratio in [1,1.2,1.5,2]:
        y=[solvent_intensity(r,ratio) for r in recovery];ax.plot(recovery*100,y,lw=2,label=f'纯产物 ×{ratio:g}')
        scenarios.extend({'scenario':'fresh_solvent_steady_state','product_ratio':ratio,'batch_resource_ratio':1,'recovery_fraction':float(r),'relative_intensity':float(v),'evidence_type':'CONDITIONAL_NOT_MEASURED'} for r,v in zip(recovery,y))
    ax.set(xlabel='可有效复用的溶剂比例（%）',ylabel='单位纯产物新鲜溶剂需求比',title='条件分析｜回收与增产如何改变新鲜溶剂需求？',ylim=(0,1.05));ax.legend();ax.grid(alpha=.15)
    fig.text(.5,.025,'基线：不回收、产物比 1；同一批次总溶剂需求不变，稳态且回收液满足复用要求。\n公式：(1 − 有效回收率) / 纯产物比；未计回收能耗、启动库存和纯化损失。',ha='center',fontsize=10);save(fig,'solvent_recovery')

    fig,ax=plt.subplots(figsize=(13,6));ax.set(xlim=(0,13),ylim=(0,6));ax.axis('off')
    def box(x,y,w,h,text,color='#e0ebe4'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.12',facecolor=color,edgecolor='#648579'));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=11)
    def arrow(a,b,label=None):
        ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':'#536e64','lw':1.8})
        if label:ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.15,label,ha='center',fontsize=10)
    box(.3,3.1,2.4,1.2,'培养基／原料\n水、耗材、试剂')
    box(3.5,3.1,2.3,1.2,'培养与生产\n底物、时间、体积')
    box(6.7,3.1,2.3,1.2,'分离与纯化\n样品质量 × 纯度')
    box(10,3.1,2.6,1.2,'功能单位\n1 g 纯光甘草定','#d0e1ce')
    arrow((2.8,3.7),(3.35,3.7));arrow((5.95,3.7),(6.55,3.7));arrow((9.15,3.7),(9.85,3.7))
    box(3.5,.5,2.3,1.2,'废物流与处理\n浓度、体积、去除率','#efe0d4')
    box(6.7,.5,2.3,1.2,'溶剂回收与复用\n有效回收量、补加量')
    arrow((4.65,2.95),(4.65,1.85));arrow((7.85,2.95),(7.85,1.85));arrow((6.55,1.1),(5.95,1.1),'不可复用部分')
    ax.annotate('',xy=(9.15,3.2),xytext=(9.15,1.1),arrowprops={'arrowstyle':'->','connectionstyle':'arc3,rad=-.8','color':'#467e75','lw':1.8});ax.text(10.15,1.7,'回收能耗也计入',fontsize=10,ha='center')
    ax.text(6.5,5.35,'生产资源边界｜物料、电耗与废物处理一起记录',ha='center',fontsize=17)
    ax.text(6.5,4.8,'各阶段记录电耗；上游原料制造与设备制造暂未纳入完整生命周期边界',ha='center',fontsize=11)
    ax.text(.3,-.05,'流程示意：箭头没有数量权重，不是项目实测桑基图。',fontsize=10);save(fig,'production_boundary')
    for name,rows in [('environmental_plot_data.csv',plotted),('resource_plot_scenarios.csv',scenarios)]:
        with (tables/name).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    meta={'new_environment_resource_figures':7,'new_cosmetic_figures':2,'environment_compounds':IDS,'new_cosmetic_reference_environment_predictions':False,
        'environment_source':'Existing verified exports; no new environmental model inference in this update',
        'actual_resource_results':None,'resource_intensity_formula':'batch_resource_ratio / pure_product_ratio',
        'solvent_formula':'(1 - effective_recovery_fraction) / pure_product_ratio',
        'solvent_assumptions':['steady state','same gross batch solvent demand','usable recovered solvent','no recovery energy or startup inventory included'],
        'literature_counts':literature['counts'],'literal_counts_are_fulltext_search':False}
    (root/'results/summaries/environment_visuals.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':run(Path(__file__).resolve().parents[2])

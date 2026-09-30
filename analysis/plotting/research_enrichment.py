"""Chinese research outputs from source data; no invented project measurements."""
import csv, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

NAMES={9:'9｜Vestitol',10:'10｜甲基化前体',11:'11｜甲基化产物',13:'13｜去甲基前体',14:'14｜Preglabridin',15:'15｜光甘草定'}
COLORS={9:'#a7ac85',10:'#678b8f',11:'#8b7394',13:'#ccab59',14:'#a77755',15:'#215c4a'}
DOI='10.1038/s41467-026-68881-8'
SOURCE='https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM9_ESM.xlsx'

def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def efficacy_data():
    # Same-assay matched controls only; 2022 contributes two assays, not two studies.
    rows=[]
    for label,doi,g,k,ge,ke,method,locator in [
      ('2016｜酶活性','10.1016/j.saa.2016.06.008',.43,75.74,None,None,'蘑菇酪氨酸酶；原研究比色法','结果 Inhibitory effects；Fig. 2'),
      ('2022｜单酚酶','10.1016/j.foodchem.2022.133423',.080,33,.008,8,'蘑菇酪氨酸酶；1 mM 底物；氧传感／比色法','摘要'),
      ('2022｜二酚酶','10.1016/j.foodchem.2022.133423',.294,17,.025,3,'蘑菇酪氨酸酶；1 mM 底物；氧传感／比色法','摘要'),
      ('2024｜酶活性','10.3389/fphar.2024.1422310',.1,25.9,None,None,'蘑菇酪氨酸酶；L-酪氨酸底物','Table 4；Methods 2.5')]:
        rows.append(dict(assay=label,doi=doi,url='https://doi.org/'+doi,locator=locator,method=method,glabridin_ic50_uM=g,kojic_ic50_uM=k,glabridin_reported_pm_uM=ge,kojic_reported_pm_uM=ke,pm_type='摘要原文 ±；未据此构造置信区间' if ge else '所用结果位置未给误差',kojic_over_glabridin=k/g,evidence_type='EXTERNAL_LITERATURE_MEASURED'))
    return rows

def run(root):
    out=root/'results/tables/research_enrichment';out.mkdir(parents=True,exist_ok=True)
    figs=root/'figures/research_enrichment';figs.mkdir(parents=True,exist_ok=True)
    font=Path('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')
    if font.exists():
        font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=['DejaVu Sans',font_manager.FontProperties(fname=str(font)).get_name()]
    plt.rcParams.update({'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path','svg.hashsalt':'galatea-enrichment-v1','axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fcfaf7','axes.facecolor':'#fcfaf7','savefig.facecolor':'#fcfaf7'})
    generated=[]
    def save(fig,name):
        p=figs/(name+'.svg');fig.savefig(p,bbox_inches='tight',metadata={'Date':None})
        p.write_text('\n'.join(x.rstrip() for x in p.read_text().splitlines())+'\n')
        fig.savefig(figs/(name+'.png'),dpi=170,bbox_inches='tight');plt.close(fig);generated.append(name)
    eff=efficacy_data();write_csv(out/'efficacy_matched_assays.csv',eff)
    fig,ax=plt.subplots(figsize=(11,5.2),layout='constrained')
    for i,r in enumerate(eff):
        ax.plot([r['glabridin_ic50_uM'],r['kojic_ic50_uM']],[i,i],color='#becac2',lw=3)
        ax.scatter(r['glabridin_ic50_uM'],i,c='#215c4a',s=70,zorder=3,label='光甘草定' if i==0 else None)
        ax.scatter(r['kojic_ic50_uM'],i,c='#ad7252',s=70,zorder=3,label='曲酸' if i==0 else None)
        ax.annotate(f"{r['glabridin_ic50_uM']:g}",(r['glabridin_ic50_uM'],i),xytext=(0,10),textcoords='offset points',ha='center')
        ax.annotate(f"{r['kojic_ic50_uM']:g}",(r['kojic_ic50_uM'],i),xytext=(0,10),textcoords='offset points',ha='center')
    ax.set(xscale='log',xlim=(.04,200),ylim=(-.55,3.65),yticks=range(4),yticklabels=[r['assay'] for r in eff],xlabel='IC50（μmol/L；对数坐标，越低表示该酶试验中抑制活性越强）',title='同研究、同试验比较｜四组酶抑制浓度，来自三篇论文')
    ax.invert_yaxis();ax.legend(loc='lower right');ax.grid(axis='x',alpha=.15)
    save(fig,'efficacy_ic50')
    fig,ax=plt.subplots(figsize=(11,5),layout='constrained')
    ratios=[r['kojic_over_glabridin'] for r in eff]
    ax.barh([r['assay'] for r in eff],ratios,color='#678f7c');ax.invert_yaxis()
    for i,x in enumerate(ratios):ax.text(x+7,i,f'{x:.1f}',va='center')
    ax.set(xlim=(0,490),xlabel='同次试验：曲酸 IC50 ÷ 光甘草定 IC50（描述性倍数）',title='优势有适用条件｜不汇总成“人体美白强多少倍”')
    save(fig,'efficacy_ratio')

    source=root/'data/raw/literature/zhang_2026_source_data.xlsx'
    rows=[]
    for sheet,ids,condition in [('Fig. 4d',[13,9,14,10,15,11],'NhPDA1 多路径体系'),('Fig. 4e',[9,13,14,15],'GgDMT1 单路径体系')]:
        frame=pd.read_excel(source,sheet_name=sheet,header=None)
        for ri in range(3,len(frame)):
            for j,c in enumerate(ids):
                for rep in range(3):
                    value=frame.iloc[ri,2+3*j+rep]
                    rows.append(dict(doi=DOI,sheet=sheet,condition=condition,time_h=float(frame.iloc[ri,1]),compound_id=c,replicate=rep+1,concentration_mg_L=None if pd.isna(value) else float(value),source_excel_row=ri+1,source_excel_column=2+3*j+rep+1,evidence_type='EXTERNAL_LITERATURE_MEASURED'))
    write_csv(out/'production_replicates.csv',rows)
    df=pd.DataFrame(rows)
    summary=df.groupby(['sheet','condition','time_h','compound_id']).concentration_mg_L.agg(['mean','std','count']).reset_index()
    summary.to_csv(out/'production_time_summary.csv',index=False,encoding='utf-8-sig')
    for sheet,filename in [('Fig. 4d','production_multiroute'),('Fig. 4e','production_singleroute')]:
        sub=summary[summary.sheet==sheet]
        fig,axes=plt.subplots(2,3 if sheet.endswith('d') else 2,figsize=(12,7.5),layout='constrained')
        for ax,c in zip(axes.flat,sorted(sub.compound_id.unique())):
            s=sub[sub.compound_id==c]
            ax.errorbar(s.time_h,s['mean'],yerr=s['std'],fmt='o-',color=COLORS[c],lw=1.5,capsize=3,label='均值 ± 样本标准差')
            raw=df[(df.sheet==sheet)&(df.compound_id==c)]
            ax.scatter(raw.time_h+(raw.replicate-2)*.7,raw.concentration_mg_L,color=COLORS[c],s=12,alpha=.5,label='原始重复')
            ax.set(title=NAMES[c],xlabel='培养时间（h）',ylabel='浓度（mg/L）',ylim=(0,None));ax.grid(alpha=.12)
        fig.suptitle(sub.condition.iloc[0]+'｜外部文献原始重复数据',fontsize=15)
        save(fig,filename)
    # Snapshot composition only: not a flux, carbon balance or conversion yield.
    comp=[]
    fig,ax=plt.subplots(figsize=(11,5),layout='constrained')
    for i,(sheet,time) in enumerate([('Fig. 4d',120),('Fig. 4e',120)]):
        s=summary[(summary.sheet==sheet)&(summary.time_h==time)];total=s['mean'].sum();left=0
        for c in [9,10,11,13,14,15]:
            rr=s[s.compound_id==c]
            if rr.empty:continue
            value=float(rr['mean'].iloc[0]);share=value/total*100
            comp.append(dict(sheet=sheet,time_h=time,compound_id=c,mean_mg_L=value,measured_pool_total_mg_L=float(total),mass_share_percent=share,denominator='本面板已测化合物均值之和；各面板覆盖不同，不是总代谢物、总碳或转化率'))
            ax.barh(i,share,left=left,color=COLORS[c],label=NAMES[c] if i==0 else None)
            if share>7:ax.text(left+share/2,i,f'{c}\n{share:.1f}%',ha='center',va='center',color='white' if c in [10,11,14,15] else '#252a25')
            left+=share
        target=float(s[s.compound_id==15]['mean'].iloc[0]);ax.text(102,i,f'光甘草定\n{target:.3f} mg/L\n占 {target/total*100:.1f}%',va='center')
    ax.set(xlim=(0,125),yticks=[0,1],yticklabels=['多路径｜6 种已测物','单路径｜4 种已测物'],xticks=[0,25,50,75,100],xlabel='120 h 已测物质量浓度构成（%）',title='生产瓶颈线索｜目标产物以外仍有中间体积累')
    ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.20),frameon=False)
    write_csv(out/'production_pool_composition.csv',comp);save(fig,'production_composition')

    extraction=[]
    for solvent,p,sd in [('100% 甲醇',.72,.020),('80% 甲醇水溶液',.55,.005),('100% 乙醇',1.93,.080),('95% 乙醇水溶液',.96,.009),('90% 乙醇水溶液',.56,.040),('80% 乙醇水溶液',.53,.010),('100% 丙酮',4.27,.270)]:
        extraction.append(dict(solvent=solvent,purity_wt_percent=p,purity_sd=sd,crude_extract_g_per_g_contained_glabridin=100/p,source_url='https://www.jstage.jst.go.jp/article/apcche/2004/0/2004_0_587/_pdf',locator='Cho et al. 2004, Table 1, PDF page 3',n=3,evidence_type='EXTERNAL_LITERATURE_AND_DERIVED',limit='提取物中含有 1 g 光甘草定所对应的粗提物质量；未计纯化损失，不是已分离纯品的产率或环境足迹'))
    write_csv(out/'extraction_purity.csv',extraction)
    fig,(a,b)=plt.subplots(1,2,figsize=(12,5.6),layout='constrained',sharey=True)
    labels=[r['solvent'] for r in extraction]
    a.barh(labels,[r['purity_wt_percent'] for r in extraction],xerr=[r['purity_sd'] for r in extraction],color='#6e9583',capsize=3)
    b.barh(labels,[r['crude_extract_g_per_g_contained_glabridin'] for r in extraction],color='#b78b68')
    a.invert_yaxis();a.set(xlabel='粗提物纯度（质量 %，均值 ± SD）',title='文献实测｜同研究七种提取条件')
    b.set(xlabel='粗提物 g / 其中含有的 1 g 光甘草定',title='由平均纯度推算｜100 ÷ 纯度百分数')
    for i,r in enumerate(extraction):b.text(r['crude_extract_g_per_g_contained_glabridin']+2,i,f"{r['crude_extract_g_per_g_contained_glabridin']:.1f}",va='center',fontsize=10)
    b.set_xlim(0,225);save(fig,'extraction_purity')
    scenarios=[];titers=[.1,.5,1,5,10,50,100];recoveries=[.3,.5,.7,.9]
    volumes=np.array([[1000/(t*r) for t in titers] for r in recoveries])
    for i,r in enumerate(recoveries):
        for j,t in enumerate(titers):scenarios.append(dict(titer_mg_L=t,overall_product_recovery=r,pure_product_g=1,broth_L=float(volumes[i,j]),evidence_type='CONDITIONAL_CALCULATION',formula='1000 / (titer_mg_L * overall_product_recovery)'))
    write_csv(out/'broth_volume_scenarios.csv',scenarios)
    fig,ax=plt.subplots(figsize=(12,5),layout='constrained')
    ax.imshow(np.log10(volumes),cmap='YlOrBr',aspect='auto')
    for i in range(4):
        for j in range(7):ax.text(j,i,f'{volumes[i,j]:,.1f} L',ha='center',va='center',color='white' if volumes[i,j]>4000 else '#332a23')
    ax.set(xticks=range(7),xticklabels=titers,yticks=range(4),yticklabels=[f'{r:.0%}' for r in recoveries],xlabel='假设发酵液光甘草定浓度（mg/L）',ylabel='假设总回收率',title='条件计算｜获得 1 g 纯光甘草定需要处理多少发酵液？')
    save(fig,'broth_volume')
    meta={'efficacy_assays':4,'efficacy_distinct_papers':3,'time_series_rows':len(rows),'time_series_observed_values':int(df.concentration_mg_L.notna().sum()),'missing_values':int(df.concentration_mg_L.isna().sum()),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_url':SOURCE,'extraction_conditions':7,'resource_scenarios':len(scenarios),'figure_names':generated,'scope':'定向补充原始研究；不是穷尽式系统综述。原数据库未按质量再次筛选。','limits':['2022 两个酶试验来自同篇论文，未做跨研究合并效应。','时间序列只重画外部文献原始重复；缺失保持缺失，零值保留原记录。','误差线不是项目湿实验或人体风险区间。','浓度构成不是物质通量、碳平衡或转化率；面板覆盖不同。','粗提物换算不包含后续纯化回收率。']}
    dump(root/'results/summaries/research_enrichment.json',meta)
    return meta

if __name__=='__main__':print(json.dumps(run(Path(__file__).resolve().parents[2]),ensure_ascii=False,indent=2))

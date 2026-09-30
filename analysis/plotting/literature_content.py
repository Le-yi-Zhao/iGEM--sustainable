"""Publication-sized Chinese corpus figures, including mass-conserving Sankey diagrams."""
import json
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch,Rectangle

COLORS=['#397a6b','#a36f4b','#6489a0','#947ba7','#aa6370','#8d9571','#b89752','#727f8d','#a8a8a0','#597781','#b29e90']

def sankey(ax,papers,columns,titles):
    n=len(papers); counts=[Counter(p[c] for p in papers) for c in columns]
    orders=[sorted(c,key=lambda k:(-c[k],k)) for c in counts]
    gap=.025;scale=(1-gap*(max(map(len,orders))-1))/n
    positions=[];palette={};width=.026
    for stage,order in enumerate(orders):
        pos={};top=1.;x=stage/(len(columns)-1)
        for i,label in enumerate(order):
            h=counts[stage][label]*scale;pos[label]=(x,top,h)
            palette[stage,label]=COLORS[i%len(COLORS)]
            top-=h+gap
        positions.append(pos)
    for stage in range(len(columns)-1):
        flow=Counter((p[columns[stage]],p[columns[stage+1]]) for p in papers)
        used_left=Counter();used_right=Counter()
        for a in orders[stage]:
            for b in orders[stage+1]:
                value=flow[a,b]
                if not value:continue
                x0,y0,_=positions[stage][a];x0+=width
                x1,y1,_=positions[stage+1][b]
                y0-=used_left[a]*scale;y1-=used_right[b]*scale;h=value*scale
                mid=(x0+x1)/2
                verts=[(x0,y0),(mid,y0),(mid,y1),(x1,y1),(x1,y1-h),(mid,y1-h),(mid,y0-h),(x0,y0-h),(x0,y0)]
                codes=[MPath.MOVETO,*([MPath.CURVE4]*3),MPath.LINETO,*([MPath.CURVE4]*3),MPath.CLOSEPOLY]
                ax.add_patch(PathPatch(MPath(verts,codes),facecolor=palette[stage,a],alpha=.27,lw=0))
                used_left[a]+=value;used_right[b]+=value
    for stage,order in enumerate(orders):
        x=stage/(len(columns)-1)
        ax.text(x+width/2,1.065,titles[stage],ha='center',fontsize=14,fontweight='bold')
        for label in order:
            x,y,h=positions[stage][label]
            ax.add_patch(Rectangle((x,y-h),width,h,facecolor=palette[stage,label],lw=0))
            if stage==0:tx=x-.012;ha='right'
            elif stage==len(columns)-1:tx=x+width+.012;ha='left'
            else:tx=x+width/2;ha='center'
            ax.text(tx,y-h/2,f'{label}  {counts[stage][label]}',ha=ha,va='center',fontsize=10,
                bbox={'facecolor':'#fcfaf7','edgecolor':'none','alpha':.92,'pad':2})
    ax.set(xlim=(-.31,1.34),ylim=(-.035,1.13));ax.axis('off')

def run(root:Path):
    papers=json.loads((root/'results/tables/literature_content/papers.json').read_text())
    s=json.loads((root/'results/summaries/literature_content.json').read_text())
    font=Path('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')
    font_manager.fontManager.addfont(str(font))
    plt.rcParams.update({'font.family':['DejaVu Sans',font_manager.FontProperties(fname=str(font)).get_name()],
        'axes.unicode_minus':False,'svg.fonttype':'path','svg.hashsalt':'galatea-literature-content-v1',
        'font.size':11,'figure.facecolor':'#fcfaf7','axes.facecolor':'#fcfaf7','savefig.facecolor':'#fcfaf7',
        'axes.spines.right':False,'axes.spines.top':False})
    out=root/'figures/literature_content';out.mkdir(parents=True,exist_ok=True)
    def save(fig,name):
        p=out/(name+'.svg');fig.savefig(p,bbox_inches='tight',metadata={'Date':None})
        p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n',encoding='utf-8')
        fig.savefig(out/(name+'.png'),dpi=160,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(17,9),layout='constrained')
    sankey(ax,papers,['host','family','system'],['研究宿主','研究对象','反应体系'])
    fig.suptitle(f'文献研究版图｜{len(papers):,} 篇文献的宿主—对象—体系',fontsize=19)
    fig.supxlabel('流带宽度 = 不同 DOI 数；每篇在每一列只计一次。展示研究关联，不表示物质流或因果关系。',fontsize=11)
    save(fig,'corpus_sankey')
    fig,axs=plt.subplots(1,2,figsize=(14,6.8),layout='constrained')
    for ax,field,title in zip(axs,['family','host'],['研究对象的分布','研究宿主的分布']):
        counts=s['counts'][field];labels=list(counts);values=list(counts.values())
        ax.barh(labels,values,color=[COLORS[i%len(COLORS)] for i in range(len(labels))]);ax.invert_yaxis()
        for i,v in enumerate(values):ax.text(v+8,i,f'{v}（{v/len(papers):.1%}）',va='center',fontsize=10)
        ax.set(xlim=(0,max(values)*1.32),xlabel='不同 DOI 数',title=title)
    fig.suptitle('研究对象与底盘选择｜以完整文献库为分母',fontsize=18)
    save(fig,'research_distribution')
    families=list(s['counts']['family']);hosts=list(s['counts']['host'])
    a=np.array([[sum(p['family']==f and p['host']==h for p in papers) for h in hosts] for f in families])
    fig,ax=plt.subplots(figsize=(12.5,8),layout='constrained')
    for i in range(len(families)):
        for j in range(len(hosts)):
            v=a[i,j]
            if v:ax.scatter(j,i,s=v*5+20,c=[v],cmap='YlGnBu',vmin=0,vmax=a.max(),alpha=.85,edgecolors='#475c57',linewidths=.3)
            ax.text(j,i,str(v),ha='center',va='center',fontsize=9,color='white' if v>140 else '#22372c')
    ax.set(xticks=range(len(hosts)),xticklabels=hosts,yticks=range(len(families)),yticklabels=families,
        title='研究对象 × 宿主｜圆面积随文献数增加',xlim=(-.7,len(hosts)-.3),ylim=(len(families)-.3,-.7))
    ax.tick_params(axis='x',rotation=35);ax.grid(alpha=.15)
    save(fig,'host_object_matrix')
    topics=s['strategy_order'];pos=np.arange(len(topics));allv=[s['counts']['strategies'][t] for t in topics];titles=[s['counts']['title_strategies'][t] for t in topics]
    fig,ax=plt.subplots(figsize=(12,7),layout='constrained')
    ax.barh(pos+.17,allv,height=.32,color='#9db8ad',label='标题或已抽取证据句提及')
    ax.barh(pos-.17,titles,height=.32,color='#397a6b',label='仅标题提及')
    for i,(v,t) in enumerate(zip(allv,titles)):
        ax.text(v+2,i+.17,str(v),va='center');ax.text(t+2,i-.17,str(t),va='center')
    ax.set(yticks=pos,yticklabels=topics,xlim=(0,max(allv)*1.23),xlabel='不同 DOI 数（可多主题）',title='工程策略与环境主题｜从单酶优化到空间组织')
    ax.invert_yaxis();ax.legend(loc='lower right',fontsize=10)
    save(fig,'strategy_mentions')
    a=np.array(s['cooccurrence']);fig,ax=plt.subplots(figsize=(12,9),layout='constrained')
    img=ax.imshow(a,cmap='YlGnBu')
    for i in range(len(topics)):
        for j in range(len(topics)):ax.text(j,i,str(a[i,j]),ha='center',va='center',color='white' if a[i,j]>80 else '#20382b')
    ax.set(xticks=range(len(topics)),xticklabels=topics,yticks=range(len(topics)),yticklabels=topics,title='研究主题共现｜同篇文献的证据关联')
    plt.setp(ax.get_xticklabels(),rotation=35,ha='right');fig.colorbar(img,ax=ax,label='共同提及的不同 DOI 数',shrink=.75)
    save(fig,'strategy_cooccurrence')
    keys=sorted([k for k in s['overlap'] if k!='000'],key=lambda k:(-s['overlap'][k],k))
    fig,(ax,mat)=plt.subplots(2,1,figsize=(11,7),height_ratios=[3,1.25],sharex=True,layout='constrained')
    ax.bar(range(len(keys)),[s['overlap'][k] for k in keys],color=['#a36f4b' if k=='111' else '#397a6b' for k in keys])
    for i,k in enumerate(keys):ax.text(i,s['overlap'][k]+9,str(s['overlap'][k]),ha='center')
    ax.set(ylabel='互斥交集的 DOI 数',ylim=(0,max(s['overlap'][k] for k in keys)*1.15),title='项目交叉位置｜黄酮相关 × 酵母相关 × 空间组织')
    for i,k in enumerate(keys):
        active=[j for j,b in enumerate(k) if b=='1']
        if len(active)>1:mat.plot([i,i],[min(active),max(active)],color='#397a6b',lw=2)
        for j,b in enumerate(k):mat.scatter(i,j,color='#397a6b' if b=='1' else '#dce3de',s=80)
    mat.set(yticks=[0,1,2],yticklabels=['黄酮／异黄酮相关','酵母相关','空间组织相关'],ylim=(2.5,-.5),xticks=[])
    mat.spines[['bottom','left']].set_visible(False)
    fig.supxlabel(f'实心点表示该列所属集合；未命中三集合的 {s["overlap"].get("000",0)} 篇未绘入。各列为互斥计数。',fontsize=10)
    save(fig,'project_intersections')
    phase=[p for p in papers if p['phase_title']]
    fig,ax=plt.subplots(figsize=(14,7),layout='constrained')
    sankey(ax,phase,['phase_class','host'],['相分离文献应用方向','源表主宿主标签'])
    fig.suptitle(f'相分离研究的应用分布｜标题明确提及的 {len(phase)} 篇文献',fontsize=18)
    fig.supxlabel('每篇只计一次；基础机制、材料、方法和生物合成分开呈现。',fontsize=11)
    save(fig,'condensate_sankey')
    # A matched comparison explicitly present in the supplied database; not a meta-analysis.
    case=json.loads((root/'results/tables/literature_content/quantitative_examples.json').read_text())
    values=[case['control'],case['condensate']]
    fig,ax=plt.subplots(figsize=(8,5.2),layout='constrained')
    bars=ax.bar(['游离酶对照','凝聚体体系'],values,color=['#a8b7b0','#397a6b'],width=.55)
    for b,v in zip(bars,values):ax.text(b.get_x()+b.get_width()/2,v+.1,f'{v:.1f}',ha='center',fontsize=14)
    ax.set(ylabel='1 小时甘氨酸浓度（mmol/L）',ylim=(0,6.3),title='数据库中的定量例证｜同一研究内的空间组织比较')
    ax.text(.5,5.85,f'{values[1]:.1f} ÷ {values[0]:.1f} ≈ {values[1]/values[0]:.2f} 倍',ha='center',fontsize=14,color='#315e4e')
    fig.supxlabel('文献 DOI：10.1016/j.jcou.2025.103269\n无细胞甘氨酸体系；非光甘草定实验。原抽取记录未给出此对比的误差条。',fontsize=10)
    save(fig,'matched_condensate_example')
    return out

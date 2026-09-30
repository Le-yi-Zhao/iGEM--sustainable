"""Analyze OPERA output without concealing failed or out-of-domain endpoints."""
import json,re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import ListedColormap
from analysis.enrichment_section import fig,table

ENDPOINTS=[('LogP_pred','LogP','亲脂性 logP','log10 比值'),('LogWS_pred','WS','水溶解度 logS','log10(mol/L)'),('LogBCF_pred','BCF','鱼体富集 logBCF','log10(L/kg)'),('ReadyBiodeg_pred','ReadyBiodeg','易生物降解','二分类 0/1'),('LogKM_pred','KM','鱼体生物转化半衰期','log10(天)'),('LogKoc_pred','Koc','土壤吸附 logKoc','log10(L/kg)')]

def run(root):
    raw=root/'data/raw/skincare/opera';d=pd.read_csv(raw/'predictions.csv')
    manifest=json.loads((raw/'input_manifest.json').read_text());names={x['id']:x['name_zh'] for x in manifest['structures']}
    assert d.MoleculeID.tolist()==list(names)
    rows=[]
    for r in d.to_dict('records'):
        for col,key,label,unit in ENDPOINTS:
            rows.append(dict(id=r['MoleculeID'],name_zh=names[r['MoleculeID']],endpoint=key,label_zh=label,value=r[col],unit=unit,global_ad=r['AD_'+key],local_ad=r['AD_index_'+key],confidence_index=r['Conf_index_'+key],status='计算缺失' if pd.isna(r[col]) else ('模型全局域内' if r['AD_'+key]==1 else '模型全局域外'),native_pred_range=r.get(('LogP' if key=='LogP' else key)+'_predRange',''),evidence_type='PREDICTED'))
    frame=pd.DataFrame(rows);out=root/'results/tables/research_enrichment';frame.to_csv(out/'opera_all_endpoints_zh.csv',index=False,encoding='utf-8-sig')
    f=Path('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')
    if f.exists():font_manager.fontManager.addfont(str(f));plt.rcParams['font.family']=['DejaVu Sans',font_manager.FontProperties(fname=str(f)).get_name()]
    plt.rcParams.update({'font.size':10,'axes.unicode_minus':False,'svg.fonttype':'path','svg.hashsalt':'galatea-opera-v1','axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fcfaf7','axes.facecolor':'#fcfaf7','savefig.facecolor':'#fcfaf7'})
    def save(f,name):
        p=root/'figures/research_enrichment'/f'{name}.svg';f.savefig(p,bbox_inches='tight',metadata={'Date':None});p.write_text('\n'.join(l.rstrip() for l in p.read_text().splitlines())+'\n');f.savefig(p.with_suffix('.png'),dpi=170,bbox_inches='tight');plt.close(f)
    panel=d.iloc[:16]
    f,axes=plt.subplots(2,2,figsize=(14,12),layout='constrained')
    for ax,(col,key,label,unit) in zip(axes.flat,[ENDPOINTS[i] for i in [0,1,2,5]]):
        v=panel[col];y=np.arange(len(panel));finite=v.notna().to_numpy();outside=(panel['AD_'+key]!=1).to_numpy()
        ax.scatter(v[finite],y[finite],c=np.array(['#aa5945']+['#668e7b']*15)[finite],s=42)
        bad=finite&outside;ax.scatter(v[bad],y[bad],marker='x',c='#8d543f',s=85)
        for j in np.flatnonzero(~finite):ax.text(.98,j,'缺失',transform=ax.get_yaxis_transform(),ha='right',color='#8d543f')
        ax.set(yticks=y,yticklabels=[names[i] for i in panel.MoleculeID],xlabel=unit,title=label);ax.invert_yaxis();ax.grid(axis='x',alpha=.12)
    f.suptitle('OPERA｜光甘草定与 15 种护肤参照；叉号为全局域外预测',fontsize=15);save(f,'opera_properties')
    ad=np.array([[(-1 if pd.isna(r[col]) else int(r['AD_'+key])) for col,key,_,_ in ENDPOINTS] for r in d.to_dict('records')])
    f,ax=plt.subplots(figsize=(12,11),layout='constrained');ax.imshow(ad,cmap=ListedColormap(['#e0ded8','#d6ae93','#719682']),vmin=-1,vmax=1,aspect='auto')
    for i in range(len(d)):
        for j in range(6):
            k=ENDPOINTS[j][1];text='缺失' if ad[i,j]==-1 else ('域内' if ad[i,j]==1 else '域外')+f"\n局部 {d.iloc[i]['AD_index_'+k]:.2f}"
            ax.text(j,i,text,ha='center',va='center',fontsize=8.5,color='#22382e')
    ax.set(yticks=range(len(d)),yticklabels=[names[i] for i in d.MoleculeID],xticks=range(6),xticklabels=[r[2] for r in ENDPOINTS],title='适用域与缺失｜颜色为全局域；数字为原生局部域指数')
    ax.tick_params(axis='x',rotation=15);ax.axhline(15.5,color='#fff',lw=3);save(f,'opera_domain')
    f,ax=plt.subplots(figsize=(12,7),layout='constrained');vals=panel.ReadyBiodeg_pred
    for i,r in panel.iterrows():
        missing=pd.isna(r.ReadyBiodeg_pred);positive=r.ReadyBiodeg_pred==1
        ax.barh(i,1,color='#ddd9d2' if missing else '#729886' if positive else '#c08e69',height=.7)
        label='计算缺失' if missing else '预测易降解' if positive else '预测非易降解'
        if not missing:label+=f"｜全局域{'内' if r.AD_ReadyBiodeg==1 else '外'}；局部指数 {r.AD_index_ReadyBiodeg:.2f}"
        ax.text(.025,i,label,va='center',fontsize=10)
    ax.set(yticks=range(16),yticklabels=[names[i] for i in panel.MoleculeID],xticks=[],xlim=(0,1),title='OPERA 易生物降解分类｜不是实际降解百分数或降解速度');ax.invert_yaxis();save(f,'opera_biodegradation')
    g=d.iloc[0];bad=frame[frame.status=='计算缺失']
    page='''<h3 id="opera">OPERA 新运行｜把护肤参照扩展到环境归趋</h3><p>本次实际运行 OPERA 2.9.5 发布包，处理光甘草定、15 种护肤参照与 5 个路径中间体，共 21 种分子。事前选择 6 项理化／环境终点，未按输出好坏删选。原始输出包含近邻、全局适用域、局部域指数与准确度估计。</p>'''
    page+=f'<p>126 个目标输出中，123 个有数值、3 个缺失，缺失均为尿素的易降解、鱼体转化和土壤吸附任务。尿素单分子重算仍在降解描述符处报错；这些项目没有填成阴性。BioDeg 半衰期模型仅适用于烃类，本轮事前排除；KM 是鱼体转化，不能当作环境降解时间。</p>'
    grows=[]
    for r in frame[frame.id=='glabridin'].to_dict('records'):grows.append([r['label_zh'],'预测非易降解（0）' if r['endpoint']=='ReadyBiodeg' else f"{r['value']:.2f}",r['unit'],r['status'],f"{r['local_ad']:.2f}",f"{r['confidence_index']:.2f}"])
    page+=table(['光甘草定终点','原生预测','单位','全局域','局部域指数','准确度指数'],grows)
    page+='<p>“全局域内”不等于高可信或安全。光甘草定局部指数只有约 0.30–0.57，近邻与目标的相似性仍有限；准确度指数也不是人体安全概率。模型原生预测范围保留在原始表中，不当作统一置信区间。</p>'
    page+=fig('opera_properties','16 种分子的四项连续输出；不同小图不能直接平均。叉号保留全局域外点，缺失单独注明。logP 与此前 ADMET-AI 的 Lipophilicity 任务定义不同，不直接拼成一条排名。')
    page+=fig('opera_domain','21 种分子 × 6 终点的适用域图；分隔线以下是路径中间体。域内、域外与计算缺失分别标示，局部指数按原始输出显示。')
    page+=fig('opera_biodegradation','易降解分类只是模型给出的试验类别；不能读成 0% 或 100% 的降解率，更不能据此确定排放浓度。')
    page+=f'<p><b>新增模型带来的结论：</b>OPERA 对光甘草定给出 logBCF={g.LogBCF_pred:.2f}（换算约 {10**g.LogBCF_pred:.1f} L/kg），与既有 EPI Suite 约 1,542 L/kg 存在明显模型差异，不能择取较低值作为环境安全证明。预测非易降解则延续了原有需要关注降解与废物流的线索。此结果加强了回收与排放控制的研究必要性。</p>'
    page+='<p>方法来源：<a href="https://github.com/kmansouri/OPERA">OPERA 官方模型说明</a>。LogP、WS 模型版本为 2.9，其余本轮四个环境模型版本为 2.6；以实际程序版本清单为准。</p><div class="downloads"><a href="results/tables/research_enrichment/opera_all_endpoints_zh.csv">全部 126 项及缺失／适用域状态</a><a href="data/raw/skincare/opera/predictions.csv">OPERA 原始输出与近邻数据</a><a href="data/raw/skincare/opera/run_metadata.json">运行命令、版本与输入校验</a><a href="docs/methodology/research_enrichment_20260930.md">新增分析的完整复现说明</a></div>'
    (root/'results/summaries/opera_section.html').write_text(page,encoding='utf-8')
    return dict(molecules=21,endpoints=6,available=int(frame.value.notna().sum()),missing=len(bad))

def integrate(root,page):
    block=(root/'results/summaries/opera_section.html').read_text()
    return re.sub(r'(<section class="section" id="environment">.*?)(</section>)',lambda m:m[1]+block+m[2],page,flags=re.S)

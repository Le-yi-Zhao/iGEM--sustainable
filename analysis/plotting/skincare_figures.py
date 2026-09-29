"""Use-specific charts; native assays and model semantics stay separate."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from analysis.models.skincare_evaluation import SAR_CORE
from analysis.models.skincare_scope import ATTRIBUTION_TASKS, MECHANISTIC

def save(fig, folder, name):
    fig.savefig(folder/(name+'.svg'),bbox_inches='tight',metadata={'Date':None})
    fig.savefig(folder/(name+'.png'),bbox_inches='tight',dpi=170)
    plt.close(fig)

def run(root):
    folder=root/'figures/skincare';folder.mkdir(parents=True,exist_ok=True)
    with plt.rc_context({'svg.hashsalt':'galatea-skincare','font.family':'DejaVu Sans'}):
        sar=pd.read_csv(root/'data/processed/admetsar_predictions.csv').set_index('compound_id')
        fields=list(SAR_CORE)
        values=sar[fields].astype(float).T
        fig,ax=plt.subplots(figsize=(10,7.5))
        im=ax.imshow(values,aspect='auto',vmin=0,vmax=1,cmap='Blues')
        ax.set_xticks(range(len(values.columns)),[str(c)+(' (glabridin)' if c==15 else '') for c in values.columns])
        ax.set_yticks(range(len(fields)),[SAR_CORE[f] for f in fields])
        for y in range(len(fields)):
            for x in range(len(values.columns)):
                v=values.iloc[y,x];ax.text(x,y,f'{v:.2f}',ha='center',va='center',color='white' if v>.6 else '#16324a')
        ax.set_title('Skincare ingredient screening: local, photo and genetic endpoints',loc='left',pad=20)
        fig.colorbar(im,ax=ax,label='admetSAR native classification score')
        fig.text(.015,.02,'PREDICTED | Verified prior web batch; newly selected by dermal-use relevance. No cosmetic safety cutoff.\n15: target ingredient. Other compounds: pathway / potential-impurity references, not measured product impurities.\nPhoto endpoints are distinct assays; a low score does not establish photostability or finished-product safety.',fontsize=9)
        fig.tight_layout(rect=(0,.12,1,1));save(fig,folder,'local_and_photo_endpoints')

        comparison=pd.read_csv(root/'results/tables/skincare/platform_comparison.csv')
        glab=comparison.loc[comparison.compound_id==15]
        fig,axes=plt.subplots(1,3,figsize=(13,5.5),sharey=True)
        models=['admet_ai','admetlab','admetsar','maplight'];colors=['#6946a4','#4183a9','#409288','#b67835']
        for ax,(_,row) in zip(axes,glab.iterrows()):
            present=[(m,c) for m,c in zip(models,colors) if pd.notna(row[m])]
            ax.bar(range(len(present)),[row[m] for m,c in present],color=[c for m,c in present])
            for i,(m,c) in enumerate(present):ax.text(i,row[m]+.025,f'{row[m]:.3f}',ha='center',fontsize=10)
            ax.set_xticks(range(len(present)),[m.replace('_','-') for m,c in present],rotation=30,ha='right')
            ax.set_title(row.endpoint.replace('_',' '));ax.set_ylim(0,1.1);ax.spines[['top','right']].set_visible(False)
        axes[0].set_ylabel('Native model classification score')
        fig.suptitle('Glabridin: preserve platform differences',x=.07,ha='left',fontsize=16)
        fig.text(.015,.025,'PREDICTED | Side-by-side context only. No averaging, vote or shared safety threshold.\nSkin and carcinogenicity assays differ across platforms; model agreement is not independent experimental validation.',fontsize=10)
        fig.tight_layout(rect=(0,.12,1,.93));save(fig,folder,'glabridin_platform_comparison')

        attrs=pd.read_csv(root/'results/tables/skincare/chemprop_atom_attribution.csv')
        manifest=pd.read_csv(root/'data/compounds/compound_manifest.csv')
        molecule=Chem.MolFromSmiles(manifest.loc[manifest.compound_id==15,'canonical_smiles'].iloc[0])
        attrs=attrs.loc[attrs.compound_id==15];scale=max(attrs['mean'].abs().max(),1e-10)
        drawer=rdMolDraw2D.MolDraw2DSVG(1500,430,500,430)
        drawer.drawOptions().legendFontSize=19;drawer.drawOptions().addAtomIndices=True
        colors=[]
        for task in ATTRIBUTION_TASKS:
            subset=attrs.loc[attrs.task==task]
            colors.append({int(r.atom_index):tuple(plt.cm.RdBu_r(.5+.5*r['mean']/scale)[:3]) for _,r in subset.iterrows()})
        drawer.DrawMolecules([molecule]*3,legends=[t+' | 5-member mean' for t in ATTRIBUTION_TASKS],highlightAtoms=[list(c) for c in colors],highlightAtomColors=colors,highlightBonds=[[]]*3)
        drawer.FinishDrawing();svg=drawer.GetDrawingText()
        (folder/'glabridin_atom_attribution.svg').write_text(svg)
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode(),write_to=str(folder/'glabridin_atom_attribution.png'))
        fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True)
        for ax,task in zip(axes,ATTRIBUTION_TASKS):
            sub=attrs.loc[attrs.task==task].sort_values('atom_index')
            ax.bar(sub.atom_index,sub['mean'],yerr=sub['std'],capsize=2,color=['#b74040' if v>=0 else '#3577aa' for v in sub['mean']])
            ax.axhline(0,color='#888',lw=.7);ax.set_ylabel(task);ax.spines[['top','right']].set_visible(False)
        axes[0].set_title('Glabridin: endpoint-specific atom and bond feature contributions',loc='left')
        axes[-1].set_xlabel('Atom index');axes[-1].set_xticks(sorted(attrs.atom_index.unique()))
        fig.text(.015,.018,'PREDICTED | Mean +/- member SD (not a confidence interval). Shared zero-feature baseline, fixed graph topology.\nRed: increases output relative to baseline; blue: decreases output. Not causal toxicity or an atom-deletion experiment.',fontsize=9)
        fig.tight_layout(rect=(0,.08,1,1));save(fig,folder,'atom_attribution_spread')

        ai=pd.read_csv(root/'data/processed/skincare/admet_ai_predictions.csv')
        data=ai.loc[ai.task.isin(MECHANISTIC)].pivot(index='task',columns='compound_id',values='prediction').reindex(MECHANISTIC)
        fig,ax=plt.subplots(figsize=(9,7))
        im=ax.imshow(data,aspect='auto',cmap='Purples',vmin=0,vmax=1)
        ax.set_xticks(range(len(data.columns)),data.columns);ax.set_yticks(range(len(data.index)),data.index)
        ax.set_title('Mechanistic follow-up: receptor and cellular assay predictions',loc='left',pad=16)
        fig.colorbar(im,ax=ax,label='Predicted assay-positive score')
        fig.text(.02,.02,'PREDICTED | Context for exposure-led follow-up, not whole-person toxicity or evidence of endocrine disruption.\nExternal skin use alone does not establish negligible systemic exposure.',fontsize=9)
        fig.tight_layout(rect=(0,.08,1,1));save(fig,folder,'mechanistic_followup')
    return 5

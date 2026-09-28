"""Figures from verified, cached model runs. No inference or external calls."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

def run(root: Path):
    output=root/'figures/evidence'; output.mkdir(parents=True,exist_ok=True)
    with plt.rc_context({'svg.hashsalt':'galatea-executed-models','font.family':'DejaVu Sans'}):
        attrs=pd.read_csv(root/'results/tables/chemprop_atom_attribution.csv')
        manifest=pd.read_csv(root/'data/compounds/compound_manifest.csv')
        glab=manifest.loc[manifest.compound_id==15].iloc[0]
        values=attrs.loc[attrs.compound_id==15]
        scale=values['mean'].abs().max()
        drawer=rdMolDraw2D.MolDraw2DSVG(1000,680,500,340)
        drawer.drawOptions().legendFontSize=20
        drawer.drawOptions().addAtomIndices=True
        molecules=[]; colors=[]; legends=[]
        for task in ['AMES','Skin_Reaction','DILI','hERG']:
            subset=values.loc[values.task==task].sort_values('atom_index')
            molecules.append(Chem.MolFromSmiles(glab.canonical_smiles))
            colors.append({int(r.atom_index):tuple(plt.cm.RdBu_r(0.5+0.5*r['mean']/scale)[:3]) for _,r in subset.iterrows()})
            legends.append(task+' | mean of 5 members')
        drawer.DrawMolecules(molecules,legends=legends,highlightAtoms=[list(c) for c in colors],highlightAtomColors=colors,highlightBonds=[[] for _ in colors])
        drawer.FinishDrawing()
        (output/'chemprop_glabridin_attribution.svg').write_text(drawer.GetDrawingText())
        # Numeric attribution and member spread accompany the colored structure.
        fig,axes=plt.subplots(4,1,figsize=(11,11),sharex=True)
        for ax,task in zip(axes,['AMES','Skin_Reaction','DILI','hERG']):
            subset=values.loc[values.task==task].sort_values('atom_index')
            ax.bar(subset.atom_index,subset['mean'],yerr=subset['std'],color=['#bb3a3a' if v>=0 else '#3274a1' for v in subset['mean']],capsize=2)
            ax.axhline(0,color='#777',lw=.7); ax.set_ylabel(task); ax.spines[['top','right']].set_visible(False)
        axes[0].set_title('Glabridin: which atom features shift each predicted endpoint?\nIntegrated gradients relative to zero features; fixed molecular topology',loc='left',pad=16)
        axes[-1].set_xlabel('RDKit atom index (same indices as the structure map)')
        axes[-1].set_xticks(values.atom_index.unique())
        fig.text(.02,.012,'PREDICTED | Mean +/- 1 SD across 5 models (not a confidence interval). Zero features are a nonphysical baseline.\nNode features plus half of each incident directed-bond contribution. Contributions are not causal toxicophores.',fontsize=10)
        fig.tight_layout(rect=(0,.065,1,1)); fig.savefig(output/'chemprop_attribution_spread.svg',metadata={'Date':None}); plt.close(fig)
        eco=pd.read_csv(root/'data/processed/ecosar_predictions.csv',keep_default_na=False)
        selected=eco.loc[(eco.Organism=='Fish')&(eco.Duration=='96-hr')&(eco.Endpoint=='LC50')].copy()
        classes=sorted(selected['QSAR Class'].unique())
        ids=list(manifest.compound_id)
        fig,ax=plt.subplots(figsize=(11,6))
        for i,cls in enumerate(classes):
            subset=selected.loc[selected['QSAR Class']==cls]
            for _,r in subset.iterrows():
                x=ids.index(r.compound_id)+(i-(len(classes)-1)/2)*.15
                flagged=r.domain_flag!='NO_EXCEEDANCE_DETECTED_NOT_DOMAIN_CERTIFIED'
                ax.scatter(x,float(r['Concentration (mg/L)']),marker='x' if flagged else 'o',color=plt.cm.tab10(i),s=70)
            ax.scatter([],[],color=plt.cm.tab10(i),label=cls)
        ax.set_yscale('log'); ax.set_xticks(range(len(ids)),[str(i) for i in ids]); ax.set_xlabel('Compound ID'); ax.set_ylabel('Predicted fish 96 h LC50 (mg/L; logarithmic axis)')
        ax.set_title('ECOSAR preserves class-specific aquatic predictions',loc='left'); ax.legend(title='QSAR class',loc='upper right'); ax.spines[['top','right']].set_visible(False)
        fig.text(.02,.02,'PREDICTED | x: source flag or selected logKow exceeds model maximum. o: neither check flagged; domain is not certified.\nAll returned classes retained separately. Lower modeled LC50 does not establish measured environmental risk.',fontsize=10)
        fig.tight_layout(rect=(0,.1,1,1)); fig.savefig(output/'ecosar_fish_screening.svg',metadata={'Date':None}); plt.close(fig)
        vega=pd.read_csv(root/'data/processed/vega_predictions.csv',keep_default_na=False)
        domain=vega.pivot(index='model_tag',columns='compound_id',values='applicability_domain_index').astype(float)
        fig,ax=plt.subplots(figsize=(10,7)); img=ax.imshow(domain,aspect='auto',vmin=0,vmax=1,cmap='viridis')
        ax.set_xticks(range(len(domain.columns)),domain.columns); ax.set_yticks(range(len(domain.index)),domain.index); ax.set_xlabel('Compound ID')
        for y in range(domain.shape[0]):
            for x in range(domain.shape[1]): ax.text(x,y,f'{domain.iloc[y,x]:.2f}',ha='center',va='center',color='white' if domain.iloc[y,x]<.65 else 'black')
        ax.set_title('VEGA: how strongly does each model support its own prediction?',loc='left',pad=18); fig.colorbar(img,ax=ax,label='Native VEGA applicability-domain index')
        fig.text(.02,.025,'PREDICTED | Model-specific ADI values are not calibrated probabilities and are not averaged.\nRead native reliability assessments and MW warnings in the accompanying table; stereochemistry is unresolved.',fontsize=10)
        fig.tight_layout(rect=(0,.08,1,1)); fig.savefig(output/'vega_applicability_domain.svg',metadata={'Date':None}); plt.close(fig)
    return 4

if __name__=='__main__': print(run(Path(__file__).resolve().parents[2]))

"""Freeze identical base descriptors and split rows before adding GIN embeddings."""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from analysis.vendor.maplight import get_fingerprints
R=Path('/root/autodl-tmp/IGEM/GALATEA-sustainable')
O=Path('/root/IGEM-storage/enrichment/gnn');O.mkdir(exist_ok=True)
train=pd.read_csv(R/'data/raw/skincare/maplight/ames_train_val.csv')
test=pd.read_csv(R/'data/raw/skincare/maplight/ames_test.csv')
structures=json.loads((R/'data/raw/skincare/expanded_references/structures.json').read_text())
print('structure type',type(structures),flush=True)
print(str(structures)[:400],flush=True)
panel=json.loads((R/'data/compounds/skincare_reference_panel_expanded.json').read_text())
print('panel keys',list(panel),flush=True)
if isinstance(structures,dict):structures=structures['compounds'] if 'compounds' in structures else list(structures.values())
refs=pd.DataFrame(structures)
print('cols',list(refs),flush=True)
smicol='canonical_smiles' if 'canonical_smiles' in refs else 'smiles'
frames=[train.Drug.tolist(),test.Drug.tolist(),refs[smicol].tolist()]
xs=[]
for smiles in frames:
    x=get_fingerprints(pd.Series(smiles));x[np.isinf(x)]=np.nan;xs.append(x)
np.savez_compressed(O/'base_features.npz',train=xs[0],test=xs[1],refs=xs[2],y_train=train.Y.to_numpy(),y_test=test.Y.to_numpy())
(O/'smiles.json').write_text(json.dumps({'train':frames[0],'test':frames[1],'refs':frames[2],'ids':refs.id.tolist()},indent=2)+'\n')
gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)
fp=lambda s:gen.GetFingerprint(Chem.MolFromSmiles(s))
tfps=[fp(s) for s in frames[0]]
neighbors=[]
for ident,s in zip(refs.id,frames[2]):
    sim=np.array(DataStructs.BulkTanimotoSimilarity(fp(s),tfps));idx=np.argsort(-sim)[:5]
    neighbors.append({'id':ident,'max_tanimoto':float(sim.max()),'neighbors':[{'train_index':int(i),'drug_id':str(train.iloc[i].Drug_ID),'smiles':train.iloc[i].Drug,'label':int(train.iloc[i].Y),'tanimoto':float(sim[i])} for i in idx]})
(O/'neighbors.json').write_text(json.dumps(neighbors,indent=2)+'\n')
print('COMPLETE', [x.shape for x in xs],flush=True)

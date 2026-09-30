"""Frozen GIN embeddings using the model named in official MapLight + GNN."""
import os
os.environ['DGLBACKEND']='pytorch'
import json, hashlib
from pathlib import Path
from importlib.metadata import version
import numpy as np
import torch
from molfeat.trans.pretrained import PretrainedDGLTransformer
from molfeat.trans.pretrained.dgl_pretrained import DGLModel
from molfeat.store import ModelStore
from dgllife.model import load_pretrained
from rdkit import Chem
torch.set_num_threads(8)
O=Path('/root/IGEM-storage/enrichment/gnn')
s=json.loads((O/'smiles.json').read_text())
# The molfeat public GCS listing is unavailable (401). Use the documented
# DGLLife upstream public checkpoint and retain molfeat's graph/pooling code.
os.chdir(O)
local_store=O/'model_store';local_store.mkdir(exist_ok=True)
encoder=DGLModel(name='gin_supervised_masking',store=ModelStore(str(local_store)))
encoder._model=load_pretrained('gin_supervised_masking').eval()
t=PretrainedDGLTransformer(kind=encoder,dtype=float)
features={}
for split in ['train','test','refs']:
    chunks=[]
    for start in range(0,len(s[split]),128):
        a=np.asarray(t([Chem.MolFromSmiles(x) for x in s[split][start:start+128]]))
        assert len(a)==min(128,len(s[split])-start) and np.isfinite(a).all()
        chunks.append(a);print(split,start,a.shape,flush=True)
    features[split]=np.concatenate(chunks,axis=0)
np.savez_compressed(O/'gin_features.npz',**features)
(O/'embedding_metadata.json').write_text(json.dumps({'encoder':'gin_supervised_masking','checkpoint_source':'DGLLife official load_pretrained; molfeat public GCS returned 401; upstream checkpoint used with unchanged molfeat graph featurization and mean pooling','checkpoint_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.glob('*.pth')},'library':'molfeat','frozen_encoder':True,'pretraining_overlap':'unknown','dimensions':int(features['train'].shape[1]),'packages':{p:version(p) for p in ['torch','numpy','dgl','dgllife','molfeat','rdkit']},'smiles_sha256':hashlib.sha256((O/'smiles.json').read_bytes()).hexdigest()},indent=2)+'\n')
print('COMPLETE',flush=True)

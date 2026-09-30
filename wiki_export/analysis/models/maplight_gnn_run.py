"""Matched MapLight ablation: frozen official GIN encoder appended to base features."""
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from importlib.metadata import version
import numpy as np
import pandas as pd
from rdkit import Chem
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss

R=Path(__file__).resolve().parents[2]
O=Path('/root/IGEM-storage/enrichment/gnn')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(y,p):return dict(roc_auc=float(roc_auc_score(y,p)),average_precision=float(average_precision_score(y,p)),brier=float(brier_score_loss(y,p)))
def run():
    raw=R/'data/raw/skincare/maplight_gnn';raw.mkdir(exist_ok=True)
    started=datetime.now(timezone.utc).isoformat()
    base=np.load(O/'base_features.npz');gin=np.load(O/'gin_features.npz')
    smiles=json.loads((O/'smiles.json').read_text())
    y=base['y_test'];xs={s:np.concatenate([base[s],gin[s]],axis=1) for s in ['train','test','refs']}
    oldmeta=json.loads((R/'data/raw/skincare/maplight/run_metadata.json').read_text())
    baseline=[];extended=[];rows=[];checkpoints=[];member=[]
    expected=pd.read_csv(R/'data/raw/skincare/maplight/ames_test_predictions.csv')
    assert np.array_equal(expected.Y.to_numpy(),y)
    for seed in range(1,6):
        old=CatBoostClassifier();old.load_model(oldmeta['checkpoints'][seed-1]['matvision_path'])
        b=old.predict_proba(base['test'])[:,1]
        assert np.max(np.abs(b-expected[f'probability_seed_{seed}']))<1e-10
        baseline.append(b)
        model=CatBoostClassifier(loss_function='Logloss',random_strength=2,random_seed=seed,iterations=1000,depth=6,nan_mode='Min',thread_count=12,verbose=False,allow_writing_files=False)
        print('FIT',seed,flush=True);model.fit(xs['train'],base['y_train'])
        p=model.predict_proba(xs['test'])[:,1];extended.append(p)
        ck=O/f'gnn_seed_{seed}.cbm';model.save_model(ck);checkpoints.append({'seed':seed,'path':str(ck),'sha256':h(ck),'bytes':ck.stat().st_size})
        for modelname,z in [('MapLight',b),('MapLight+GIN',p)]:member.append(dict(model=modelname,seed=seed,**metrics(y,z)))
        for modelname,z in [('MapLight',old.predict_proba(base['refs'])[:,1]),('MapLight+GIN',model.predict_proba(xs['refs'])[:,1])]:
            for cid,val in zip(smiles['ids'],z):rows.append(dict(id=cid,model=modelname,task='AMES',seed=seed,score=float(val),evidence_type='PREDICTED'))
    pred=expected[['Drug_ID','Drug','Y']].copy()
    norm=lambda s:Chem.MolToSmiles(Chem.MolFromSmiles(s),isomericSmiles=False)
    trainkeys={norm(s) for s in smiles['train']};keys=[norm(s) for s in smiles['test']]
    mask=np.array([k not in trainkeys for k in keys]);pred['overlaps_training_connectivity']=~mask
    for m,seq in [('base',baseline),('gnn',extended)]:
        for seed,p in enumerate(seq,1):pred[f'{m}_seed_{seed}']=p
        pred[f'{m}_mean']=np.mean(seq,axis=0)
    pred.to_csv(raw/'heldout_predictions.csv',index=False)
    pd.DataFrame(rows).to_csv(raw/'reference_members.csv',index=False)
    result=[]
    for split,keep in [('official_test',np.ones(len(y),dtype=bool)),('test_without_training_overlap',mask)]:
        for model,col in [('MapLight','base_mean'),('MapLight+GIN','gnn_mean')]:result.append(dict(model=model,split=split,n=int(keep.sum()),positives=int(y[keep].sum()),**metrics(y[keep],pred[col].to_numpy()[keep])))
    # Paired bootstrap resamples unique chemical connectivity groups on the disjoint subset.
    validkeys=sorted({keys[i] for i in np.flatnonzero(mask)})
    groups=[np.array([i for i,k in enumerate(keys) if k==key and mask[i]]) for key in validkeys]
    rng=np.random.default_rng(20260930);deltas={k:[] for k in ['roc_auc','average_precision','brier']}
    for _ in range(1000):
        ii=np.concatenate([groups[i] for i in rng.integers(0,len(groups),len(groups))])
        if len(np.unique(y[ii]))<2:continue
        a=metrics(y[ii],pred.base_mean.to_numpy()[ii]);b=metrics(y[ii],pred.gnn_mean.to_numpy()[ii])
        for k in deltas:deltas[k].append(b[k]-a[k])
    boot={k:{'delta_gnn_minus_base_mean':float(np.mean(v)),'percentile95':[float(x) for x in np.quantile(v,[.025,.975])]} for k,v in deltas.items()}
    meta={'status':'COMPLETE','started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'source_commit':'c249378c63232354d17083c83fe94fe728960a27','official_source':'https://github.com/maplightrx/MapLight-TDC/blob/c249378c63232354d17083c83fe94fe728960a27/maplight_gnn.py','method':'Original MapLight 2563 features plus frozen gin_supervised_masking embeddings; CatBoost defaults matched to prior run','parameters':{'iterations':1000,'depth':6,'random_strength':2,'thread_count':12,'nan_mode':'Min'},'task':'AMES','feature_count':int(xs['train'].shape[1]),'train_n':len(base['y_train']),'test_n':len(y),'test_training_connectivity_overlap_rows':int((~mask).sum()),'test_distinct_connectivities':len(set(keys)),'seeds':[1,2,3,4,5],'test_used_for_fit_tuning_stopping':False,'base_reproduction_max_allowed_error':1e-10,'embedding':json.loads((O/'embedding_metadata.json').read_text()),'packages':{p:version(p) for p in ['catboost','rdkit','numpy','scikit-learn']},'checksums':{p.name:h(p) for p in [O/'base_features.npz',O/'gin_features.npz',O/'smiles.json',R/'data/raw/skincare/maplight/ames_train_val.csv',R/'data/raw/skincare/maplight/ames_test.csv']},'checkpoints':checkpoints,'ensemble_metrics':result,'member_metrics':member,'paired_bootstrap':{'resamples':1000,'seed':20260930,'population':'test without training connectivity overlap','resampling_unit':'chemical connectivity group','results':boot},'limitations':['Benchmark test is not new independent cosmetic safety validation.','GIN pretraining overlap with benchmark compounds is unknown.','Bootstrap covers test-sample sampling uncertainty, not all model/data uncertainty.','Member SD is not a safety interval; no safe-concentration threshold selected.','Frozen GIN fingerprint + CatBoost, not an end-to-end retrained GNN.']}
    (raw/'run_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (raw/'training_neighbors.json').write_text((O/'neighbors.json').read_text())
    print(json.dumps(result,indent=2),flush=True)
    return meta
if __name__=='__main__':run()

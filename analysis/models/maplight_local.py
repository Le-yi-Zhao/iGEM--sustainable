"""Run the official MapLight feature + CatBoost recipe on the skincare-relevant TDC AMES task.

Five CPU members use the official default 1000 iterations and depth 6. The fixed
TDC test split is used only for evaluation, never for training or model selection.
"""
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from tdc.benchmark_group import admet_group
from analysis.vendor.maplight import get_fingerprints

ROOT=Path(__file__).resolve().parents[2]

def run():
    started=datetime.now(timezone.utc).isoformat()
    raw=ROOT/'data/raw/skincare/maplight';raw.mkdir(parents=True,exist_ok=True)
    cache=ROOT.parent/'work/maplight_skincare';cache.mkdir(parents=True,exist_ok=True)
    group=admet_group(path=str(ROOT.parent/'work/maplight/tdc'))
    manifest=pd.read_csv(ROOT/'data/compounds/compound_manifest.csv')
    features=get_fingerprints(manifest.canonical_smiles)
    if not np.isfinite(features).all(): raise ValueError('Nonfinite project descriptors')
    member_rows=[]; validation=[]; checkpoints=[]; datasets=[]
    from analysis.models.skincare_scope import MAPLIGHT_TASKS
    (ROOT/'data/processed/skincare').mkdir(parents=True,exist_ok=True)
    (ROOT/'results/tables/skincare').mkdir(parents=True,exist_ok=True)
    for task in MAPLIGHT_TASKS:
        bench=group.get(task)
        train,test=bench['train_val'].copy(),bench['test'].copy()
        for name,frame in [('train_val',train),('test',test)]:
            file=raw/f'{task}_{name}.csv';frame.to_csv(file,index=False)
            datasets.append({'task':task,'split':name,'rows':len(frame),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'file':str(file.relative_to(ROOT))})
        x_train=get_fingerprints(train.Drug);x_test=get_fingerprints(test.Drug)
        # RDKit can return undefined descriptors. CatBoost handles missing values
        # natively; retain every split row and never learn replacements from test.
        for split_name,x in [('train_val',x_train),('test',x_test)]:
            datasets.append({'task':task,'split':split_name,'undefined_feature_values':int(np.isnan(x).sum()),'infinite_feature_values':int(np.isinf(x).sum())})
            x[np.isinf(x)] = np.nan
        test_predictions=[]
        for seed in [1,2,3,4,5]:
            print(f'Training {task} seed {seed}: {len(train)} train / {len(test)} test',flush=True)
            model=CatBoostClassifier(loss_function='Logloss',random_strength=2,random_seed=seed,iterations=1000,depth=6,nan_mode='Min',thread_count=12,verbose=False,allow_writing_files=False)
            model.fit(x_train,train.Y.to_numpy())
            y_test=model.predict_proba(x_test)[:,1];y_project=model.predict_proba(features)[:,1]
            test_predictions.append(y_test)
            model_file=cache/f'{task}_seed_{seed}.cbm';model.save_model(str(model_file))
            checkpoints.append({'task':task,'seed':seed,'sha256':hashlib.sha256(model_file.read_bytes()).hexdigest(),'bytes':model_file.stat().st_size,'matvision_path':str(model_file)})
            for i,c in manifest.iterrows(): member_rows.append({'compound_id':c.compound_id,'task':task,'seed':seed,'positive_class_probability':float(y_project[i]),'evidence_type':'PREDICTED'})
            validation.append({'task':task,'seed':seed,'train_n':len(train),'test_n':len(test),'roc_auc':roc_auc_score(test.Y,y_test),'average_precision':average_precision_score(test.Y,y_test),'brier_score':brier_score_loss(test.Y,y_test),'split':'official TDC train_val/test','test_used_for_fit':False})
            print(f'Completed {task} seed {seed}',flush=True)
        predictions=test[['Drug_ID','Drug','Y']].copy()
        for seed,ys in enumerate(test_predictions,1):predictions[f'probability_seed_{seed}']=ys
        predictions.to_csv(raw/f'{task}_test_predictions.csv',index=False)
        # Check exact canonical connectivity overlap, including project membership.
        from rdkit import Chem
        norm=lambda s:Chem.MolToSmiles(Chem.MolFromSmiles(s),isomericSmiles=False)
        train_keys=set(train.Drug.map(norm));test_keys=set(test.Drug.map(norm))
        datasets.append({'task':task,'canonical_train_test_overlap':len(train_keys&test_keys),'project_ids_in_train':[int(c.compound_id) for _,c in manifest.iterrows() if norm(c.canonical_smiles) in train_keys],'project_ids_in_test':[int(c.compound_id) for _,c in manifest.iterrows() if norm(c.canonical_smiles) in test_keys]})
    frame=pd.DataFrame(member_rows);frame.to_csv(raw/'member_predictions.csv',index=False)
    summary=frame.groupby(['compound_id','task']).positive_class_probability.agg(['mean','std','count']).reset_index();summary['evidence_type']='PREDICTED'
    summary.to_csv(ROOT/'data/processed/skincare/maplight_predictions.csv',index=False)
    pd.DataFrame(validation).to_csv(ROOT/'results/tables/skincare/maplight_heldout_metrics.csv',index=False)
    metadata={'status':'COMPLETE_FOR_SELECTED_TASKS','official_repository':'https://github.com/maplightrx/MapLight-TDC','source_commit':(ROOT/'analysis/vendor/maplight_source_commit.txt').read_text().strip(),'method':'official MapLight (without GNN) ECFP/Avalon/ErG/200-descriptor CatBoost recipe','selected_tasks':list(MAPLIGHT_TASKS),'seeds':[1,2,3,4,5],'iterations':1000,'depth':6,'random_strength':2,'thread_count':12,'device':'CPU','missing_feature_policy':'CatBoost nan_mode=Min; infinite values become NaN; no row deletion and no imputation fitted on test data','feature_count':features.shape[1],'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'packages':{p:version(p) for p in ['catboost','PyTDC','rdkit','numpy','scikit-learn']},'input_sha256':hashlib.sha256((ROOT/'data/compounds/compound_manifest.csv').read_bytes()).hexdigest(),'checkpoints':checkpoints,'datasets':datasets,'limitations':['Selected tasks only; other MapLight endpoints and MapLight+GNN were not run.','RDKit/CatBoost versions differ from original publication; this is a recipe reproduction, not an exact leaderboard replication.','TDC test splits were not used for fitting, stopping or tuning. Overlap audit is reported; no independent GALATEA wet-lab validation.','Ensemble spread is not a calibrated confidence interval. No formal chemical applicability domain established.']}
    (raw/'run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata

if __name__=='__main__':print(json.dumps(run(),indent=2))

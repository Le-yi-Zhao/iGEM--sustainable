"""Ensemble integrated gradients of Chemprop input features, with fixed topology.

This is a prediction explanation relative to a zero-feature baseline, not an
atom deletion experiment or a causal toxicophore analysis.
"""
from __future__ import annotations
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
from analysis.models.skincare_scope import ATTRIBUTION_TASKS
TASKS = list(ATTRIBUTION_TASKS)

def run(steps=128):
    import numpy as np
    import pandas as pd
    import torch
    from admet_ai import ADMETModel
    from chemprop.data import MoleculeDatapoint, MoleculeDataset
    from chemprop.data.collate import BatchMolGraph
    from rdkit import Chem
    torch.manual_seed(20260928)
    torch.set_num_threads(4)
    started = datetime.now(timezone.utc).isoformat()
    manifest = pd.read_csv(ROOT/'data/compounds/compound_manifest.csv', dtype={'compound_id':str})
    mols = [Chem.MolFromSmiles(s) for s in manifest.canonical_smiles]
    dataset = MoleculeDataset([MoleculeDatapoint(mol=m) for m in mols])
    graphs = [dataset[i].mg for i in range(len(dataset))]
    model = ADMETModel(include_physchem=False, num_workers=0)
    selected = [(names, members) for names, members in zip(model.task_lists, model.model_lists) if all(t in names for t in TASKS)]
    if len(selected) != 1: raise RuntimeError('Exactly one ensemble must contain all interpretation endpoints')
    names, members = selected[0]
    task_indices = [names.index(t) for t in TASKS]
    fresh = pd.read_csv(ROOT/'data/raw/skincare/admet_ai/ensemble_member_predictions.csv', dtype={'compound_id':str})
    (ROOT/'results/tables/skincare').mkdir(parents=True,exist_ok=True)
    records, checks = [], []
    for member_id, member in enumerate(members):
        member = member.cpu().eval()
        for parameter in member.parameters(): parameter.requires_grad_(False)
        graph = BatchMolGraph(graphs)
        actual_v, actual_e = graph.V.clone(), graph.E.clone()
        with torch.no_grad():
            actual = member(graph)[:,task_indices].numpy()
            graph.V, graph.E = torch.zeros_like(actual_v), torch.zeros_like(actual_e)
            baseline = member(graph)[:,task_indices].numpy()
        for i,c in manifest.iterrows():
            for j,t in enumerate(TASKS):
                expected = fresh[(fresh.compound_id==c.compound_id)&(fresh.task==t)&(fresh.ensemble_member==member_id)].prediction.to_numpy()
                if len(expected)!=1 or abs(actual[i,j]-expected[0])>1e-5:
                    raise RuntimeError('Attribution forward pass does not match fresh inference')
        n = steps
        while True:
            gv = torch.zeros((len(TASKS), *actual_v.shape))
            ge = torch.zeros((len(TASKS), *actual_e.shape))
            for k in range(n+1):
                graph.V = (actual_v*(k/n)).requires_grad_(True)
                graph.E = (actual_e*(k/n)).requires_grad_(True)
                values = member(graph)
                weight = (0.5 if k in (0,n) else 1.0)/n
                for j, ti in enumerate(task_indices):
                    dv,de = torch.autograd.grad(values[:,ti].sum(),(graph.V,graph.E),retain_graph=j<len(TASKS)-1)
                    gv[j] += weight*dv
                    ge[j] += weight*de
            node_values = (gv*actual_v).sum(-1).numpy()
            edge_values = (ge*actual_e).sum(-1).numpy()
            edge_to_nodes = np.zeros_like(node_values)
            for e,(src,dst) in enumerate(graph.edge_index.T.tolist()):
                edge_to_nodes[:,src] += edge_values[:,e]/2
                edge_to_nodes[:,dst] += edge_values[:,e]/2
            atoms = node_values+edge_to_nodes
            sums = np.stack([atoms[:,graph.batch.numpy()==i].sum(1) for i in range(len(mols))])
            residual = sums-(actual-baseline)
            if np.max(np.abs(residual))<=0.005 or n>=1024: break
            n*=2
        if not np.isfinite(atoms).all(): raise RuntimeError('Nonfinite attributions')
        offset=0
        for i,c in manifest.iterrows():
            for j,t in enumerate(TASKS):
                checks.append({'compound_id':c.compound_id,'task':t,'ensemble_member':member_id,'prediction':float(actual[i,j]),'baseline_prediction':float(baseline[i,j]),'attribution_sum':float(sums[i,j]),'completeness_residual':float(residual[i,j]),'steps':n,'passes_0_005':bool(abs(residual[i,j])<=0.005)})
                for a in range(mols[i].GetNumAtoms()):
                    records.append({'compound_id':c.compound_id,'task':t,'ensemble_member':member_id,'atom_index':a,'element':mols[i].GetAtomWithIdx(a).GetSymbol(),'node_feature_contribution':float(node_values[j,offset+a]),'allocated_bond_contribution':float(edge_to_nodes[j,offset+a]),'attribution':float(atoms[j,offset+a]),'evidence_type':'PREDICTED'})
            offset+=mols[i].GetNumAtoms()
        print(f'Explained member {member_id}: {n} steps, max residual {np.max(np.abs(residual)):.6f}',flush=True)
    raw=ROOT/'data/raw/skincare/chemprop';raw.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(records).to_csv(raw/'integrated_gradients_members.csv',index=False)
    pd.DataFrame(checks).to_csv(ROOT/'results/tables/skincare/chemprop_attribution_completeness.csv',index=False)
    frame=pd.DataFrame(records)
    summary=frame.groupby(['compound_id','task','atom_index','element'],sort=False).attribution.agg(['mean','std','count']).reset_index()
    summary.to_csv(ROOT/'results/tables/skincare/chemprop_atom_attribution.csv',index=False)
    metadata={'status':'COMPLETE' if all(c['passes_0_005'] for c in checks) else 'PARTIAL','method':'trapezoidal integrated gradients of atom and directed-bond features; fixed topology','baseline':'all atom/bond features set to zero with original graph topology retained','bond_allocation':'each directed-edge contribution split equally between its two endpoint atoms','seed':20260928,'endpoints':TASKS,'members':len(members),'molecules':len(mols),'completeness_tolerance':0.005,'max_absolute_completeness_residual':max(abs(c['completeness_residual']) for c in checks),'forward_pass_matches_fresh_predictions':True,'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'evidence_type':'PREDICTED','input_sha256':hashlib.sha256((ROOT/'data/compounds/compound_manifest.csv').read_bytes()).hexdigest(),'prediction_run':'data/raw/skincare/admet_ai/run_metadata.json','limitations':['Zero features are an out-of-distribution mathematical baseline, not a physical molecule.','Graph topology is held fixed; contributions explain features conditional on connectivity.','Ensemble standard deviation is model spread, not a confidence interval.','Numerical completeness checks do not validate biological causality.','Not a causal toxicophore or proof of safety.']}
    (raw/'attribution_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata

if __name__=='__main__':print(json.dumps(run(),indent=2))

import json,hashlib
from pathlib import Path
import pandas as pd
from rdkit import Chem
R=Path('/root/autodl-tmp/IGEM/GALATEA-sustainable')
O=R/'data/raw/skincare/opera';O.mkdir(exist_ok=True)
panel=json.loads((R/'data/raw/skincare/expanded_references/structures.json').read_text())
for r in pd.read_csv(R/'data/compounds/compound_manifest.csv').to_dict('records'):
    if r['compound_id']!=15:panel.append({'id':'pathway_'+str(r['compound_id']),'smiles':r['canonical_smiles'],'name_zh':'路径化合物 '+str(r['compound_id']),'role':'PATHWAY_INTERMEDIATE'})
w=Chem.SDWriter(str(O/'input.sdf'))
for r in panel:
    m=Chem.MolFromSmiles(r['smiles']);assert m is not None
    m.SetProp('_Name',r['id']);w.write(m)
w.close()
(O/'input_manifest.json').write_text(json.dumps({'structures':panel,'selected_endpoints':['logP','WS','BCF','Koc','RB','KM'],'excluded_endpoints':{'BioDeg':'Model limited to hydrocarbons (C/H); glabridin contains oxygen, so this half-life model is excluded.'},'selection_basis':'Physicochemical/environmental fate endpoints selected before inference, independent of results.','input_sha256':hashlib.sha256((O/'input.sdf').read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print('PREPARED',len(panel))

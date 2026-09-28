"""Normalize executed VEGA and EPA exports without changing their native scales."""
from __future__ import annotations
import csv
import io
import json
import re
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def connectivity(smiles):
    mol=Chem.MolFromSmiles(smiles)
    if mol is None: raise ValueError('Unparseable exported structure')
    return Chem.MolToSmiles(mol, isomericSmiles=False)

def ecosar_domain(row):
    try:
        outside=float(row['Selected Log Kow']) > float(row['Max Log Kow'])
    except (ValueError, KeyError):
        return 'UNKNOWN'
    if outside: return 'EXCEEDS_MAX_LOGKOW'
    if row.get('Flags','').strip(): return 'SOURCE_FLAG_PRESENT'
    return 'NO_EXCEEDANCE_DETECTED_NOT_DOMAIN_CERTIFIED'

def run(root: Path):
    manifest=read(root/'data/compounds/compound_manifest.csv')
    by_id={r['compound_id']:r for r in manifest}
    by_smiles={r['canonical_smiles']:r for r in manifest}
    if len(by_smiles)!=len(manifest): raise ValueError('Ambiguous manifest SMILES')
    vega=[]
    for path in sorted((root/'data/raw/vega/reports').glob('*.txt')):
        text=path.read_text(); lines=text.splitlines()
        start=next(i for i,l in enumerate(lines) if l.startswith('No.\t'))
        rows=list(csv.DictReader(io.StringIO('\n'.join(lines[start:])),delimiter='\t'))
        if len(rows)!=len(manifest) or {r['Id'] for r in rows}!=set(by_id):
            raise ValueError(f'Incomplete VEGA report: {path.name}')
        for r in rows:
            c=by_id[r['Id']]
            if connectivity(r['SMILES'])!=connectivity(c['canonical_smiles']):
                raise ValueError('VEGA structure/ID mismatch')
            prediction_fields={k:v for k,v in r.items() if k.startswith('Predicted ')}
            if not prediction_fields: raise ValueError('VEGA report lacks predictions')
            reliability=re.search(r'\(([^()]*reliability)\)',r.get('Assessment',''))
            source_mw=r.get('Molecular Weight',r.get('MW',''))
            mismatch=bool(source_mw and abs(float(source_mw)-Descriptors.MolWt(Chem.MolFromSmiles(c['canonical_smiles'])))>0.5)
            vega.append({'compound_id':r['Id'],'compound_name':c['compound_name'],'model_tag':path.stem,'model_version':lines[1],'assessment':r.get('Assessment',''),'prediction_fields_json':json.dumps(prediction_fields,sort_keys=True),'applicability_domain_index':r.get('ADI',''),'reliability':reliability.group(1) if reliability else 'NOT_EXPORTED','remarks':r.get('Remarks',''),'connectivity_matches_input':True,'stereochemistry_resolved':False,'source_molecular_weight_warning':mismatch,'raw_report':str(path.relative_to(root)),'evidence_type':'PREDICTED'})
    if vega: write(root/'data/processed/vega_predictions.csv',vega)
    epi=read(root/'data/raw/episuite/episuite_results.csv')
    if len(epi)!=len(manifest): raise ValueError('Incomplete EPI export')
    normalized=[]
    selected={
        'Predicted Log Kow':'dimensionless log10',
        'Predicted Water Solubility, WSKow (mg/L)':'mg/L',
        'Predicted Water Solubility, WaterNT (mg/L)':'mg/L',
        'Bioconcentration Factor (L/kg wet-wt)':'L/kg wet-wt',
        'Bioaccumulation Factor (L/kg wet-wt)':'L/kg wet-wt',
        'BioWin3 (Ultimate Biodegradation Timeframe)':'ordinal model score (not days)',
        'BioWin5 (MITI Linear Model Prediction)':'model score',
        'BioWin6 (MITI Non-Linear Model Prediction)':'model score',
        'Predicted Log Koc':'dimensionless log10',
    }
    for r in epi:
        c=by_smiles[r['Submitted Chemical']]
        if r['Status']!='success' or connectivity(r['SMILES'])!=connectivity(c['canonical_smiles']):
            raise ValueError('Unsuccessful or mismatched EPA structure')
        for endpoint,unit in selected.items():
            if r[endpoint]: normalized.append({'compound_id':c['compound_id'],'endpoint':endpoint,'value':r[endpoint],'unit':unit,'evidence_type':'PREDICTED','applicability_domain':'NOT_EXPORTED','raw_file':'data/raw/episuite/episuite_results.csv'})
    write(root/'data/processed/episuite_predictions.csv',normalized)
    eco=read(root/'data/raw/ecosar/ecosar_aquatic.csv')
    out=[]
    for r in eco:
        c=by_smiles[r['Submitted Chemical']]
        if r['Status']!='success' or connectivity(r['SMILES'])!=connectivity(c['canonical_smiles']):
            raise ValueError('Unsuccessful or mismatched ECOSAR structure')
        out.append({'compound_id':c['compound_id'],'compound_name':c['compound_name'],**r,'domain_flag':ecosar_domain(r),'evidence_type':'PREDICTED'})
    if {r['compound_id'] for r in out}!=set(by_id): raise ValueError('Missing ECOSAR compounds')
    write(root/'data/processed/ecosar_predictions.csv',out)
    summary={'vega_selected_models':len({r['model_tag'] for r in vega}),'vega_records':len(vega),'vega_molecular_weight_warnings':sum(r['source_molecular_weight_warning'] for r in vega),'epi_compounds':len(epi),'epi_selected_values':len(normalized),'ecosar_records':len(out),'ecosar_logkow_exceedances':sum(r['domain_flag']=='EXCEEDS_MAX_LOGKOW' for r in out),'ecosar_source_flags':sum(bool(r['Flags']) for r in out),'evidence_type':'PREDICTED','normalization':'join EPA exact Submitted Chemical; verify VEGA IDs and constitutional connectivity; retain native units, all classes and source flags; no cross-model probability averaging','limitations':['No formal domain values in the EPA wide export.','ECOSAR no-exceedance is not a full applicability-domain certificate.','VEGA removes stereochemistry; certain reported molecular weights differ from RDKit by >0.5 g/mol; source values retained and flagged, not corrected.','Related methods across VEGA and EPI are not independent votes.']}
    (root/'results/summaries/environmental_execution.json').write_text(json.dumps(summary,indent=2)+'\n')
    sar_metadata=json.loads((root/'data/raw/admetsar/run_metadata.json').read_text())
    sar_path=root/'data/raw/admetsar'/f"{sar_metadata['job_id']}_pred.txt"
    with sar_path.open(encoding='utf-8-sig',newline='') as f:
        sar_rows=list(csv.DictReader(f,delimiter='\t'))
    iso=lambda x:Chem.MolToSmiles(Chem.MolFromSmiles(x),isomericSmiles=True)
    sar_map={iso(r['canonical_smiles']):r['compound_id'] for r in manifest}
    if len(sar_map)!=len(manifest):raise ValueError('Ambiguous admetSAR input mapping')
    sar_out=[{'compound_id':sar_map[iso(r['SMILES'])],**r,'applicability_domain':'NOT_EXPORTED'} for r in sar_rows]
    if len(sar_out)!=6 or {r['compound_id'] for r in sar_out}!=set(by_id):raise ValueError('Incomplete admetSAR output')
    write(root/'data/processed/admetsar_predictions.csv',sar_out)
    return summary

if __name__=='__main__': print(json.dumps(run(Path(__file__).resolve().parents[2]),indent=2))

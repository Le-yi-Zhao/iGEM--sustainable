"""Build use-specific evidence without treating molecular scores as product safety."""
from pathlib import Path
import csv
import hashlib
import json
from analysis.models.skincare_scope import ACTIVE_AI, ai_scope, PRODUCT_ASSUMPTION, GUIDANCE

SAR_CORE = {
    'Skin_sensitisation':'Skin sensitisation', 'Skin_irritation':'Skin irritation',
    'Skin_corrosion':'Skin corrosion', 'Eye_irritation':'Eye irritation',
    'Eye_corrosion':'Eye corrosion', 'Ames':'Ames mutagenicity',
    'Micronucleus':'Micronucleus genotoxicity', 'Rodents_carcinogenicity':'Rodent carcinogenicity',
    'Photoinduced_toxicity':'Photoinduced toxicity',
    'Phototoxicity_Photoirritation':'Phototoxicity / photoirritation',
    'Photoallergy':'Photoallergy',
}
SAR_FOLLOWUP = {'Reproductive_toxicity':'Reproductive toxicity',
                'Repeated_dose_toxicity':'Repeated-dose toxicity',
                'AR':'Androgen receptor activity','ER':'Estrogen receptor activity',
                'AR_LBD':'Androgen receptor LBD activity','ER_LBD':'Estrogen receptor LBD activity',
                'Aromatase':'Aromatase activity','TR':'Thyroid receptor activity'}
LAB_CORE = {'SkinSen':'Skin sensitisation','Ames':'Ames mutagenicity',
            'Genotoxicity':'Genotoxicity','Carcinogenicity':'Carcinogenicity',
            'EC':'Eye corrosion','EI':'Eye irritation'}

def read(root, path):
    with (root/path).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def write(root, path, rows):
    p=root/path; p.parent.mkdir(parents=True,exist_ok=True)
    if not rows: raise ValueError('Refuse an empty evidence table: '+path)
    with p.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    return p

def validate_rows(rows, expected_ids, fields):
    if {str(r['compound_id']) for r in rows} != expected_ids or len(rows)!=len(expected_ids):
        raise ValueError('Missing, duplicate or unexpected structure-matched rows')
    for row in rows:
        for field in fields:
            value=float(row[field])
            if not 0 <= value <= 1: raise ValueError(f'Invalid score: {field}={value}')

def run(root: Path):
    manifest=read(root,'data/compounds/compound_manifest.csv')
    names={r['compound_id']:r['compound_name'] for r in manifest}
    ids=set(names); records=[]; sources=set()
    def add(cid, platform, field, endpoint, value, scope, source, semantics, uncertainty='', domain='NOT_EXPORTED'):
        sources.add(source)
        records.append(dict(compound_id=str(cid),compound_name=names[str(cid)],
            role='TARGET_INGREDIENT' if str(cid)=='15' else 'PATHWAY_OR_POTENTIAL_IMPURITY_REFERENCE',
            platform=platform,raw_endpoint=field,endpoint=endpoint,value=str(value),scope=scope,
            value_semantics=semantics,uncertainty=str(uncertainty),applicability=domain,
            evidence_type='PREDICTED',source_file=source))

    ai_path='data/processed/skincare/admet_ai_predictions.csv'
    ai=read(root,ai_path)
    if {r['task'] for r in ai} != set(ACTIVE_AI) or len(ai)!=6*len(ACTIVE_AI):
        raise ValueError('ADMET skincare output does not match the declared scope')
    for r in ai:
        semantics='positive_class_model_score' if r['task_type']=='classification' else 'native_regression_units: '+r['units']
        add(r['compound_id'],'ADMET-AI',r['task'],r['endpoint'],r['prediction'],ai_scope(r['task']),ai_path,semantics,r['ensemble_std'],'NOT_FORMALLY_ESTABLISHED')

    sar_path='data/processed/admetsar_predictions.csv'; sar=read(root,sar_path)
    validate_rows(sar,ids,{**SAR_CORE,**SAR_FOLLOWUP})
    for r in sar:
        for field,label in {**SAR_CORE,**SAR_FOLLOWUP}.items():
            add(r['compound_id'],'admetSAR',field,label,r[field],
                'CORE_HAZARD' if field in SAR_CORE else 'SYSTEMIC_FOLLOWUP',sar_path,
                'native_classification_score; no calibrated cosmetic risk cutoff')

    lab_path='data/raw/admetlab/admetlab_predictions.csv'; lab=read(root,lab_path)
    from rdkit import Chem
    canonical=lambda s:Chem.MolToSmiles(Chem.MolFromSmiles(s),isomericSmiles=True)
    by_structure={canonical(r['canonical_smiles']):r['compound_id'] for r in manifest}
    for r in lab: r['compound_id']=by_structure[canonical(r['raw_smiles'])]
    validate_rows(lab,ids,LAB_CORE)
    for r in lab:
        for field,label in LAB_CORE.items():
            add(r['compound_id'],'ADMETlab',field,label,r[field],'CORE_HAZARD',lab_path,'positive_class_model_score')
        for field in ['logP','logS','logD']:
            add(r['compound_id'],'ADMETlab',field,field,r[field],'FORMULATION_CONTEXT',lab_path,'native_regression_scale')

    mp='data/processed/skincare/maplight_predictions.csv'
    for r in read(root,mp):
        if r['task']!='ames': raise ValueError('Non-skincare MapLight task in current run')
        add(r['compound_id'],'MapLight','ames','Ames mutagenicity',r['mean'],'CORE_HAZARD',mp,'positive_class_model_score',r['std'],'NOT_FORMALLY_ESTABLISHED')

    pp='data/raw/protox/protox_predictions.csv'
    for r in read(root,pp):
        if r['shorthand'] in {'mutagen','carcino','eco'}:
            add(r['compound_id'],'ProTox',r['shorthand'],r['endpoint'],r['prediction'],
                'ENVIRONMENT' if r['shorthand']=='eco' else 'CORE_HAZARD',pp,
                'reported_class; confidence is not positive-class probability',r['confidence'])
    vp='data/processed/vega_predictions.csv'
    for r in read(root,vp):
        scope='CORE_HAZARD' if r['model_tag'] in {'MUTA_CAESAR','SKIN_CAESAR'} else 'ENVIRONMENT'
        if r['model_tag']=='LOGP_MEYLAN': scope='FORMULATION_CONTEXT'
        add(r['compound_id'],'VEGA',r['model_tag'],r['model_tag'],r['assessment'],scope,vp,
            'native assessment; see source for units and molecular-weight warnings','',
            r['applicability_domain_index']+'; '+r['reliability']+'; MW warning='+r['source_molecular_weight_warning'])
    write(root,'results/tables/skincare/evidence.csv',records)

    historical=read(root,'data/processed/admet_ai_predictions.csv'); seen=set(); selection=[]
    for r in historical:
        if r['task'] in seen: continue
        seen.add(r['task']); scope=ai_scope(r['task'])
        reason={'CORE_HAZARD':'Dermal contact or genotoxic/carcinogenic hazard screening',
                'FORMULATION_CONTEXT':'Solubility and partitioning context; not measured skin absorption',
                'MECHANISTIC_FOLLOWUP':'Cell/ receptor activity only; preserve signals for exposure-led follow-up',
                'NOT_IN_ROUTINE_SKINCARE_SCREEN':'Drug-disposition or organ-specific drug-screen endpoint; historical evidence retained, not waived as a hazard'}[scope]
        selection.append(dict(task=r['task'],endpoint=r['endpoint'],task_type=r['task_type'],scope=scope,
                              active=scope!='NOT_IN_ROUTINE_SKINCARE_SCREEN',reason=reason))
    write(root,'results/tables/skincare/admet_task_selection.csv',selection)

    # Comparison is descriptive; no safety decision, pooled probability or cross-assay vote.
    lookup={(r['compound_id'],r['task']):r for r in ai}
    lab_by={r['compound_id']:r for r in lab}; sar_by={r['compound_id']:r for r in sar}
    map_by={r['compound_id']:r for r in read(root,mp)}; comparison=[]
    for cid in names:
        for task,lab_field,sar_field in [('AMES','Ames','Ames'),('Skin_Reaction','SkinSen','Skin_sensitisation'),('Carcinogens_Lagunin','Carcinogenicity','Rodents_carcinogenicity')]:
            r=lookup[cid,task]
            comparison.append(dict(compound_id=cid,endpoint=task,admet_ai=r['prediction'],admet_ai_std=r['ensemble_std'],
                admetlab=lab_by[cid][lab_field],admetsar=sar_by[cid][sar_field],
                maplight=map_by[cid]['mean'] if task=='AMES' else '',
                interpretation='SIDE_BY_SIDE_ONLY; assay definitions, training sets and calibration differ; 0.5 is not a safety threshold'))
    write(root,'results/tables/skincare/platform_comparison.csv',comparison)

    gaps=[
        ('Dermal absorption','WAITING_FOR_DATA','No measured skin absorption or validated formulation-specific model; Caco-2/PAMPA are not skin substitutes.'),
        ('Concentration and use','WAITING_FOR_DATA','Final concentration, applied amount, frequency, area, rinse/leave-on and target population are needed.'),
        ('Formulation and local tolerance','WAITING_FOR_DATA','Ingredient QSAR cannot validate finished-product irritation, sensitisation or ocular tolerance.'),
        ('Photo safety','PARTIAL','admetSAR photo scores available; UV/visible spectrum, photostability and formulation testing are absent.'),
        ('Systemic safety margin','WAITING_FOR_DATA','No systemic exposure dose or suitable point of departure; repeated-dose, reproductive and endocrine concerns are not waived.'),
        ('Purity and residuals','WAITING_FOR_DATA','Pathway compounds are comparison candidates, not measured impurities; quantify purity, residual solvents and contaminants.'),
        ('Model calibration and controls','WAITING_FOR_DATA','No cosmetic-specific calibrated cutoff or independent positive/negative control panel. DrugBank is not a safe control set.'),
        ('Finished-product quality','WAITING_FOR_DATA','Stability, preservation/microbial quality and packaging compatibility need formulation evidence.'),
        ('Benefit / efficacy','OUTSIDE_SAFETY_SCREEN','No whitening, efficacy or skin-benefit claim is inferred from toxicity predictions.'),
    ]
    write(root,'results/tables/skincare/evidence_gaps.csv',[dict(topic=a,status=b,reason=c) for a,b,c in gaps])
    inventory=[]
    for platform in dict.fromkeys(r['platform'] for r in records):
        inventory.append(dict(platform=platform,selected_records=sum(r['platform']==platform for r in records),
            execution='FRESH_CHECKPOINT_INFERENCE' if platform=='ADMET-AI' else 'FRESH_AMES_TRAINING' if platform=='MapLight' else 'SELECTED_FROM_VERIFIED_PRIOR_RUN',
            status='PREDICTED; ingredient screening only'))
    for platform,path in [('EPA EPI Suite','data/processed/episuite_predictions.csv'),('ECOSAR','data/processed/ecosar_predictions.csv')]:
        sources.add(path);inventory.append(dict(platform=platform,selected_records=len(read(root,path)),execution='SELECTED_FROM_VERIFIED_PRIOR_RUN',status='ENVIRONMENT; native domain flags retained'))
    write(root,'results/tables/skincare/model_inventory.csv',inventory)
    run_files=[]
    for p in sorted((root/'data/raw/skincare').rglob('*')):
        if p.is_file():run_files.append(dict(path=str(p.relative_to(root)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    summary=dict(profile='skincare',product_assumption=PRODUCT_ASSUMPTION,focus_compound='15 / glabridin',
        guidance=GUIDANCE,regulatory_status='Scientific scoping reference, not a jurisdiction-specific compliance assessment',
        selected_admet_tasks=len(ACTIVE_AI),inactive_admet_tasks=41-len(ACTIVE_AI),
        attribution_tasks=['AMES','Skin_Reaction','Carcinogens_Lagunin'],maplight_tasks=['ames'],
        records=len(records),scope_selected_by='intended use and endpoint meaning, not favorable prediction values',
        calibrated_low_risk_threshold=None,systemic_safety_margin=None,
        missing_exposure_data=True,cross_platform_probabilities_averaged=False,
        archive_policy='Prior broad outputs remain unchanged for traceability; not current scheduled tasks',
        fresh_run_files=run_files,
        files=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in sorted(sources)])
    (root/'results/summaries/skincare_scope.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary

if __name__=='__main__': print(json.dumps(run(Path(__file__).resolve().parents[2]),indent=2))

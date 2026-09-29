"""Evidence-selected cosmetic reference panel; fresh inference is explicit.

Run with --predict on Matvision, then without arguments for an offline report rebuild.
Reference membership and source use conditions are frozen before inference.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / 'data/compounds/skincare_reference_panel.json'
RAW = ROOT / 'data/raw/skincare/references'
RESULT = ROOT / 'results/tables/skincare/reference_predictions.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def predict():
    import numpy as np
    import pandas as pd
    import torch
    from admet_ai import ADMETModel
    from admet_ai.constants import DEFAULT_MODELS_DIR
    from catboost import CatBoostClassifier
    from lightning import pytorch as pl
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors
    from analysis.models.skincare_scope import ACTIVE_AI
    from analysis.vendor.maplight import get_fingerprints

    started = datetime.now(timezone.utc).isoformat()
    panel = json.loads(PANEL.read_text())
    rows = list(csv.DictReader((ROOT/'data/compounds/compound_manifest.csv').open()))
    target = next(r for r in rows if r['compound_id'] == '15')
    compounds = [{'id': 'glabridin', 'name': 'Glabridin', 'name_zh': '光甘草定', 'smiles': target['canonical_smiles'], 'inchikey': target['inchikey'], 'role': 'TARGET'}]
    structure_sources = []
    for ref in panel['references']:
        source = RAW/'pubchem'/f"{ref['id']}.json"
        doc = json.loads(source.read_text())
        props = doc['response']['PropertyTable']['Properties']
        assert doc['query_cas'] == ref['cas'] and len(props) == 1
        p = props[0]
        assert p['CID'] == ref['pubchem_cid'], (ref['id'], p['CID'])
        mol = Chem.MolFromSmiles(p['SMILES'])
        assert mol is not None and Chem.MolToInchiKey(mol) == p['InChIKey']
        assert rdMolDescriptors.CalcMolFormula(mol) == p['MolecularFormula']
        compounds.append({k: ref[k] for k in ['id', 'name', 'name_zh', 'role']} | {'smiles': p['SMILES'], 'inchikey': p['InChIKey'], 'cas': ref['cas'], 'pubchem_cid': p['CID']})
        structure_sources.append({'path': str(source.relative_to(ROOT)), 'sha256': digest(source)})
    smiles = [c['smiles'] for c in compounds]
    alpha, beta = (next(c for c in compounds if c['id'] == k) for k in ['alpha_arbutin', 'beta_arbutin'])
    assert alpha['inchikey'] != beta['inchikey']
    connectivity = lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(s), isomericSmiles=False)
    assert connectivity(alpha['smiles']) == connectivity(beta['smiles'])

    pl.seed_everything(20260928, workers=True)
    torch.set_num_threads(4)
    model = ADMETModel(include_physchem=False, num_workers=0)
    mols, valid = model._filter_valid_molecules(smiles=smiles)
    assert list(valid) == smiles
    loader = model._build_dataloader(mols=mols)
    members, summary = [], []
    for tasks, models in zip(model.task_lists, model.model_lists, strict=True):
        indices = [i for i, t in enumerate(tasks) if t in ACTIVE_AI]
        selected = [tasks[i] for i in indices]
        if not selected:
            continue
        trainer = pl.Trainer(logger=False, enable_checkpointing=False, enable_progress_bar=False, accelerator=model.device, devices=1)
        values = []
        for member_id, member in enumerate(models):
            with torch.inference_mode():
                pred = torch.cat(trainer.predict(model=member, dataloaders=loader), dim=0).detach().cpu().numpy()[:, indices]
            values.append(pred)
            for c, row in zip(compounds, pred, strict=True):
                members.extend({'id': c['id'], 'model': 'ADMET-AI', 'task': t, 'member': member_id, 'value': float(v)} for t, v in zip(selected, row, strict=True))
        values = np.stack(values)
        assert np.isfinite(values).all() and values.shape == (5, 6, len(selected))
        for i, c in enumerate(compounds):
            for j, t in enumerate(selected):
                summary.append({'id': c['id'], 'model': 'ADMET-AI', 'task': t, 'mean': float(values[:, i, j].mean()), 'sd': float(values[:, i, j].std(ddof=1)), 'n_members': 5, 'evidence_type': 'PREDICTED'})
    checkpoints = [{'model': 'ADMET-AI', 'path': str(p.relative_to(DEFAULT_MODELS_DIR)), 'sha256': digest(p)} for p in sorted(DEFAULT_MODELS_DIR.glob('**/*.pt'))]
    old_ai = json.loads((ROOT/'data/raw/skincare/admet_ai/run_metadata.json').read_text())
    assert {c['path']: c['sha256'] for c in checkpoints} == {c['path']: c['sha256'] for c in old_ai['checkpoint_manifest']}
    print('ADMET-AI completed for all six structures and 17 selected tasks.', flush=True)

    features = get_fingerprints(pd.Series(smiles))
    assert np.isfinite(features).all()
    old_map = json.loads((ROOT/'data/raw/skincare/maplight/run_metadata.json').read_text())
    map_values = []
    for checkpoint in old_map['checkpoints']:
        path = Path(checkpoint['matvision_path'])
        assert digest(path) == checkpoint['sha256'], 'Checkpoint changed'
        cb = CatBoostClassifier(thread_count=4)
        cb.load_model(str(path))
        values = cb.predict_proba(features)[:, 1]
        map_values.append(values)
        members.extend({'id': c['id'], 'model': 'MapLight', 'task': 'AMES', 'member': checkpoint['seed'], 'value': float(v)} for c, v in zip(compounds, values, strict=True))
        checkpoints.append({'model': 'MapLight', 'path': str(path), 'sha256': digest(path)})
    map_values = np.stack(map_values)
    for i, c in enumerate(compounds):
        summary.append({'id': c['id'], 'model': 'MapLight', 'task': 'AMES', 'mean': float(map_values[:, i].mean()), 'sd': float(map_values[:, i].std(ddof=1)), 'n_members': 5, 'evidence_type': 'PREDICTED'})

    audit = []
    for split in ['train_val', 'test']:
        path = ROOT/f'data/raw/skincare/maplight/ames_{split}.csv'
        dataset = list(csv.DictReader(path.open()))
        keys = {connectivity(r['Drug']) for r in dataset}
        audit.append({'model': 'MapLight', 'split': split, 'dataset_sha256': digest(path), 'overlapping_ids_connectivity': [c['id'] for c in compounds if connectivity(c['smiles']) in keys]})
    audit.append({'model': 'ADMET-AI', 'training_membership': 'NOT_AUDITED; do not treat this panel as independent validation'})
    old_results = list(csv.DictReader((ROOT/'data/processed/skincare/admet_ai_predictions.csv').open()))
    lookup = {r['task']: float(r['prediction']) for r in old_results if r['compound_id'] == '15'}
    ai_delta = max(abs(r['mean'] - lookup[r['task']]) for r in summary if r['id'] == 'glabridin' and r['model'] == 'ADMET-AI')
    old_map_results = list(csv.DictReader((ROOT/'data/processed/skincare/maplight_predictions.csv').open()))
    old_mean = float(next(r for r in old_map_results if r['compound_id'] == '15')['mean'])
    map_delta = abs(map_values.mean(axis=0)[0] - old_mean)
    assert ai_delta < 1e-5 and map_delta < 1e-10
    arbutin_indices = [next(i for i, c in enumerate(compounds) if c['id'] == k) for k in ['alpha_arbutin', 'beta_arbutin']]
    arbutin_ai_delta = max(abs(next(r['mean'] for r in summary if r['id'] == 'alpha_arbutin' and r['model'] == 'ADMET-AI' and r['task'] == t) - next(r['mean'] for r in summary if r['id'] == 'beta_arbutin' and r['model'] == 'ADMET-AI' and r['task'] == t)) for t in ACTIVE_AI)
    metadata = {'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(), 'execution_host': 'Matvision via SSH alias autodl', 'execution': 'Fresh inference with existing verified checkpoints; no retraining or threshold tuning', 'panel_sha256': digest(PANEL), 'structure_sources': structure_sources, 'checkpoints': checkpoints, 'packages': {p: importlib.metadata.version(p) for p in ['admet-ai', 'chemprop', 'torch', 'rdkit', 'catboost']}, 'selected_tasks_admet_ai': list(ACTIVE_AI), 'packaged_forward_pass_tasks': 41, 'maplight_tasks': ['AMES'], 'seed': 20260928, 'compound_count': len(compounds), 'prediction_rows': len(summary), 'member_prediction_rows': len(members), 'membership_audit': audit, 'glabridin_reproduction_max_abs_delta': {'ADMET-AI': ai_delta, 'MapLight': float(map_delta)}, 'arbutin_stereochemistry_audit': {'distinct_inchikeys': True, 'same_connectivity': True, 'maplight_features_identical': bool(np.array_equal(features[arbutin_indices[0]], features[arbutin_indices[1]])), 'admet_ai_max_mean_difference': arbutin_ai_delta}, 'calibrated_low_risk_threshold': None, 'safe_glabridin_concentration': None, 'actual_exposure_comparison': 'NOT_AVAILABLE', 'limitations': ['SD describes member spread, not a confidence interval.', 'Literature concentrations are not supplied as model inputs.', 'Scores must not be multiplied by concentration to estimate risk.', 'No new eye irritation or phototoxicity model predictions exist for this reference panel.', 'ADMETlab, admetSAR, VEGA and ProTox were not newly run for these references.', 'No formal applicability domain or independent calibration established.']}
    assert len(summary) == 108 and len(members) == 540
    write_json(RAW/'structures.json', compounds)
    write_json(RAW/'member_predictions.json', members)
    write_json(RAW/'run_metadata.json', metadata)
    write_json(RESULT, summary)
    print(json.dumps(metadata, ensure_ascii=False, indent=2), flush=True)


def build_report():
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    panel = json.loads(PANEL.read_text())
    metadata = json.loads((RAW/'run_metadata.json').read_text())
    assert metadata['panel_sha256'] == digest(PANEL), 'Panel changed; predictions must be rerun'
    rows = json.loads(RESULT.read_text())
    compounds = json.loads((RAW/'structures.json').read_text())
    lookup = {(r['id'], r['model'], r['task']): r for r in rows}
    views = [('ADMET-AI', 'Skin_Reaction'), ('ADMET-AI', 'AMES'), ('MapLight', 'AMES'), ('ADMET-AI', 'Carcinogens_Lagunin')]
    figure, axes = plt.subplots(2, 2, figsize=(13, 8.5), sharex=True)
    for ax, (model, task) in zip(axes.flat, views):
        data = [lookup[c['id'], model, task] for c in compounds]
        y = np.arange(len(compounds))
        colors = ['#147d92'] + ['#9bacc0'] * (len(compounds) - 1)
        ax.barh(y, [r['mean'] for r in data], color=colors, height=.58)
        means = np.array([r['mean'] for r in data]); sd = np.array([r['sd'] for r in data])
        ax.errorbar(means, y, xerr=np.stack([np.minimum(sd, means), np.minimum(sd, 1-means)]), fmt='none', color='#30475e', capsize=3)
        for i, r in enumerate(data):
            ax.text(min(r['mean'] + r['sd'] + .025, .96), i, f"{r['mean']:.3f}", va='center', fontsize=9)
        ax.set_yticks(y, [c['name'] for c in compounds]); ax.invert_yaxis()
        ax.set_xlim(0, 1.12); ax.set_xticks([0, .25, .5, .75, 1])
        ax.set_title(f'{model} | {task}', loc='left', fontsize=12, fontweight='bold')
        ax.set_xlabel('Model score (not a human adverse-event probability)')
        ax.spines[['top', 'right']].set_visible(False); ax.grid(axis='x', alpha=.15); ax.set_axisbelow(True)
    figure.suptitle('Glabridin and evidence-selected cosmetic references', fontsize=17, fontweight='bold', y=.98)
    figure.text(.04, .025, 'PREDICTED | Mean +/- SD across 5 members; error bars clipped to [0, 1]. SD is not a confidence interval.\nSource use concentrations are not model inputs. No safety threshold, efficacy matching or exposure-based ranking.', fontsize=10)
    figure.tight_layout(rect=(0, .08, 1, .95))
    figdir = ROOT/'figures/skincare'; figdir.mkdir(parents=True, exist_ok=True)
    for ext in ['png', 'svg']:
        figure.savefig(figdir/f'reference_comparison.{ext}', dpi=180, bbox_inches='tight')
    plt.close(figure)

    text = ['# 光甘草定护肤品参照成分与首次模型比较', '', '参照组于 2026-09-29 根据公开安全资料、用途和结构确定，并在查看本轮预测前固定。保留全部入选成分。', '', '**这些是有条件安全使用资料的参照原料，不是所有终点均为阴性的对照组。没有建立光甘草定的安全浓度或低风险阈值。**', '', '## 入选资料与条件', '', '| 成分 | 角色 | 资料支持范围 |', '|---|---|---|']
    for ref in panel['references']:
        sources = '、'.join(f"[{s}]({panel['sources'][s]['url']})" for s in ref['source_ids'])
        text.append(f"| {ref['name_zh']}（{ref['name']}，CAS {ref['cas']}） | {ref['role']} | {ref['evidence_summary_zh']} {sources} |")
    text += ['', '浓度含义必须区分：SCCS 的指定使用条件、EU 限制、CIR 报告的实际用量与单项试验浓度并不等价。EU 资料不代表已完成中国市场合规审核。抗坏血酸葡糖苷作为抗氧化/皮肤调理补充参照，其 CIR 结论不覆盖脱色用途。烟酰胺 2005 评估属于历史资料，不称为新近重评结果。', '', '## 同模型、同终点的预测', '', '| 成分 | ADMET-AI Skin_Reaction | ADMET-AI AMES | MapLight AMES | ADMET-AI Carcinogens_Lagunin |', '|---|---:|---:|---:|---:|']
    for c in compounds:
        cells = [f"{lookup[c['id'], m, t]['mean']:.3f} ± {lookup[c['id'], m, t]['sd']:.3f}" for m, t in views]
        text.append('| ' + c['name_zh'] + ' | ' + ' | '.join(cells) + ' |')
    skin_target = lookup['glabridin', 'ADMET-AI', 'Skin_Reaction']['mean']
    skin_refs = [lookup[c['id'], 'ADMET-AI', 'Skin_Reaction']['mean'] for c in compounds if c['id'] != 'glabridin']
    text += ['', '![参照模型比较](../../figures/skincare/reference_comparison.png)', '', '数值为五成员均值 ± 标准差；不同列不能平均或互换。仅为结构预测，不含浓度、配方、经皮吸收和用量。不能将分数乘以浓度作为真实风险。', '', f"本轮 ADMET-AI Skin_Reaction：光甘草定 {skin_target:.3f}，五种参照均值范围 {min(skin_refs):.3f}–{max(skin_refs):.3f}。该结果支持优先验证皮肤相关警示，不能建立整体安全优势，也不是人体不良反应发生率。", '', '## 结果解释与证据缺口', '', '- 光甘草定的既有皮肤/眼部等警示继续保留。某一模型分数低于参照物不构成整体更安全的结论。', '- α/β-熊果苷保留独立立体结构。本轮 MapLight 特征完全相同、输出相同；ADMET-AI 并非完全相同。不能由此证明两种异构体生物效应相同，也不能作为两个独立支持票。', '- 该小参照组不是外部校准数据集；未知训练成员身份不视作无重叠。', '- 尚未为参照物运行 admetSAR、ADMETlab、VEGA 或 ProTox；尤其未完成参照组眼刺激/光毒性比较，缺失不记作阴性。', '- 光甘草定使用浓度、成品配方、经皮吸收和等效功效条件缺失，尚不能完成实际风险排序。', '- 需要另外建立带终点实验标签的阳性/阴性验证集，并核查训练集重叠与适用域。', '', '### 已核查的 MapLight 数据集重叠', '']
    for item in metadata['membership_audit']:
        text.append('- ' + json.dumps(item, ensure_ascii=False))
    text += ['', '### 原始数据与复现', '', '- [固定参照清单与来源](../../data/compounds/skincare_reference_panel.json)', '- [全部 108 项模型输出](../../results/tables/skincare/reference_predictions.json)', '- [540 项成员输出](../../data/raw/skincare/references/member_predictions.json)', '- [运行元数据与校验和](../../data/raw/skincare/references/run_metadata.json)', '', 'Matvision：`python -m analysis.models.skincare_references --predict` 执行新推理；不带参数仅重建报告与图。既有五成员 MapLight AMES 检查点复用，不重新训练。ADMET-AI 提取同一组 17 个护肤任务；共享网络包含的其他输出不进入比较。', '']
    path = ROOT/'docs/methodology/skincare_reference_panel_zh.md'
    path.write_text('\n'.join(text), encoding='utf-8')
    print(path, flush=True)


def render_html(root, table):
    panel = json.loads((root/'data/compounds/skincare_reference_panel.json').read_text())
    refs = [{'name': r['name_zh'], 'role': r['role'], 'evidence': r['evidence_summary_zh']} for r in panel['references']]
    body = '<h3>有公开安全评估的护肤原料参照</h3><p>参照名单在本轮预测前固定：α-熊果苷、烟酰胺为主要用途参照；抗坏血酸葡糖苷补充抗氧化/调理用途；曲酸保留使用条件；β-熊果苷扩展立体异构体比较。它们都不是所有终点阴性的标准品。</p>'
    body += table(refs, [('name', '参照成分'), ('role', '角色'), ('evidence', '证据与使用条件')])
    body += '<p>浓度来自特定评估或试验，未输入结构预测模型，也不能作为光甘草定的安全浓度。CIR 报告用量不等于法规上限。抗坏血酸葡糖苷的 CIR 结论不覆盖脱色用途。完整来源与条件见下方报告。</p><figure class="figure"><img src="figures/skincare/reference_comparison.svg" alt="光甘草定与五种护肤参照成分在同模型终点下的预测比较"><figcaption>PREDICTED：均值 ± 五成员标准差，不是人体发生率或置信区间。没有安全分界线，不进行跨终点综合排名。</figcaption></figure><p>新推理使用既有检查点：ADMET-AI 提取 17 项任务，MapLight 预测 AMES。原光甘草定输出复现一致。烟酰胺出现在 MapLight 训练集，曲酸出现在其固定测试集；ADMET-AI 训练成员身份未核查。这组参照不能作为新的独立验证集。参照组眼刺激和光毒性预测仍缺失。</p><div class="downloads"><a href="docs/methodology/skincare_reference_panel_zh.md">参照依据及结果</a><a href="data/compounds/skincare_reference_panel.json">固定参照清单</a><a href="results/tables/skincare/reference_predictions.json">108 项模型输出</a><a href="data/raw/skincare/references/run_metadata.json">运行校验与限制</a></div>'
    return body


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--predict', action='store_true')
    args = parser.parse_args()
    if args.predict:
        predict()
    build_report()

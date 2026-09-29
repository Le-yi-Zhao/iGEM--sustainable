#!/usr/bin/env python3
"""Run the official local ADMET-AI v2 ensembles and cache member predictions."""
from __future__ import annotations

import csv
import hashlib
import shutil
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path




ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/raw/skincare/admet_ai"
RAW_WIDE = RAW_DIR / "admet_ai_predictions.csv"
RAW_MEMBERS = RAW_DIR / "ensemble_member_predictions.csv"
METADATA = RAW_DIR / "run_metadata.json"
PROCESSED = ROOT / "data/processed/skincare/admet_ai_predictions.csv"


def confirmed_compounds() -> list[dict[str, str]]:
    with (ROOT / "data/compounds/compound_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row["structure_confirmed"].lower() == "yes"]


def run(force: bool = False) -> Path:
    if RAW_WIDE.exists() and RAW_MEMBERS.exists() and PROCESSED.exists() and not force:
        return RAW_WIDE

    # Prediction dependencies are needed only when rebuilding the model cache.
    import numpy as np
    import pandas as pd
    import torch
    from admet_ai import ADMETModel
    from admet_ai.admet_info import get_admet_info
    from admet_ai.physchem import compute_physicochemical_properties
    from lightning import pytorch as pl

    from analysis.models.skincare_scope import ACTIVE_AI
    started = datetime.now(timezone.utc).isoformat()
    pl.seed_everything(20260928, workers=True)
    torch.set_num_threads(4)
    compounds = confirmed_compounds()
    smiles = [row["canonical_smiles"] for row in compounds]
    model = ADMETModel(include_physchem=True, num_workers=0)
    mols, valid_smiles = model._filter_valid_molecules(smiles=smiles)
    if list(valid_smiles) != smiles:
        raise RuntimeError("ADMET-AI did not accept every structure-confirmed input in manifest order")
    loader = model._build_dataloader(mols=mols)

    task_means: dict[str, np.ndarray] = {}
    task_stds: dict[str, np.ndarray] = {}
    member_records: list[dict[str, object]] = []
    ensemble_sizes: dict[str, int] = {}

    for tasks, members in zip(model.task_lists, model.model_lists, strict=True):
        selected_indices = [i for i, task in enumerate(tasks) if task in ACTIVE_AI]
        tasks = [tasks[i] for i in selected_indices]
        if not tasks:
            continue
        trainer = pl.Trainer(
            logger=False,
            enable_checkpointing=False,
            enable_progress_bar=False,
            accelerator=model.device,
            devices=1,
        )
        arrays = []
        for member_index, member in enumerate(members):
            with torch.inference_mode():
                values = torch.cat(trainer.predict(model=member, dataloaders=loader), dim=0).detach().cpu().numpy()
            values = values[:, selected_indices]
            arrays.append(values)
            for compound, task_values in zip(compounds, values, strict=True):
                for task_index, task in enumerate(tasks):
                    member_records.append({
                        "compound_id": compound["compound_id"],
                        "compound_name": compound["compound_name"],
                        "task": task,
                        "ensemble_member": member_index,
                        "prediction": float(task_values[task_index]),
                        "evidence_type": "PREDICTED",
                    })
        stacked = np.stack(arrays)
        if stacked.shape != (len(members), len(compounds), len(tasks)) or not np.isfinite(stacked).all():
            raise RuntimeError("Invalid ensemble prediction shape or nonfinite output")
        ensemble_sizes["classification" if np.all((stacked >= 0) & (stacked <= 1)) else "regression"] = len(members)
        for task_index, task in enumerate(tasks):
            task_means[task] = stacked[:, :, task_index].mean(axis=0)
            task_stds[task] = stacked[:, :, task_index].std(axis=0, ddof=1)

    prediction_df = pd.DataFrame(task_means, index=smiles)
    physchem_df = compute_physicochemical_properties(all_smiles=smiles, mols=mols)
    combined = pd.concat([physchem_df, prediction_df], axis=1)
    combined = model._add_drugbank_percentiles(preds=combined, smiles=smiles)
    combined.insert(0, "compound_name", [row["compound_name"] for row in compounds])
    combined.insert(0, "compound_id", [row["compound_id"] for row in compounds])
    combined.index.name = "smiles"

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    # Preserve the exact previous exports before promoting a successful fresh inference.
    if force and RAW_WIDE.exists():
        archive = RAW_DIR / "archive" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive.mkdir(parents=True, exist_ok=False)
        for previous in [RAW_WIDE, RAW_MEMBERS, METADATA, PROCESSED]:
            if previous.exists():
                name = "processed_predictions.csv" if previous == PROCESSED else previous.name
                shutil.copy2(previous, archive / name)
    combined.to_csv(RAW_WIDE)
    pd.DataFrame(member_records).to_csv(RAW_MEMBERS, index=False)

    info = get_admet_info().set_index("id")
    processed_records = []
    for compound_index, compound in enumerate(compounds):
        for task in prediction_df.columns:
            row = info.loc[task]
            percentile_column = f"{task}_drugbank_approved_percentile"
            processed_records.append({
                "compound_id": compound["compound_id"],
                "compound_name": compound["compound_name"],
                "task": task,
                "endpoint": row["name"],
                "category": row["category"],
                "task_type": row["task_type"],
                "species": row["species"],
                "units": row["units"],
                "training_size": row["size"],
                "reference_auprc": row["AUPRC"],
                "reference_auroc": row["AUROC"],
                "reference_r2": row["R^2"],
                "reference_mae": row["MAE"],
                "prediction": task_means[task][compound_index],
                "ensemble_std": task_stds[task][compound_index],
                "drugbank_approved_percentile": combined.iloc[compound_index].get(percentile_column, np.nan),
                "model": "ADMET-AI 2.0.1",
                "evidence_type": "PREDICTED",
            })
    pd.DataFrame(processed_records).to_csv(PROCESSED, index=False)

    from admet_ai.constants import DEFAULT_MODELS_DIR
    checkpoints = [{"path": path.relative_to(DEFAULT_MODELS_DIR).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                   for path in sorted(DEFAULT_MODELS_DIR.glob("**/*.pt"))]
    metadata = {
        "profile": "skincare",
        "selected_tasks": list(ACTIVE_AI),
        "packaged_output_tasks": 41,
        "selection_note": "Packaged multitask forward passes are shared; only 17 selected tasks are extracted and analyzed. No retraining or independent computation of excluded tasks is scheduled.",
        "execution_mode": "fresh checkpoint inference (not cache import)",
        "seed": 20260928,
        "checkpoint_manifest": checkpoints,
        "input_sha256": hashlib.sha256((ROOT / "data/compounds/compound_manifest.csv").read_bytes()).hexdigest(),
        "numpy_version": np.__version__,
        "cuda_runtime": torch.version.cuda,
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "model": "ADMET-AI v2",
        "package_version": importlib.metadata.version("admet-ai"),
        "chemprop_version": importlib.metadata.version("chemprop"),
        "torch_version": importlib.metadata.version("torch"),
        "rdkit_version": importlib.metadata.version("rdkit"),
        "official_repository": "https://github.com/swansonk14/admet_ai",
        "dataset": "Therapeutics Data Commons ADMET tasks; packaged model checkpoints",
        "reference_distribution": "Packaged DrugBank approved compounds",
        "input_manifest": "data/compounds/compound_manifest.csv",
        "compound_count": len(compounds),
        "task_count": len(prediction_df.columns),
        "ensemble_sizes": ensemble_sizes,
        "device": model.device,
        "platform": platform.platform(),
        "started_utc": started,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "raw_predictions": str(RAW_WIDE.relative_to(ROOT)),
        "raw_member_predictions": str(RAW_MEMBERS.relative_to(ROOT)),
        "processed_predictions": str(PROCESSED.relative_to(ROOT)),
    }
    METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return RAW_WIDE


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(run(force=args.force))

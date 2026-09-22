from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd


def run(root: Path) -> Path:
    harmonization = pd.read_csv(root / "docs/methodology/endpoint_harmonization.csv")
    harmonization = harmonization[harmonization["comparable"].eq("yes")]
    admet_ai = pd.read_csv(root / "data/processed/admet_ai_predictions.csv")
    admetlab = pd.read_csv(root / "data/raw/admetlab/admetlab_predictions.csv")
    manifest = pd.read_csv(root / "data/compounds/compound_manifest.csv")
    admetlab.insert(0, "compound_id", manifest["compound_id"].astype(str))

    uncertainty_cutoff = float(admet_ai.loc[admet_ai["task_type"].eq("classification"), "ensemble_std"].quantile(.75))
    rows: list[dict[str, object]] = []
    for _, mapping in harmonization.iterrows():
        ai_rows = admet_ai[admet_ai["task"].eq(mapping["admet_ai_task"])]
        for _, ai in ai_rows.iterrows():
            lab = admetlab[admetlab["compound_id"].astype(str).eq(str(ai["compound_id"]))].iloc[0]
            ai_probability = float(ai["prediction"])
            lab_probability = float(lab[mapping["admetlab_raw_endpoint"]])
            ai_concern = ai_probability >= .5
            lab_concern = lab_probability >= .5
            if float(ai["ensemble_std"]) >= uncertainty_cutoff:
                consensus = "HIGH_UNCERTAINTY"
            elif ai_concern != lab_concern:
                consensus = "MODEL_DISAGREEMENT"
            elif ai_concern:
                consensus = "CONSENSUS_CONCERN"
            else:
                consensus = "CONSENSUS_LOW_CONCERN"
            rows.append({
                "compound_id": ai["compound_id"],
                "compound_name": ai["compound_name"],
                "endpoint": mapping["harmonized_endpoint"],
                "admet_ai_probability": ai_probability,
                "admet_ai_ensemble_std": ai["ensemble_std"],
                "admet_ai_drugbank_percentile": ai["drugbank_approved_percentile"],
                "admetlab_probability": lab_probability,
                "absolute_probability_difference": abs(ai_probability - lab_probability),
                "uncertainty_cutoff_empirical_p75": uncertainty_cutoff,
                "consensus": consensus,
                "evidence_type": "PREDICTED",
            })
    output = root / "results/tables/multi_model_toxicity_consensus.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)
    return output

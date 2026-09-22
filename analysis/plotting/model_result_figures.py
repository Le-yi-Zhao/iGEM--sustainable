from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from admet_ai.constants import DEFAULT_DRUGBANK_PATH
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


INK = "#21182B"
MUTED = "#6E6576"
PURPLE = "#6F3CA7"
LINE = "#DED4E7"
COMPOUND_COLORS = ["#5A2C83", "#6F3CA7", "#8454B3", "#9A70C4", "#B18BD2", "#C8A9DF"]
KEY_TASKS = ["AMES", "DILI", "ClinTox", "hERG", "Carcinogens_Lagunin", "Skin_Reaction"]


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight", metadata={"Creator": "analysis/plotting/model_result_figures.py"})
    plt.close(fig)


def _toxicity(root: Path) -> pd.DataFrame:
    data = pd.read_csv(root / "data/processed/admet_ai_predictions.csv")
    return data[data["category"].eq("Toxicity")].copy()


def endpoint_heatmap(root: Path) -> None:
    data = _toxicity(root)
    data = data[data["task_type"].eq("classification")]
    compounds = data[["compound_id", "compound_name"]].drop_duplicates()
    tasks = data[["task", "endpoint"]].drop_duplicates()
    matrix = data.pivot(index="compound_id", columns="task", values="prediction").reindex(index=compounds["compound_id"], columns=tasks["task"])
    labels = [f"{row.compound_id} · {row.compound_name}" for row in compounds.itertuples()]
    cmap = LinearSegmentedColormap.from_list("probability", ["#EAF6EF", "#FFF3D2", "#B94C59"])
    fig, ax = plt.subplots(figsize=(17, 6.6))
    image = ax.imshow(matrix.values, vmin=0, vmax=1, cmap=cmap, aspect="auto")
    ax.set_title("ADMET-AI v2 toxicity endpoint predictions", loc="left", fontsize=18, weight="bold", color=INK, pad=16)
    ax.set_xticks(range(len(tasks)), [name.replace(" ", "\n") for name in tasks["endpoint"]], fontsize=7.5)
    ax.set_yticks(range(len(labels)), labels, fontsize=9)
    colorbar = fig.colorbar(image, ax=ax, fraction=.022, pad=.015)
    colorbar.set_label("Predicted positive-class probability")
    ax.text(0, -.29, "PREDICTED · Official ADMET-AI 2.0.1 local Chemprop ensemble. All classification toxicity tasks are shown; endpoints were not selected by favorability.", transform=ax.transAxes, fontsize=9, color=MUTED)
    _save(fig, root / "figures/supporting/admet_ai_endpoint_heatmap.svg")


def compound_profiles(root: Path) -> None:
    data = _toxicity(root)
    data = data[data["task"].isin(KEY_TASKS)]
    compounds = data[["compound_id", "compound_name"]].drop_duplicates()
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5), sharex=True)
    for ax, compound, color in zip(axes.flat, compounds.itertuples(), COMPOUND_COLORS):
        subset = data[data["compound_id"].eq(compound.compound_id)].set_index("task").reindex(KEY_TASKS)
        y = np.arange(len(subset))
        ax.errorbar(subset["prediction"], y, xerr=subset["ensemble_std"], fmt="o", color=color, ecolor="#AFA5B5", capsize=3)
        ax.axvline(.5, color="#B94C59", linestyle="--", linewidth=1)
        ax.set_yticks(y, subset["endpoint"], fontsize=8)
        ax.set_xlim(0, 1)
        ax.set_title(f"{compound.compound_id} · {compound.compound_name}", loc="left", fontsize=10, weight="bold")
        ax.grid(axis="x", color=LINE, linewidth=.7)
    fig.suptitle("ADMET-AI compound toxicity profiles", x=.08, ha="left", fontsize=18, weight="bold", color=INK)
    fig.text(.08, .01, "PREDICTED · Points are five-member ensemble means; error bars are observed ensemble-member standard deviations. The dashed line is the binary model decision threshold, not a safety threshold.", fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, .05, 1, .94))
    _save(fig, root / "figures/supporting/admet_ai_compound_profiles.svg")


def drugbank_reference(root: Path) -> None:
    project = _toxicity(root)
    project = project[project["task"].isin(KEY_TASKS)]
    reference = pd.read_csv(DEFAULT_DRUGBANK_PATH)
    fig, ax = plt.subplots(figsize=(13.5, 7.2))
    distributions = [reference[task].dropna().values for task in KEY_TASKS]
    parts = ax.violinplot(distributions, positions=np.arange(len(KEY_TASKS)), showmeans=False, showmedians=True, widths=.82)
    for body in parts["bodies"]:
        body.set_facecolor("#DCCCEB"); body.set_edgecolor(PURPLE); body.set_alpha(.8)
    parts["cmedians"].set_color(INK)
    for compound_index, (compound_id, subset) in enumerate(project.groupby("compound_id", sort=False)):
        subset = subset.set_index("task").reindex(KEY_TASKS)
        jitter = (compound_index - 2.5) * .035
        ax.scatter(np.arange(len(KEY_TASKS)) + jitter, subset["prediction"], s=42, color=COMPOUND_COLORS[compound_index], edgecolor="white", label=str(compound_id), zorder=3)
    endpoint_names = project.drop_duplicates("task").set_index("task").reindex(KEY_TASKS)["endpoint"]
    ax.set_xticks(range(len(KEY_TASKS)), endpoint_names, rotation=20, ha="right")
    ax.set_ylim(-.03, 1.03)
    ax.set_ylabel("Prediction probability")
    ax.set_title("Project compounds within the packaged DrugBank-approved prediction distributions", loc="left", fontsize=17, weight="bold", color=INK, pad=15)
    ax.legend(title="Compound ID", ncol=6, loc="upper center", bbox_to_anchor=(.5, 1.02))
    ax.grid(axis="y", color=LINE, linewidth=.7)
    ax.text(0, -.23, f"PREDICTED · Reference distributions contain {len(reference):,} packaged DrugBank-approved compounds. They are prediction distributions, not observed safety distributions.", transform=ax.transAxes, fontsize=9, color=MUTED)
    _save(fig, root / "figures/supporting/admet_ai_drugbank_reference.svg")


def prediction_space(root: Path) -> None:
    project = pd.read_csv(root / "data/raw/admet_ai/admet_ai_predictions.csv")
    processed = pd.read_csv(root / "data/processed/admet_ai_predictions.csv")
    task_columns = processed["task"].drop_duplicates().tolist()
    reference = pd.read_csv(DEFAULT_DRUGBANK_PATH).dropna(subset=task_columns)
    scaler = StandardScaler().fit(reference[task_columns])
    reference_scaled = scaler.transform(reference[task_columns])
    project_scaled = scaler.transform(project[task_columns])
    pca = PCA(n_components=2).fit(reference_scaled)
    reference_xy = pca.transform(reference_scaled)
    project_xy = pca.transform(project_scaled)
    fig, ax = plt.subplots(figsize=(9.8, 7.2))
    ax.scatter(reference_xy[:, 0], reference_xy[:, 1], s=8, color="#CFC7D4", alpha=.32, label=f"DrugBank reference (n={len(reference):,})")
    ax.scatter(project_xy[:, 0], project_xy[:, 1], s=120, c=COMPOUND_COLORS, edgecolor="white", linewidth=1.2, label="GALATEA compounds")
    for row, (x, y) in zip(project.itertuples(), project_xy):
        ax.annotate(str(row.compound_id), (x, y), xytext=(5, 5), textcoords="offset points", weight="bold", color=INK)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)")
    ax.set_title("ADMET-AI prediction-space context", loc="left", fontsize=18, weight="bold", color=INK, pad=15)
    ax.legend(loc="best")
    ax.grid(color=LINE, linewidth=.7)
    ax.text(0, -.15, "PREDICTED · PCA was fitted on standardized ADMET-AI task predictions for the packaged DrugBank reference. Distance is descriptive and is not a safety ranking or applicability-domain certificate.", transform=ax.transAxes, fontsize=9, color=MUTED)
    _save(fig, root / "figures/supporting/admet_ai_compound_distance.svg")


def ensemble_uncertainty(root: Path) -> None:
    data = _toxicity(root)
    data = data[data["task_type"].eq("classification")]
    compounds = data[["compound_id", "compound_name"]].drop_duplicates()
    tasks = data[["task", "endpoint"]].drop_duplicates()
    matrix = data.pivot(index="compound_id", columns="task", values="ensemble_std").reindex(index=compounds["compound_id"], columns=tasks["task"])
    fig, ax = plt.subplots(figsize=(17, 6.6))
    image = ax.imshow(matrix.values, cmap="magma_r", vmin=0, vmax=max(.2, matrix.values.max()), aspect="auto")
    ax.set_title("ADMET-AI ensemble-member uncertainty", loc="left", fontsize=18, weight="bold", color=INK, pad=16)
    ax.set_xticks(range(len(tasks)), [name.replace(" ", "\n") for name in tasks["endpoint"]], fontsize=7.5)
    ax.set_yticks(range(len(compounds)), [f"{r.compound_id} · {r.compound_name}" for r in compounds.itertuples()], fontsize=9)
    colorbar = fig.colorbar(image, ax=ax, fraction=.022, pad=.015)
    colorbar.set_label("Standard deviation across 5 ensemble members")
    ax.text(0, -.29, "PREDICTED · Uncertainty is calculated from the five packaged ADMET-AI v2 ensemble checkpoints for each task; it is not an arbitrary error band.", transform=ax.transAxes, fontsize=9, color=MUTED)
    _save(fig, root / "figures/supporting/admet_ai_ensemble_uncertainty.svg")


def multi_model_figures(root: Path) -> None:
    data = pd.read_csv(root / "results/tables/multi_model_toxicity_consensus.csv")
    compounds = data[["compound_id", "compound_name"]].drop_duplicates()
    endpoints = data["endpoint"].drop_duplicates().tolist()
    state_order = ["CONSENSUS_LOW_CONCERN", "CONSENSUS_CONCERN", "MODEL_DISAGREEMENT", "HIGH_UNCERTAINTY"]
    state_to_number = {state: i for i, state in enumerate(state_order)}
    state_matrix = data.assign(code=data["consensus"].map(state_to_number)).pivot(index="compound_id", columns="endpoint", values="code").reindex(index=compounds["compound_id"], columns=endpoints)
    colors = ["#5CA978", "#B94C59", "#D69A2D", "#76528F"]
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.imshow(state_matrix.values, cmap=ListedColormap(colors), norm=BoundaryNorm(np.arange(-.5, 4.5), 4), aspect="auto")
    ax.set_xticks(range(len(endpoints)), endpoints, rotation=20, ha="right")
    ax.set_yticks(range(len(compounds)), [f"{r.compound_id} · {r.compound_name}" for r in compounds.itertuples()])
    for i in range(state_matrix.shape[0]):
        for j in range(state_matrix.shape[1]):
            ax.text(j, i, state_order[int(state_matrix.iloc[i, j])].replace("CONSENSUS_", "").replace("MODEL_", "").replace("HIGH_", ""), ha="center", va="center", fontsize=7.5, color="white", weight="bold")
    handles = [plt.Line2D([0], [0], marker="s", linestyle="", color=color, label=state.replace("_", " ")) for state, color in zip(state_order, colors)]
    ax.legend(handles=handles, ncol=2, loc="upper center", bbox_to_anchor=(.5, 1.22), fontsize=8)
    ax.set_title("ADMET-AI × ADMETlab toxicity consensus", loc="left", fontsize=18, weight="bold", color=INK, pad=38)
    ax.text(0, -.27, "PREDICTED · Consensus uses only four definition-matched endpoints. Probabilities are not averaged. HIGH UNCERTAINTY uses the empirical 75th percentile of ADMET-AI ensemble SD.", transform=ax.transAxes, fontsize=9, color=MUTED)
    _save(fig, root / "figures/evidence/multi_model_toxicity_consensus.svg")

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 9), sharex=True, sharey=True)
    for ax, endpoint in zip(axes.flat, endpoints):
        subset = data[data["endpoint"].eq(endpoint)]
        ax.plot([0, 1], [0, 1], color=LINE, linestyle="--")
        ax.scatter(subset["admet_ai_probability"], subset["admetlab_probability"], c=COMPOUND_COLORS, s=80, edgecolor="white")
        for row in subset.itertuples():
            ax.annotate(str(row.compound_id), (row.admet_ai_probability, row.admetlab_probability), xytext=(4, 4), textcoords="offset points", fontsize=8)
        ax.set_title(endpoint, loc="left", fontsize=11, weight="bold")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.grid(color=LINE, linewidth=.7)
    fig.supxlabel("ADMET-AI probability"); fig.supylabel("ADMETlab probability")
    fig.suptitle("Independent-model agreement", x=.08, ha="left", fontsize=18, weight="bold", color=INK)
    fig.text(.08, .01, "PREDICTED · The diagonal is equality, not a fitted calibration line. Differences are preserved rather than averaged away.", fontsize=9, color=MUTED)
    fig.tight_layout(rect=(.04, .05, 1, .94))
    _save(fig, root / "figures/supporting/multi_model_agreement_matrix.svg")

    difference = data.pivot(index="compound_id", columns="endpoint", values="absolute_probability_difference").reindex(index=compounds["compound_id"], columns=endpoints)
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    image = ax.imshow(difference.values, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(endpoints)), endpoints, rotation=20, ha="right")
    ax.set_yticks(range(len(compounds)), [f"{r.compound_id} · {r.compound_name}" for r in compounds.itertuples()])
    for i in range(difference.shape[0]):
        for j in range(difference.shape[1]):
            ax.text(j, i, f"{difference.iloc[i, j]:.2f}", ha="center", va="center", fontsize=9, color=INK)
    colorbar = fig.colorbar(image, ax=ax, fraction=.035, pad=.02); colorbar.set_label("Absolute probability difference")
    ax.set_title("Toxicity model disagreement", loc="left", fontsize=18, weight="bold", color=INK, pad=15)
    ax.text(0, -.27, "PREDICTED · Larger differences define model-validation priorities; they are not hidden by probability averaging.", transform=ax.transAxes, fontsize=9, color=MUTED)
    _save(fig, root / "figures/supporting/toxicity_model_disagreement.svg")

    fig, ax = plt.subplots(figsize=(10, 6.5))
    for endpoint_index, endpoint in enumerate(endpoints):
        subset = data[data["endpoint"].eq(endpoint)]
        ax.scatter(subset["admet_ai_probability"], subset["admet_ai_ensemble_std"], s=65, alpha=.85, label=endpoint)
    cutoff = data["uncertainty_cutoff_empirical_p75"].iloc[0]
    ax.axvline(.5, color="#B94C59", linestyle="--", linewidth=1)
    ax.axhline(cutoff, color="#76528F", linestyle="--", linewidth=1)
    ax.set_xlabel("ADMET-AI predicted positive-class probability")
    ax.set_ylabel("ADMET-AI five-member ensemble SD")
    ax.set_title("Prediction versus ensemble uncertainty", loc="left", fontsize=18, weight="bold", color=INK, pad=15)
    ax.legend(fontsize=8, ncol=2)
    ax.grid(color=LINE, linewidth=.7)
    ax.text(0, -.17, "PREDICTED · Dashed lines show the binary decision threshold and the observed 75th-percentile ensemble SD. High probability and low uncertainty are visually distinct from uncertain predictions.", transform=ax.transAxes, fontsize=9, color=MUTED)
    _save(fig, root / "figures/supporting/prediction_vs_uncertainty.svg")


def run(root: Path) -> None:
    endpoint_heatmap(root)
    compound_profiles(root)
    drugbank_reference(root)
    prediction_space(root)
    ensemble_uncertainty(root)
    multi_model_figures(root)

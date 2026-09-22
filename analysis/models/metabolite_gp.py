from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel


COMPOUNDS = ["precursor_concentration", "compound_14_concentration", "compound_9_concentration", "compound_10_concentration", "compound_11_concentration", "compound_13_concentration", "glabridin_concentration"]


def run(root: Path) -> list[Path]:
    source = root / "data/wetlab/metabolite_timecourse_template.csv"
    df = pd.read_csv(source)
    if df.empty:
        return []
    outputs: list[Path] = []
    for compound in COMPOUNDS:
        subset = df.dropna(subset=["time_day", compound, "group"])
        if subset.empty:
            continue
        fig, ax = plt.subplots(figsize=(8, 5))
        for group, grp in subset.groupby("group"):
            x = grp["time_day"].to_numpy(float).reshape(-1, 1)
            y = grp[compound].to_numpy(float)
            ax.scatter(x[:, 0], y, s=28, alpha=.75, label=f"{group} raw")
            if len(np.unique(x)) >= 3 and len(y) >= 5:
                kernel = ConstantKernel(1.0, (1e-3, 1e3)) * RBF(2.0, (1e-2, 1e2)) + WhiteKernel(1.0, (1e-6, 1e2))
                gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, random_state=2026, n_restarts_optimizer=2)
                gp.fit(x, y)
                grid = np.linspace(x.min(), x.max(), 200).reshape(-1, 1)
                mean, std = gp.predict(grid, return_std=True)
                ax.plot(grid[:, 0], mean, lw=2, label=f"{group} GP")
                ax.fill_between(grid[:, 0], mean-1.96*std, mean+1.96*std, alpha=.18)
        ax.set(title=compound.replace("_", " ").title(), xlabel="Time (day)", ylabel="Concentration (input unit)")
        ax.legend(frameon=False); ax.grid(alpha=.2)
        path = root / f"figures/evidence/gp_{compound}.svg"; path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, format="svg", bbox_inches="tight", metadata={"Creator":"analysis/models/metabolite_gp.py"}); plt.close(fig); outputs.append(path)
    return outputs


"""Which reference compounds remain unmeasured at each candidate panel size?"""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def run(root: Path):
    with (root / "results/tables/metabolite_panel_coverage.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    with plt.rc_context({"svg.hashsalt": "galatea-panel-coverage", "font.family": "DejaVu Sans"}):
        fig, ax = plt.subplots(figsize=(11, 5.8))
        values = [int(r["planned_analytes"]) for r in rows]
        ax.barh(range(len(rows)), values, color="#714299", height=0.55)
        ax.set_yticks(range(len(rows)), ["{"+r["panel"].replace(";", ", ")+"}" for r in rows])
        ax.invert_yaxis()
        ax.set_xlim(0, 10)
        ax.set_xticks(range(7))
        ax.set_xlabel("Planned analytes in the six-compound reference set")
        ax.set_title("Which compounds does each panel leave unmeasured?", loc="left", pad=20)
        for i, r in enumerate(rows):
            ax.text(values[i]+0.12, i, f'{values[i]}/6 ({float(r["node_coverage_percent"]):g}%)', va="center")
            ax.text(7.4, i, r["unmeasured_ids"].replace(";", ", ") or "None", va="center", fontsize=10)
        ax.text(7.4, -0.55, "Unmeasured IDs", fontsize=10, weight="bold")
        ax.spines[["top", "right", "left"]].set_visible(False)
        fig.text(0.02, 0.03, "SCENARIO design coverage | Database-derived compound identities\nNot measured performance, whole-pathway coverage, observability or information gain.", fontsize=10)
        fig.tight_layout(rect=(0,0.12,1,1))
        path=root / "figures/evidence/metabolite_panel_coverage.svg"
        fig.savefig(path, metadata={"Date": None, "Creator": "analysis/plotting/panel_coverage_figure.py"})
        plt.close(fig)
    return path

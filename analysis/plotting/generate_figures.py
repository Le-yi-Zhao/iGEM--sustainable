from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


PURPLE = "#6F3CA7"
INK = "#21182B"
MUTED = "#6E6576"
GREEN = "#2F7D5B"
AMBER = "#9A6500"
RED = "#9A4650"
LIGHT = "#F7F2FB"
LINE = "#DED4E7"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight", metadata={"Creator": "analysis/plotting/generate_figures.py"})
    plt.close(fig)


def structure_audit(root: Path) -> None:
    rows = _rows(root / "results/tables/compound_structure_audit.csv")
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.axis("off")
    ax.set_title("Chemical structure quality control", loc="left", fontsize=18, weight="bold", color=INK, pad=18)
    ax.text(0, 1.01, "PubChem records re-parsed with RDKit 2025.03.6", transform=ax.transAxes, color=MUTED, fontsize=10)
    headers = ["ID", "Compound", "Parse", "Formula", "MW", "InChIKey", "Duplicate", "Status"]
    data = []
    for r in rows:
        data.append([
            r["compound_id"], r["compound_name"], r["parse_success"], r["formula_match"],
            r["molecular_weight_match"], r["inchikey_match"], r["duplicate_connectivity_of"] or "none", r["audit_status"],
        ])
    table = ax.table(cellText=data, colLabels=headers, loc="center", cellLoc="center", colWidths=[.05,.24,.08,.08,.08,.10,.10,.10])
    table.auto_set_font_size(False); table.set_fontsize(9); table.scale(1, 1.55)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(LINE)
        if row == 0:
            cell.set_facecolor(PURPLE); cell.get_text().set_color("white"); cell.get_text().set_weight("bold")
        elif row % 2 == 0:
            cell.set_facecolor(LIGHT)
        if row > 0 and col == 7:
            cell.get_text().set_color(GREEN if data[row-1][7] == "PASS" else AMBER)
            cell.get_text().set_weight("bold")
    ax.text(0, -0.02, "Evidence: DATABASE structures + COMPUTED normalization. Parse success does not confirm an authentic laboratory standard.", transform=ax.transAxes, fontsize=9, color=MUTED)
    _save(fig, root / "figures/evidence/compound_structure_audit.svg")


def provenance_matrix(root: Path) -> None:
    rows = [
        ("Pathway identifiers and reaction edges", "DATABASE", "Nature Communications 2026"),
        ("Molecular structures", "DATABASE", "PubChem cached records"),
        ("Structure QC and descriptors", "COMPUTED", "RDKit"),
        ("Human toxicity screening", "MISSING", "ADMETlab/ProTox exports required"),
        ("Environmental fate", "MISSING", "CompTox export required"),
        ("Aquatic ecotoxicity", "MISSING", "ECOSAR export required"),
        ("Matched production benchmark", "MISSING", "G1 versus LLPS wet-lab data required"),
        ("Resource, energy and cost", "MISSING", "batch inventories required"),
        ("Containment", "MISSING", "CFU before/after required"),
        ("Functional unit", "SCENARIO", "working value: 1 g purified glabridin"),
    ]
    colors = {"DATABASE": "#366D96", "COMPUTED": PURPLE, "MISSING": "#D6CDD9", "SCENARIO": AMBER}
    fig, ax = plt.subplots(figsize=(11, 6.1)); ax.axis("off")
    ax.set_title("Evidence provenance and current availability", loc="left", fontsize=18, weight="bold", color=INK, pad=15)
    y = .89
    for label, state, source in rows:
        ax.add_patch(FancyBboxPatch((.01, y-.045), .97, .07, boxstyle="round,pad=0.008,rounding_size=.012", facecolor="white", edgecolor=LINE))
        ax.text(.035, y, label, va="center", fontsize=10, color=INK, weight="bold")
        ax.text(.56, y, state, va="center", fontsize=9, color="white" if state != "MISSING" else MUTED, weight="bold", bbox=dict(boxstyle="round,pad=.32", facecolor=colors[state], edgecolor="none"))
        ax.text(.72, y, source, va="center", fontsize=9, color=MUTED)
        y -= .082
    ax.text(.01, .01, "Missing evidence remains missing; the pipeline does not convert unavailable values to zero.", fontsize=9, color=MUTED)
    _save(fig, root / "figures/framework/evidence_provenance_matrix.svg")


def stakeholder_flow(root: Path) -> None:
    rows = _rows(root / "data/stakeholder_intervention_log.csv")
    fig, ax = plt.subplots(figsize=(12, 6)); ax.axis("off")
    ax.set_title("Stakeholder concern to project intervention", loc="left", fontsize=18, weight="bold", color=INK, pad=16)
    headers = ["Stakeholder", "Concern", "Metric", "Project change", "Validation"]
    xs = [.01, .18, .42, .62, .84]; widths = [.15,.21,.18,.20,.15]
    for x, w, h in zip(xs, widths, headers):
        ax.text(x+w/2, .90, h, ha="center", va="center", fontsize=10, weight="bold", color="white", bbox=dict(boxstyle="round,pad=.42", facecolor=PURPLE, edgecolor="none"))
    y=.76
    for r in rows:
        values=[r["stakeholder"],r["concern"],r["metric"],r["design_change"],r["validation"]]
        for x,w,val in zip(xs,widths,values):
            ax.add_patch(FancyBboxPatch((x,y-.055),w,.115,boxstyle="round,pad=.008,rounding_size=.012",facecolor="white",edgecolor=LINE))
            ax.text(x+.008,y, val if len(val)<72 else val[:69]+"...", va="center", fontsize=8.1, color=INK, wrap=True)
        for i in range(4):
            ax.annotate("", xy=(xs[i+1]-.004,y), xytext=(xs[i]+widths[i]+.004,y), arrowprops=dict(arrowstyle="->",color=PURPLE,lw=1.4))
        y-=.17
    ax.text(.01,.02,"Round 2 and sustainability/process expert validation remain outstanding.",fontsize=9,color=RED,weight="bold")
    _save(fig, root / "figures/framework/stakeholder_intervention_flow.svg")


def tradeoff_matrix(root: Path) -> None:
    data = [
        ["LLPS may improve pathway control", "Construct complexity and reproducibility", "No matched result yet", "Freeze Construct IDs and quantify expression", "Run G1 vs LLPS with n>=3"],
        ["Microbial production may reduce plant extraction", "GMO waste and release risk", "Containment data missing", "Validated inactivation and waste handling", "Measure CFU before and after"],
        ["Higher product concentration may reduce upstream intensity", "Extraction solvent burden can remain", "Inventory missing", "Track solvent and recovery per batch", "Report solvent per functional unit"],
        ["Responds to stakeholder-defined skin needs", "Efficacy or safety overclaim", "Qualitative stakeholder evidence", "Use evidence-level language", "Return measured evidence to stakeholders"],
        ["Lab-scale productivity may improve", "Scale-up benefit may not persist", "Scale-up data missing", "Sensitivity and scenario analysis", "Define a documented scale-up case"],
    ]
    headers=["Potential benefit","Potential negative burden","Current evidence","Mitigation","Next iteration"]
    fig,ax=plt.subplots(figsize=(14,6.4)); ax.axis("off"); ax.set_title("Positive and negative impact matrix",loc="left",fontsize=18,weight="bold",color=INK,pad=16)
    table=ax.table(cellText=data,colLabels=headers,loc="center",cellLoc="left",colWidths=[.20,.21,.18,.20,.20])
    table.auto_set_font_size(False); table.set_fontsize(8.5); table.scale(1,2.2)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor(LINE); cell.PAD=.06
        if r==0: cell.set_facecolor(PURPLE); cell.get_text().set_color("white"); cell.get_text().set_weight("bold")
        elif r%2==0: cell.set_facecolor(LIGHT)
    ax.text(0,-.01,"Framework evidence only. No benefit is claimed as measured until matched experiments and inventories are supplied.",transform=ax.transAxes,fontsize=9,color=MUTED)
    _save(fig,root/"figures/framework/positive_negative_mitigation_matrix.svg")


def integrated_dashboard(root: Path) -> None:
    panels=[("Environmental",[("Structures","available",GREEN),("Toxicity/fate","missing",RED),("Resource inventory","missing",RED),("Containment","missing",RED)]),("Economic",[("Productivity","missing",RED),("Recovery/purity","missing",RED),("Cost per g","missing",RED),("Sensitivity","waiting",AMBER)]),("Social",[("Round 1 concerns","partial",AMBER),("Evidence transparency","implemented",GREEN),("Safety evidence","missing",RED),("Round 2 validation","missing",RED)])]
    fig,ax=plt.subplots(figsize=(11.5,5)); ax.axis("off"); ax.set_title("Integrated impact evidence status",loc="left",fontsize=18,weight="bold",color=INK,pad=16)
    for j,(title,items) in enumerate(panels):
        x=.02+j*.33
        ax.add_patch(FancyBboxPatch((x,.12),.30,.72,boxstyle="round,pad=.012,rounding_size=.02",facecolor="white",edgecolor=LINE,lw=1.5))
        ax.text(x+.02,.77,title,fontsize=14,weight="bold",color=PURPLE)
        y=.64
        for label,state,color in items:
            ax.text(x+.025,y,label,fontsize=10,color=INK,va="center")
            ax.text(x+.275,y,state.upper(),fontsize=8,color=color,weight="bold",ha="right",va="center")
            y-=.125
    ax.text(.02,.03,"Environmental, economic and social evidence are reported separately; no composite sustainability score is calculated.",fontsize=9,color=MUTED)
    _save(fig,root/"figures/framework/integrated_impact_dashboard.svg")


def sdg_map(root: Path) -> None:
    fig,ax=plt.subplots(figsize=(12,5)); ax.axis("off"); ax.set_title("SDG evidence map",loc="left",fontsize=18,weight="bold",color=INK,pad=16)
    sdgs=[(.04,"SDG 3","Why production matters","Stakeholder-defined skin-health needs","Round 2 and safety evidence missing","#4C9F38"),(.37,"SDG 12","How to reduce burden","Yield, PMI, water, solvent, waste, energy","Matched measurements missing","#BF8B2E"),(.70,"SDG 9","Can it become a process","Productivity, purity, recovery, batch CV, cost/g","Process and cost data missing","#FD6925")]
    for x,sdg,q,metric,gap,color in sdgs:
        ax.add_patch(FancyBboxPatch((x,.25),.27,.55,boxstyle="round,pad=.015,rounding_size=.025",facecolor="white",edgecolor=color,lw=2.4))
        ax.text(x+.02,.71,sdg,fontsize=16,weight="bold",color=color)
        ax.text(x+.02,.60,q,fontsize=10,weight="bold",color=INK)
        ax.text(x+.02,.49,"Metric",fontsize=8,weight="bold",color=MUTED)
        ax.text(x+.02,.42,metric,fontsize=9,color=INK,wrap=True)
        ax.text(x+.02,.32,"GAP: "+gap,fontsize=8.4,color=RED,wrap=True)
    ax.annotate("",xy=(.36,.53),xytext=(.32,.53),arrowprops=dict(arrowstyle="->",color=PURPLE,lw=2)); ax.annotate("",xy=(.69,.53),xytext=(.65,.53),arrowprops=dict(arrowstyle="->",color=PURPLE,lw=2))
    ax.text(.04,.10,"The map links SDGs to metrics and evidence gaps. It does not claim completed impact.",fontsize=9,color=MUTED)
    _save(fig,root/"figures/framework/sdg_evidence_map.svg")


def run(root: Path) -> None:
    structure_audit(root)
    provenance_matrix(root)
    stakeholder_flow(root)
    tradeoff_matrix(root)
    integrated_dashboard(root)
    sdg_map(root)


#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""))


def csv_rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def table(rows: list[dict[str, str]], columns: list[tuple[str, str]]) -> str:
    out = ['<div class="table-wrap"><table><thead><tr>']
    out.extend(f"<th>{esc(label)}</th>" for _, label in columns)
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        out.extend(f"<td>{esc(row.get(key, ''))}</td>" for key, _ in columns)
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def build() -> Path:
    structures = csv_rows("results/tables/compound_structure_audit.csv")
    models = csv_rows("results/tables/model_run_inventory.csv")
    stakeholder = csv_rows("data/stakeholder_intervention_log.csv")
    structure_table = table(structures, [
        ("compound_id", "Compound ID"), ("compound_name", "Name"), ("computed_molecular_formula", "Formula"),
        ("computed_molecular_weight", "RDKit MW"), ("computed_inchikey", "InChIKey"), ("audit_status", "Audit"),
    ])
    model_table = table(models, [("model", "Model/database"), ("status", "Status"), ("records", "Records"), ("reason", "Reason")])
    stakeholder_table = table(stakeholder, [("stakeholder", "Stakeholder"), ("concern", "Concern"), ("metric", "Metric"), ("design_change", "Project change"), ("validation", "Validation")])

    body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="GALATEA evidence-based sustainable development analysis"><title>GALATEA Sustainable Development Impact</title><link rel="stylesheet" href="assets/styles.css"></head><body>
<div class="draft"><b>EVIDENCE STATUS MATTERS.</b> Model predictions and missing measurements are explicitly distinguished.</div>
<header class="hero"><div class="wrap"><div class="eyebrow">Tsinghua-T iGEM 2026 · GALATEA</div><h1>Sustainable Development Impact</h1><p>Can programmable microbial production improve glabridin manufacturing efficiency while avoiding new resource, environmental, safety and social burdens?</p><div class="sdgs"><span class="sdg-pill">SDG 3 · Responsible purpose</span><span class="sdg-pill">SDG 12 · Primary quantitative focus</span><span class="sdg-pill">SDG 9 · Manufacturing feasibility</span></div></div></header>
<div class="layout"><aside class="sidebar"><b>Evidence pathway</b><a href="#challenge">Challenge and baseline</a><a href="#stakeholders">Stakeholder intervention</a><a href="#structures">Molecular structure QC</a><a href="#screening">Model screening</a><a href="#benchmark">Wet-lab benchmark</a><a href="#resources">Resource and energy</a><a href="#trade-offs">Trade-offs</a><a href="#integrated-impact">Integrated impact</a><a href="#toolkit">Reproducible toolkit</a></aside><main>
<section class="section" id="challenge"><div class="kicker">01 Challenge and baseline</div><h2>The primary comparison is matched No-LLPS versus LLPS</h2><p class="lead">The analysis uses G1, low-expression OC/DMT without LLPS, as the baseline and the same OC/DMT background with LLPS as the main comparison. Host, medium, initial OD600, precursor concentration, temperature, RPM and fermentation conditions must be matched. Normal-expression constructs are references; optimization constructs do not replace the primary comparison.</p><div class="note"><b>Current status:</b> the comparison is defined, but no matched measurements are present. All process-light variables were removed because the current design no longer uses light control.</div><figure class="figure"><img src="figures/framework/sdg_evidence_map.svg" alt="SDG evidence map"><figcaption>SDG 3 defines responsible purpose, SDG 12 carries the main quantitative claim, and SDG 9 tests process feasibility.</figcaption></figure></section>
<section class="section" id="stakeholders"><div class="kicker">02 Stakeholder evidence</div><h2>Concerns are linked to metrics and project changes</h2><p class="lead">The intervention log separates documented concerns from planned validation. No stakeholder quotation is included without a traceable source.</p><figure class="figure"><img src="figures/framework/stakeholder_intervention_flow.svg" alt="Stakeholder intervention flow"><figcaption>Round 2 and a dedicated sustainability/process expert remain outstanding.</figcaption></figure>{stakeholder_table}</section>
<section class="section" id="structures"><div class="kicker">03 Molecular structure QC</div><h2>Six pathway structures are traceable and machine-validated</h2><p class="lead">Compounds 9, 10, 11, 13, 14 and 15 were mapped to the 2026 pathway article, cached from PubChem and re-parsed with RDKit. Formula, molecular weight and InChIKey are checked independently. This does not replace authentic analytical standards.</p><figure class="figure"><img src="figures/evidence/compound_structure_audit.svg" alt="Compound structure audit"><figcaption>DATABASE structures with COMPUTED normalization. Exact records and audit fields are downloadable below.</figcaption></figure>{structure_table}</section>
<section class="section" id="screening"><div class="kicker">04 Molecular safety and environmental screening</div><h2>ADMETlab 3.0 was run on all six confirmed structures</h2><p class="lead">The official ADMETlab web batch model completed successfully for 6/6 molecules and returned 122 columns of molecular and ADMET outputs. The unmodified CSV, run metadata and a selected long-format table are retained. ProTox, CompTox and ECOSAR remain unavailable, so these are single-model screening predictions rather than consensus safety conclusions.</p>{model_table}<div class="note warning"><b>Interpretation boundary:</b> a high positive-class probability is a prioritization signal, not measured toxicity. The official web CSV did not expose uncertainty fields, so no uncertainty figure is claimed.</div><figure class="figure"><img src="figures/evidence/toxicity_prediction_probability.svg" alt="ADMETlab toxicity prediction probability heatmap"><figcaption>Actual ADMETlab 3.0 positive-class probabilities for ten toxicity endpoints. Every cell displays the exported numerical value.</figcaption></figure><figure class="figure"><img src="figures/evidence/environmental_model_outputs.svg" alt="ADMETlab environmental model outputs"><figcaption>Actual exported logP, logS, BCF-model and aquatic ecotoxicity outputs, shown without combining incompatible model scales.</figcaption></figure><figure class="figure"><img src="figures/evidence/predicted_chemical_property_landscape.svg" alt="Predicted chemical property landscape"><figcaption>Actual model outputs: logP versus logS, colored by the exported BCF model output and sized by molecular weight.</figcaption></figure></section>
<section class="section" id="benchmark"><div class="kicker">05 Wet-lab benchmark</div><h2>Production impact is waiting for biological replicates</h2><p class="lead">Required measurements include raw biological replicates for OD600, compounds 9/10/11/13/14/15, precursor consumption, glabridin titer, purity and recovery. The primary result must show raw points, summary estimates, uncertainty and the stated statistical method.</p><div class="grid2"><article class="card"><span class="status missing">WAITING FOR DATA</span><h3>Titer yield and productivity</h3><p>No G1 versus LLPS measurements are present.</p></article><article class="card"><span class="status missing">WAITING FOR DATA</span><h3>Metabolite time course</h3><p>The repository provides the exact input template, including compound 13 and OD600.</p></article><article class="card"><span class="status missing">WAITING FOR DATA</span><h3>Gaussian process fit</h3><p>Fitting is disabled until real replicate time series are supplied.</p></article><article class="card"><span class="status missing">WAITING FOR DATA</span><h3>Containment</h3><p>CFU before and after approved inactivation is required.</p></article></div></section>
<section class="section" id="resources"><div class="kicker">06 Resource energy and cost</div><h2>Templates follow the working functional unit</h2><p class="lead">The working functional unit is 1 g purified glabridin. Templates capture actual materials, water, solvents, equipment time, power provenance, recovery, purity and price. No PMI, energy intensity or cost result is reported before product mass and batch inventories exist.</p><div class="note"><b>Accounting rule:</b> OD-normalized substrate uptake remains a proxy until a strain-specific OD600-to-dry-cell-weight calibration is available. Nameplate power and measured power are reported separately.</div></section>
<section class="section" id="trade-offs"><div class="kicker">07 Positive and negative interactions</div><h2>Potential benefits are paired with burdens and mitigation</h2><figure class="figure"><img src="figures/framework/positive_negative_mitigation_matrix.svg" alt="Positive and negative impact matrix"><figcaption>The matrix distinguishes potential benefits from measured effects and identifies the next evidence needed.</figcaption></figure></section>
<section class="section" id="integrated-impact"><div class="kicker">08 Integrated impact</div><h2>Environmental economic and social evidence remain separate</h2><figure class="figure"><img src="figures/framework/integrated_impact_dashboard.svg" alt="Integrated impact evidence status"><figcaption>No arbitrary composite sustainability score is calculated.</figcaption></figure></section>
<section class="section" id="toolkit"><div class="kicker">09 Reproducible toolkit</div><h2>One command rebuilds the current evidence package</h2><pre><code>python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python analysis/run_all.py</code></pre><p>The command validates structures, loads cached model outputs, updates evidence tables, regenerates figures, rebuilds this site and checks local links. It does not call external model services by default.</p><div class="downloads"><a href="results/tables/compound_structure_audit.csv">Structure audit CSV</a><a href="results/tables/model_run_inventory.csv">Model inventory CSV</a><a href="results/tables/admetlab_selected_predictions.csv">Selected ADMETlab predictions</a><a href="data/raw/admetlab/admetlab_predictions.csv">Raw ADMETlab CSV</a><a href="data/raw/admetlab/run_metadata.json">ADMETlab run metadata</a><a href="docs/methodology/COMPUTATIONAL_SUSTAINABILITY.md">Methodology</a><a href="docs/provenance/MODEL_PROVENANCE.md">Model provenance</a><a href="docs/limitations/CURRENT_LIMITATIONS.md">Limitations</a></div></section>
</main></div><footer><b>GALATEA Sustainable Development Impact</b><br>All displayed evidence is traceable to repository data and code. Missing results remain explicitly missing.</footer></body></html>'''
    index = ROOT / "index.html"
    index.write_text(body, encoding="utf-8")
    return index


def export_wiki() -> Path:
    destination = ROOT / "wiki_export"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "index.html", destination / "index.html")
    for directory in ["assets", "figures/evidence", "figures/framework"]:
        shutil.copytree(ROOT / directory, destination / directory, dirs_exist_ok=True)
    for directory in ["results/tables", "data/raw/admetlab", "docs/methodology", "docs/provenance", "docs/limitations"]:
        shutil.copytree(ROOT / directory, destination / directory, dirs_exist_ok=True)
    (destination / ".nojekyll").touch()
    return destination


if __name__ == "__main__":
    build()
    export_wiki()

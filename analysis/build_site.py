#!/usr/bin/env python3
from pathlib import Path
import csv, html

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
FIG=ROOT/'figures'
FIG.mkdir(exist_ok=True)

def rows(name):
    with open(DATA/name,encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

def esc(x): return html.escape(str(x or ''))

def text_lines(x,y,lines,cls='small muted',step=17):
    out=[f'<text x="{x}" y="{y}" class="{cls}">']
    for i,line in enumerate(lines):
        dy=0 if i==0 else step
        out.append(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
    out.append('</text>')
    return ''.join(out)

def svg_header(w,h,title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}"><style>
    text{{font-family:Arial,Helvetica,sans-serif;fill:#21182b}} .muted{{fill:#6e6576}} .white{{fill:#fff}} .bold{{font-weight:700}} .small{{font-size:13px}} .med{{font-size:16px}} .big{{font-size:22px;font-weight:700}}
    </style>'''

def make_stakeholder_svg():
    s=svg_header(1080,520,'Stakeholder to metric map')
    s+='<rect width="1080" height="520" rx="24" fill="#fbf9fd"/><text x="40" y="48" class="big">Stakeholder → Concern → Metric → Project response</text>'
    items=[
      ('Consumers / NUS','#4c9f38',['Skin-health needs','efficacy · safety · price','process control · transparency'],['Purity · safety · efficacy','cost/g · stability','evidence provenance'],['Reframe application','expand success criteria']),
      ('Industry','#fd6925',['Purity · safety · efficacy','cost · supply stability','complete data package'],['Purity · recovery · productivity','cost/g · batch CV','safety evidence'],['Add quality + economics','add reproducibility evidence']),
      ('Academic / technical','#6f3ca7',['Matched controls','LLPS mechanism','pathway interpretation'],['LLPS evidence · time series','DMT activity 9/10/11','model uncertainty'],['Keep mechanism separate','use it to explain outcomes']),
      ('Sustainability / process','#366d96',['Boundary · functional unit','resource metrics','practical significance'],['PMI · water · solvent','waste · process energy','limitation review'],['Still to add expert review','Round 2 validation'])]
    y=84
    for name,c,conc,metric,response in items:
        s+=f'<rect x="36" y="{y}" width="205" height="88" rx="15" fill="{c}" opacity=".95"/><text x="52" y="{y+36}" class="white med bold">{esc(name)}</text>'
        s+=f'<rect x="270" y="{y}" width="255" height="88" rx="15" fill="#fff" stroke="#ded4e7"/><text x="286" y="{y+24}" class="small bold">Concern</text>'+text_lines(286,y+43,conc,'small muted',15)
        s+=f'<rect x="554" y="{y}" width="225" height="88" rx="15" fill="#fff" stroke="#ded4e7"/><text x="570" y="{y+24}" class="small bold">Metric / evidence</text>'+text_lines(570,y+43,metric,'small muted',15)
        s+=f'<rect x="808" y="{y}" width="236" height="88" rx="15" fill="#f2ebf8" stroke="#cdb9de"/><text x="824" y="{y+24}" class="small bold">Project response</text>'+text_lines(824,y+45,response,'small muted',16)
        for x1,x2 in [(241,270),(525,554),(779,808)]:
            s+=f'<path d="M{x1} {y+44} L{x2-7} {y+44}" stroke="#8b5bb8" stroke-width="3"/><path d="M{x2-12} {y+39} L{x2-5} {y+44} L{x2-12} {y+49}" fill="none" stroke="#8b5bb8" stroke-width="3"/>'
        y+=105
    s+='</svg>'
    (FIG/'stakeholder_metric.svg').write_text(s,encoding='utf-8')

def make_sdg_svg():
    s=svg_header(1080,390,'SDG 3, 12 and 9 mapping')
    s+='<rect width="1080" height="390" rx="24" fill="#fbf9fd"/><text x="40" y="48" class="big">One coherent sustainability story</text>'
    cols=[(45,'#4c9f38','SDG 3','WHY it should matter',['Real skin-health needs'],['Safety · efficacy','product evidence']),(388,'#bf8b2e','SDG 12','HOW to produce responsibly',['Lower burden per unit product'],['Substrate · PMI · water','solvent · waste · energy']),(731,'#fd6925','SDG 9','CAN it become a real process?',['Reliable biomanufacturing'],['Productivity · purity · recovery','batch CV · cost'])]
    for x,c,sdg,q,a,m in cols:
        s+=f'<rect x="{x}" y="90" width="300" height="220" rx="22" fill="#fff" stroke="{c}" stroke-width="3"/><rect x="{x}" y="90" width="300" height="55" rx="20" fill="{c}"/><text x="{x+22}" y="126" class="white big">{sdg}</text>'
        s+=f'<text x="{x+22}" y="180" class="med bold">{esc(q)}</text>'+text_lines(x+22,210,a,'small muted',16)+f'<text x="{x+22}" y="250" class="small bold">Evidence</text>'+text_lines(x+22,270,m,'small muted',16)
    s+='<path d="M345 200 L375 200" stroke="#8b5bb8" stroke-width="4"/><path d="M370 194 L380 200 L370 206" fill="none" stroke="#8b5bb8" stroke-width="4"/><path d="M688 200 L718 200" stroke="#8b5bb8" stroke-width="4"/><path d="M713 194 L723 200 L713 206" fill="none" stroke="#8b5bb8" stroke-width="4"/><text x="40" y="352" class="small muted">SDG 3 defines purpose; SDG 12 evaluates per-product resource burden; SDG 9 tests industrial plausibility.</text></svg>'
    (FIG/'sdg_map.svg').write_text(s,encoding='utf-8')

def make_boundary_svg():
    s=svg_header(1080,450,'System boundary')
    s+='<rect width="1080" height="450" rx="24" fill="#fbf9fd"/><text x="40" y="48" class="big">Recommended core system boundary</text>'
    s+='<rect x="35" y="86" width="230" height="280" rx="18" fill="#f3f0f5" stroke="#cfc6d6" stroke-dasharray="7 7"/><text x="55" y="118" class="med bold">R&amp;D / construction</text><text x="55" y="145" class="small muted">Outside core comparison</text>'
    items=['Plasmid design / PCR','Gel / Gibson','E. coli transformation','Sequencing / plasmid prep','Yeast transformation']
    yy=180
    for it in items:
        s+=f'<rect x="55" y="{yy}" width="190" height="34" rx="9" fill="#fff" stroke="#ded4e7"/><text x="68" y="{yy+22}" class="small">{esc(it)}</text>'; yy+=42
    s+='<rect x="300" y="86" width="740" height="280" rx="18" fill="#f7f2fb" stroke="#6f3ca7" stroke-width="3"/><text x="320" y="118" class="med bold">Core production boundary: engineered yeast inoculum → analyzed / purified product</text>'
    stages=[('Seed / expansion',['medium · time · OD']),('Induction / expression',['galactose if applicable']),('Fermentation',['precursor · OD · time series']),('Harvest / extraction',['centrifuge · water','ethyl acetate']),('Concentration / analysis',['sonication · rotavap','methanol · chromatography'])]
    x=325
    for i,(a,b) in enumerate(stages):
        w=130 if i<4 else 160
        s+=f'<rect x="{x}" y="170" width="{w}" height="110" rx="14" fill="#fff" stroke="#cbb7dc"/><text x="{x+12}" y="195" class="small bold">{esc(a)}</text>'+text_lines(x+12,220,b,'small muted',16)
        if i<4:
            s+=f'<path d="M{x+w} 225 L{x+w+20} 225" stroke="#8b5bb8" stroke-width="3"/><path d="M{x+w+15} 220 L{x+w+22} 225 L{x+w+15} 230" fill="none" stroke="#8b5bb8" stroke-width="3"/>'
        x += w+24
    s+='<text x="320" y="322" class="small muted">Working functional unit: per 1 g purified glabridin (review with a sustainability/process stakeholder).</text><text x="40" y="410" class="small muted">Use an extended R&amp;D boundary only as a separate scenario; do not charge one-time construction to every batch by default.</text></svg>'
    (FIG/'system_boundary.svg').write_text(s,encoding='utf-8')

def make_process_svg():
    s=svg_header(1080,350,'Protocol to process inventory')
    s+='<rect width="1080" height="350" rx="24" fill="#fbf9fd"/><text x="40" y="48" class="big">Protocol → recurring production inventory</text>'
    stages=[('1','Expansion',['Culture medium','actual volume / time / RPM']),('2','Induction',['Galactose if applicable','actual amount']),('3','Fermentation',['Precursor + OD600','Day 1/3/5/7/10']),('4','Harvest',['Centrifuge','volume + use time']),('5','Extraction',['Water + ethyl acetate','sonication']),('6','Analysis',['Rotavap + methanol','chromatography / purity'])]
    x=35
    for i,(n,a,b) in enumerate(stages):
        w=150
        s+=f'<circle cx="{x+25}" cy="113" r="21" fill="#6f3ca7"/><text x="{x+19}" y="119" class="white med bold">{n}</text><rect x="{x}" y="145" width="{w}" height="120" rx="14" fill="#fff" stroke="#ded4e7"/><text x="{x+14}" y="173" class="med bold">{a}</text>'+text_lines(x+14,198,b,'small muted',17)
        if i<5:
            s+=f'<path d="M{x+w} 205 L{x+w+22} 205" stroke="#8b5bb8" stroke-width="3"/><path d="M{x+w+17} 200 L{x+w+24} 205 L{x+w+17} 210" fill="none" stroke="#8b5bb8" stroke-width="3"/>'
        x+=174
    s+='<text x="40" y="312" class="small muted">Protocol defines the stages; accounting still needs actual per-batch quantities, sampling volumes, use time and rated power.</text></svg>'
    (FIG/'process_inventory.svg').write_text(s,encoding='utf-8')

def make_gap_svg():
    rs=rows('wetlab_gap_audit.csv')
    counts={k:sum(1 for r in rs if r['priority']==k) for k in ['Critical','High','Not applicable']}
    total=len(rs); usable=total-counts['Not applicable']
    s=svg_header(1080,420,'Wet lab data gap audit')
    s+='<rect width="1080" height="420" rx="24" fill="#fbf9fd"/><text x="40" y="48" class="big">Wet-lab data gap audit</text><text x="40" y="76" class="small muted">Current audit counts fields needed for sustainability/traceability; it is not a score of scientific quality.</text>'
    # bar
    x=40;y=110;W=1000;H=44
    crit=W*counts['Critical']/total; high=W*counts['High']/total; na=W*counts['Not applicable']/total
    s+=f'<rect x="{x}" y="{y}" width="{crit:.1f}" height="{H}" rx="10" fill="#9a4650"/><rect x="{x+crit:.1f}" y="{y}" width="{high:.1f}" height="{H}" fill="#d4942f"/><rect x="{x+crit+high:.1f}" y="{y}" width="{na:.1f}" height="{H}" rx="10" fill="#b7b0bc"/>'
    s+=f'<text x="55" y="139" class="white med bold">Critical {counts["Critical"]}</text><text x="{x+crit+18:.1f}" y="139" class="white med bold">High {counts["High"]}</text><text x="{x+crit+high+6:.1f}" y="139" class="small bold">N/A {counts["Not applicable"]}</text>'
    gaps=[('OD600 time points','critical','separate biomass growth from pathway efficiency'),('Initial + residual precursor','critical','substrate consumption and Yield'),('Metabolite 14','critical','important demethylation product'),('Glabridin time series','critical','Titer / Productivity'),('Actual material inventory','critical','PMI / water / solvent / cost'),('Biological replicates + standards','critical','statistics and reproducibility'),('DMT activity 9/10/11','high','explain substrate preference'),('Safety / containment','high','negative-impact mitigation')]
    s+='<text x="40" y="194" class="med bold">Highest-value gaps to close next</text>'
    yy=220
    for i,(a,p,b) in enumerate(gaps):
        col1=40 if i<4 else 550; row=i if i<4 else i-4; y0=220+row*42
        color='#9a4650' if p=='critical' else '#d4942f'
        desc_x=(col1+215 if col1<500 else col1+280)
        s+=f'<circle cx="{col1+8}" cy="{y0+10}" r="7" fill="{color}"/><text x="{col1+24}" y="{y0+15}" class="small bold">{esc(a)}</text><text x="{desc_x}" y="{y0+15}" class="small muted">{esc(b)}</text>'
    s+='<text x="40" y="397" class="small muted">Process-light fields are intentionally removed because the current production system no longer uses light control.</text></svg>'
    (FIG/'wetlab_gap_audit.svg').write_text(s,encoding='utf-8')

def table(records, columns):
    out=['<div class="table-wrap"><table><thead><tr>']
    for key,label in columns: out.append(f'<th>{esc(label)}</th>')
    out.append('</tr></thead><tbody>')
    for r in records:
        out.append('<tr>')
        for key,label in columns: out.append(f'<td>{esc(r.get(key,""))}</td>')
        out.append('</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def build_html():
    sm=rows('stakeholder_metric.csv'); sdg=rows('sdg_mapping.csv'); proc=rows('process_inventory.csv'); gap=rows('wetlab_gap_audit.csv')
    critical=sum(1 for r in gap if r['priority']=='Critical'); high=sum(1 for r in gap if r['priority']=='High')
    html_text=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><meta name="description" content="GALATEA Sustainable Development Impact working analysis"/><title>GALATEA · Sustainable Development Impact</title><link rel="stylesheet" href="assets/styles.css"/></head><body>
<div class="draft"><b>INTERNAL WORKING ANALYSIS.</b> Verify claims, references, stakeholder quotations and experimental results before copying to the official iGEM Wiki.</div>
<header class="hero"><div class="wrap"><div class="eyebrow">Tsinghua-T iGEM 2026 · GALATEA</div><h1>From More Product to Better Production</h1><p>This working page turns the current Human Practices, wet-lab protocol and sustainability planning into five judge-facing analyses that can already be completed before final experimental results arrive.</p><div class="sdgs"><span class="sdg-pill">SDG 3 · Good Health and Well-being</span><span class="sdg-pill">SDG 12 · Responsible Consumption and Production</span><span class="sdg-pill">SDG 9 · Industry, Innovation and Infrastructure</span></div></div></header>
<div class="layout"><aside class="sidebar"><b>Current analyses</b><a href="#rubric">Handbook map</a><a href="#stakeholder">Stakeholder → Metric</a><a href="#sdg">SDG 3 / 12 / 9</a><a href="#inventory">Protocol → Process inventory</a><a href="#boundary">System boundary</a><a href="#gap">Wet-lab data gap audit</a><a href="#next">What can be analyzed next?</a><a href="#downloads">Download data</a></aside><main>
<section class="section" id="rubric"><div class="kicker">Judge-first design</div><h2>How the current work maps to the handbook</h2><p class="lead">The 2026 Sustainable Development Impact rubric asks whether stakeholder feedback entered the work, whether social/environmental/economic impacts were addressed, whether positive and negative SDG interactions were considered, whether the work is reusable, and whether at least one SDG was addressed measurably and significantly.</p><div class="judging"><div class="q">Q1</div><div>Stakeholder feedback changed the project</div><div class="loc">Stakeholder → Metric</div><div class="q">Q2</div><div>Long-term social, environmental and economic impacts</div><div class="loc">SDG map + process analysis</div><div class="q">Q3</div><div>Positive / negative SDG interactions</div><div class="loc">Risk register to complete</div><div class="q">Q4</div><div>Reusable documentation and methods</div><div class="loc">CSV + build script</div><div class="q">Q5</div><div>Measurable and significant SDG impact</div><div class="loc">Needs wet-lab data + Round 2</div></div></section>
<section class="section" id="stakeholder"><div class="kicker">Analysis 1 · Q1</div><h2>Stakeholder → Metric analysis</h2><p class="lead">Existing stakeholder material already supports a structured intervention map. The key analytical move is to convert concerns into metrics and project changes rather than present interviews as stand-alone narratives.</p><figure class="figure"><img src="figures/stakeholder_metric.svg" alt="Stakeholder to metric map"/><figcaption>Current map: consumer, industry and academic concerns are documented; a dedicated sustainability/process stakeholder remains a gap.</figcaption></figure>{table(sm,[('stakeholder','Stakeholder'),('documented_concern','Documented concern'),('metric_or_evidence','Metric / evidence'),('project_response','Project response'),('current_status','Status')])}<p class="source-note">Internal sources used: NUS student interviews; GALATEA HP Storyline v4; previous Sustainable Development planning.</p></section>
<section class="section" id="sdg"><div class="kicker">Analysis 2 · Q2/Q3</div><h2>SDG 3 / 12 / 9 correspondence</h2><p class="lead">The strongest structure is not three disconnected SDG labels. SDG 3 defines responsible purpose, SDG 12 evaluates resource burden per unit product, and SDG 9 asks whether the improvement can become a reliable manufacturing process.</p><figure class="figure"><img src="figures/sdg_map.svg" alt="SDG 3 12 9 map"/><figcaption>This relationship keeps social, environmental and economic dimensions connected while preserving evidence boundaries.</figcaption></figure>{table(sdg,[('sdg','SDG'),('core_question','Core question'),('current_evidence','Current evidence'),('planned_metrics','Planned metrics'),('key_risk','Key risk'),('current_readiness','Readiness')])}</section>
<section class="section" id="inventory"><div class="kicker">Analysis 3 · SDG 12</div><h2>Protocol → Process inventory</h2><p class="lead">The current protocol is already enough to define the recurring production stages and the materials/equipment that must be logged. The remaining gap is actual batch-level quantities rather than stage identification.</p><figure class="figure"><img src="figures/process_inventory.svg" alt="Protocol to process inventory"/><figcaption>The protocol defines culture, induction, fermentation, extraction and analysis; actual resource quantities and equipment use must be recorded per batch.</figcaption></figure>{table(proc,[('boundary','Boundary'),('stage','Stage'),('input_or_operation','Input / operation'),('protocol_information','What the protocol already tells us'),('what_to_record','What to record now'),('status','Status')])}<div class="note"><b>Important update:</b> the current production system no longer uses process light control, so LED wavelength / irradiance / duty-cycle accounting is removed from the sustainability inventory.</div></section>
<section class="section" id="boundary"><div class="kicker">Analysis 4 · Accounting logic</div><h2>System boundary</h2><p class="lead">For the main No-LLPS vs LLPS comparison, use a recurring production boundary that starts from an engineered yeast inoculum and ends at analyzed/purified product. Keep one-time strain construction outside the core boundary unless it is reported separately as an extended R&amp;D scenario.</p><figure class="figure"><img src="figures/system_boundary.svg" alt="System boundary diagram"/><figcaption>Working system boundary. The proposed functional unit is per 1 g purified glabridin; this should be reviewed with a sustainability/process stakeholder before final submission.</figcaption></figure><div class="grid"><div class="card"><span class="status ready">IN SCOPE</span><h3>Recurring production</h3><p>Seed/expansion, induction where applicable, precursor fermentation, harvest, extraction, concentration and product analysis/purification.</p></div><div class="card"><span class="status info">OUTSIDE CORE</span><h3>One-time R&amp;D</h3><p>PCR, gel, Gibson, E. coli transformation, sequencing, plasmid preparation and yeast transformation.</p></div><div class="card"><span class="status partial">TO REVIEW</span><h3>Functional unit</h3><p>Working recommendation: per 1 g purified glabridin. A different unit can be retained if purification is not yet sufficiently defined, but the choice must be explicit.</p></div></div></section>
<section class="section" id="gap"><div class="kicker">Analysis 5 · Data readiness</div><h2>Wet-lab data gap audit</h2><p class="lead">The audit identifies {critical} critical data fields, {high} high-priority fields and one obsolete light-control field. These counts describe analysis readiness, not experimental quality.</p><figure class="figure"><img src="figures/wetlab_gap_audit.svg" alt="Wet lab data gap audit"/><figcaption>The most urgent gaps are OD600, residual precursor, glabridin/time-series data, metabolite 14, actual material inventory, biological replicates and quantitative QA.</figcaption></figure>{table(gap,[('category','Category'),('data_item','Data item'),('why_needed','Why needed'),('current_source_status','Current source status'),('action','Action'),('priority','Priority')])}</section>
<section class="section" id="next"><div class="kicker">What comes next</div><h2>Analyses that become available when measured data arrive</h2><div class="grid2"><div class="card"><span class="status partial">AFTER CORE DATA</span><h3>Production benchmark</h3><p>Titer, Yield, Productivity, effect sizes, replicate variation and a matched No-LLPS vs LLPS comparison.</p></div><div class="card"><span class="status partial">AFTER OD + SUBSTRATE</span><h3>Biomass-normalized uptake</h3><p>Substrate consumption normalized by biomass proxy and time, with the OD-to-biomass assumption stated explicitly.</p></div><div class="card"><span class="status partial">AFTER METABOLITE DATA</span><h3>Metabolite dynamics</h3><p>14 / 9 / 10 / 11 / glabridin time series; DMT substrate-preference comparison; Sankey only if quantitative mass-flow interpretation is defensible.</p></div><div class="card"><span class="status partial">AFTER INVENTORY</span><h3>SDG 12 resource indicators</h3><p>PMI, water intensity, solvent intensity, waste intensity and process energy per unit product.</p></div><div class="card"><span class="status partial">AFTER PRICE + RECOVERY</span><h3>SDG 9 economics</h3><p>Basic cost/g and sensitivity analysis for Yield, precursor, solvent, productivity and recovery.</p></div><div class="card"><span class="status missing">STILL REQUIRED</span><h3>Round 2 validation</h3><p>Return actual improvements to industry, consumers and a sustainability/process expert to judge practical significance and remaining limitations.</p></div></div></section>
<section class="section" id="downloads"><div class="kicker">Reusable package · Q4</div><h2>Download the current analysis tables</h2><div class="downloads"><a href="data/stakeholder_metric.csv">Stakeholder → Metric CSV</a><a href="data/sdg_mapping.csv">SDG mapping CSV</a><a href="data/process_inventory.csv">Process inventory CSV</a><a href="data/wetlab_gap_audit.csv">Wet-lab gap audit CSV</a><a href="analysis/README.md">Analysis notes</a></div><div class="note warning"><b>Competition-use boundary:</b> this page is an internal analytical scaffold. Final iGEM Wiki prose should be written/confirmed by the team, use real stakeholder quotations, real citations and real experiment/model outputs.</div></section>
</main></div><footer><b>GALATEA Sustainable Development Impact · analysis working site v2</b><br/>Built from the current team materials; no experimental result is invented where data are absent.</footer></body></html>'''
    (ROOT/'index.html').write_text(html_text,encoding='utf-8')

if __name__=='__main__':
    make_stakeholder_svg(); make_sdg_svg(); make_boundary_svg(); make_process_svg(); make_gap_svg(); build_html()

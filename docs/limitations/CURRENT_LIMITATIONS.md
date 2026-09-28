# Current limitations

- No matched G1 versus G2/G5 wet-lab dataset has been supplied.
- ADMET-AI 2.0.1 and ADMETlab 3.0 provide two model platforms for four definition-matched endpoints, but the existing endpoint-harmonized comparison is still only two-platform and ADMETlab exposes no uncertainty fields.
- Ten selected VEGA models now ran with Java 17; many records have LOW/MODERATE reliability. Native MW discrepancies are flagged, and stereochemistry is unresolved. The full VEGA platform was not run.
- ProTox selected endpoints ran through the official website; its API sample still returns 404. EPI/ECOSAR six-compound exports are now available, including source/domain warnings. CompTox still requires an individual API key.
- DrugBank percentiles and PCA are prediction-space context, not a formal chemical applicability-domain certificate.
- SBD and self-inhibitory peptide sequences remain unfrozen in the wet-lab protocol.
- Authentic standard availability for compounds 9, 10, 11, 13, 14 and 15 is not confirmed in the repository.
- The 1 g purified glabridin functional unit has not yet been reviewed by a sustainability or process stakeholder.
- Material, water, solvent, equipment, recovery, purity and cost inventories are empty templates.
- No quantitative containment result is available.
- Round 2 stakeholder validation has not been completed.
- Consequently, no claim that LLPS reduces resource burden or improves safety is currently supported.

- Panel coverage is a SCENARIO count over six manifest compounds, not complete pathway coverage or demonstrated bottleneck distinguishability. Reaction provenance, assay performance and panel cost remain unresolved.

- Chemprop attribution uses a nonphysical zero-feature baseline and fixed topology; numerical completeness is not causal validation. Alternative-baseline robustness is untested.
- MapLight is a selected-task recipe reproduction using current dependencies, not an exact leaderboard replication. Held-out TDC data do not validate GALATEA laboratory outcomes; see split overlap audits.
- EPI and VEGA share some underlying methods; these predictions cannot be counted as fully independent evidence.

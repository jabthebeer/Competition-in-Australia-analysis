# Decision log

Every assumption, deviation from the paper and judgment call, with a one-line rationale. Entries are append-only. Superseded entries are marked rather than deleted.

| ID | Date | Phase | Decision | Rationale |
|---|---|---|---|---|
| D-001 | 2026-10-05 | Setup | The project lives in a self-contained folder, `hf2025-replication/`, at the repo root. | User instruction. |
| D-002 | 2026-10-05 | Setup | Python is the main language, `output/report.md` is the deliverable, and this project's layout is used. This overrides the R-default `CLAUDE.md` on the unmerged branch `claude/kind-shannon-co8qal`. | User instruction to prioritise the replication prompt. |
| D-003 | 2026-10-05 | Setup | H&F (2025) PDF committed to `literature/`. EMX and other third-party PDFs will not be committed. | The RDP is released under CC BY 4.0 (RDP copyright page). Journal articles are copyrighted. |
| D-004 | 2026-10-05 | Phase 3 | Listed-firm financials: no institutional database. Fallback approved: ABS *Australian Industry* price–cost margins, ATO corporate tax transparency (concentration), ABS *Counts of Australian Businesses* (size distribution), and published BLADE figures as benchmarks. No firm-level DLEU/DLW markups. The superelasticity is treated as a sensitivity range around 0.13. | User has no access to Morningstar, WRDS, Orbis or similar, and approved the fallback. An optional pilot using agents to extract figures from annual-report PDFs is deferred to the Phase 3 check-in and not yet approved. |
| D-005 | 2026-10-05 | Phase 1 | In the model, cost-weighted and harmonic sales-weighted aggregate markups are identical (both = sales/variable cost). The two H&F columns are treated as two separate calibrations to different data targets. | Model algebra and H&F footnote 8. |
| D-006 | 2026-10-05 | Phase 1 | The paper's published numbers are never "corrected". Replicated values are reported beside them, and suspected typos (model_summary §3) are listed as discrepancies. | Transparency; the ground rules forbid fabrication. |
| D-007 | 2026-10-05 | Phase 2 | *Provisional.* The "elasticity of labour supply" sensitivity will vary the Frisch elasticity $1/\nu$ over {0.25, 0.5, 1, 2}. Both readings coincide at H&F's baseline value of 1. | H&F call $\nu$ the elasticity, but in eq. (1) the Frisch elasticity is $1/\nu$. To be confirmed against EMX. |

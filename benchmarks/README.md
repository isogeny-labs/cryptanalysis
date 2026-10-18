# Archived campaign reports

These entries retain browsing copies of source reports and graphs. Raw inputs,
protocols, run records and correctness certificates stay in the linked studies.
PNG copies are rendered at 150 dpi from the canonical source SVG where the
study's original PNG used a different rendering resolution.

The campaign uses L0/shared-host diagnostic terminology. These entries do not
claim this repository's **Tier 0 host-isolated** qualification: no isolation
receipt exists, and no comparative timing or end-to-end speedup is admitted.

| Date | Entry | Recorded diagnostic | Host and scope | Source |
|---|---|---|---|---|
| 2026-10-18 | [Learning controls](20261018-learning-controls/) | 88 WDSat calls; learned heldout conflicts 16,097 vs paper control 3,092, no improvement; group-kernel heldout incumbent/selected both 820 counted units; 1,718 aggregate receipts, whole-curve 90% interval unbounded | CPU only, one worker, `F4_F2_ECHELON=host`, shared four-CPU host; unqualified timing, no full IC claim | [Study](../experiments/ideas_learning_20261018/REPORT.md), [PDF](20261018-learning-controls/report.pdf) |
| 2026-10-18 | [Boolean solver controls](20261018-boolean-controls/) | 48 independently certified order arms, 16 existing F5/M4RI signature arms, 6 Dinur parity and 6 LPTWY search checks; scalar/native each retain twelve 20-second timeouts | CPU only, one worker, `F4_F2_ECHELON=host`, shared host; no credible exponent fit, invariant solving-degree or end-to-end speed claim | [Study](../experiments/ideas_boolean_20261018/REPORT.md), [PDF](20261018-boolean-controls/report.pdf) |

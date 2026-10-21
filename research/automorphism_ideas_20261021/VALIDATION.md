# Validation and remaining gates

Date: 2026-10-21. Scope: documentation, diagram and experiment planning only.

| Requirement | Evidence / state |
| --- | --- |
| Preserve five paper-derived ideas | README DGM-01 through DGM-05; all labeled proposed or awaiting reproduction |
| Identify overlap | Existing repository notes/catalog and PR pointers; folding is not presented as novel |
| Specify controls and acceptance | Per-workstream acceptance and matched single-target measurement contract |
| Record actual experiment activity | No experiments, run IDs, performance results or new certificates |
| Render the report | `make` passed with CairoSVG, Pandoc and XeLaTeX; all PDF pages and the embedded diagram inspected |
| Validate execution readiness | Not ready: fixture IDs, native harness/checker and frozen protocol are pending |

Work is isolated to a new study directory and a discoverability link in the
catalog README. The existing candidate, measurement, curve and route data
are unchanged. No native source or test implementation changes in this PR.

No native C build, solver correctness test, performance benchmark or Lean
proof was run. Document checks do not establish solver correctness.
Required CI and review remain merge gates; future implementation needs its
native correctness and evidence checks before any experiment claim.
The planning PR may be reviewed separately from future execution.

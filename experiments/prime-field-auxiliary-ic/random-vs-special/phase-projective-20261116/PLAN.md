# Core phase accounting and projective scalar multiplication

Implementation baseline: `5b8528ce0d2346ed1e5451b23f75ed315d2b6edf`.
There is no qualified Rust timing baseline. This is engineering preparation,
not a new field/curve search or performance experiment. [pcc:unverified]

| Requested work | Acceptance for this increment |
| --- | --- |
| Compare ordinary random IC with special auxiliary IC | Keep the three arms, actual columns and shared sampler; preserve all row/certificate controls |
| Improve common arithmetic | Move scalar-loop intermediates to projective coordinates; compare with separate affine addition on small groups and both requested fields |
| Separate the costs | Opt-in exact, disjoint core phases, local replay charged, initialization and early exits covered, no instrumentation in original APIs |
| Prevent misleading comparisons | Reject malformed/mismatched profiling scopes and partition totals; no timing ratio or speedup from the report checker |
| Establish measured improvement | Still open: checkpoint upload, admitted CUDA execution, immutable fresh panel, complete cold costs and independent signed replay |

The arithmetic hypothesis is that avoiding repeated affine inversions can
lower common preparation/validation/replay cost. A runtime benefit is
unmeasured and is not predicted from correctness-test elapsed times. The
change must apply equally to all three arms and cannot itself establish an
auxiliary-map advantage. [pcc:unverified]

Development controls: exhaustive repeated-affine-addition comparisons on all
nonsingular F_7 curves and selected F_31/F_127 curves, including torsion and
full-width unsigned scalars; separate affine scalar references at p=2^31-1
and p=2^61-1; all existing exact polynomial/SIMD, dense-graph, certificate and
random-base tests; profiled/unprofiled work/outcome equality without a live
time cap (plus the deterministic zero deadline); scripted-clock partition
checks; actual three-arm p=127 CLI hand-off; malformed-report refusal tests;
Rust 1.78/stable formatting, lint, documentation and binding controls.
These are unit/regression checks on an editing host, not natural-yield,
profiling-performance, fresh-target or benchmark runs.

Keep failed attempts with their exact source and command. Stop dependent
checks on invalid arithmetic/accounting; correct the source and retain the
failure. Freeze a new source for corrective checks. Never modify the archived
2,473-file snapshot. Qualified timings stay null.

Sources checked: the local core field/solve code, CLI and comparison spec on
the baseline above; root AGENTS.md and `.agents/skills/report-evidence/SKILL.md`.
The shared research-KB connector is not exposed in this runtime; the owning
lead atlas remains unavailable as recorded in the prior field-fiber report.
No literature/novelty claim, new ECDLP mechanism or atlas disposition is made.
The implementation uses ordinary Jacobian coordinates for existing scalar
arithmetic; no new mathematical theorem is claimed.

Next discriminating engineering lead after these controls: share/jointly
compute each row's two public scalar products and avoid unnecessary affine
normalizations when comparing the two sides. It must retain the affine oracle
and all final certificate checks. Measure only after the standing gates pass.

# Native evidence and development failures

`final-check-attempt3` is the final fixed-fixture verification record. Its
certificate replays on the current CLI. `post-main-replay.txt` confirms it
still replays after integrating main; imported native source bytes did not change.
Commands and scopes are in `../check.sh`, `../SPEC.md` and `../REPORT.md`.

The final check passes formatting, strict new-code Clippy with the existing
native suite lint policy, 62 library/native tests plus one CLI integration test,
and the 12-theorem transitive Lean audit. One upstream slow curve test remains
ignored exactly as in the source suite; the new B-163 test verifies its own
source generator and pulled-back generator order directly.

The public scalar-37 test is a known-answer control, not an unknown-log solve.
No wall-time ratio or speed claim is inferred from test-run durations. These
are deterministic unit, proof and fixture correctness checks, not a research
sweep. The failed S3 gate remains an infrastructure blocker for new experiments.

`final-check-attempt2` is an earlier valid certificate before closing-edge output
and the fixed spectral controls were added. Its exact library source snapshot
is retained; its implementation fingerprint was reconstructed and checked against
that snapshot plus the unchanged main/Cargo/native input bytes. Do not replay
that historical certificate against a later CLI or overwrite it.

Other attempt logs are development diagnostics: offline dependency absence,
Lean syntax and reduction problems, a missing audit subprocess PATH, inherited
native-module lint-policy differences, the rejected impossible toy subgroup,
SVG whitespace and raster-PDF size corrections. They are not successful proofs
or research runs. Full source snapshots were not taken for every preliminary
edit; those intermediate diagnostics are not claimed to be independently
replayable frozen experiments. Final source-bound verification is retained.
Compiled `.olean` build products are ignored; their checked source, toolchain,
compiler version and transitive native output are retained and CI rebuilds them.

The local lead atlas was materialized from indexed bytes without changing its
sparse patterns. Three setup failures are retained, followed by the successful
match: LEAD-TRF-ghs-binary-composite and KR-IC-5ea2f8 identify the known GHS/gGHS
baseline. This work is verification/tooling, not a new mechanism being promoted
into that atlas. The LMFDB NAS/cache paths were unavailable and no remote
catalogue result or LMFDB identity is claimed.

Current artifact-policy and global workflow-wiring checks pass locally. No old
scientific manifest, journal, PDF or claim was rewritten. `artifact-manifest.json`
binds the new evidence and explicit versions of active report/index files.

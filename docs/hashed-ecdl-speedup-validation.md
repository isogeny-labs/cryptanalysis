# Native exact-primality and witness engineering update — 2026-10-30

Paired source and fixture changes mirror crypto PR #2891. The new native
module verifies Pocklington proof nodes for optional parameter certification;
the exact default primality path gains a bounded u64 test and retains AKS for
larger uncovered values. The published ECCp-131 proof input passes parameter
and target-subgroup validation under its original two-million-step policy.

Functional leaf witness search preserves the original least word and full
graph evaluation while avoiding repeated prefix counts. A free-input interface
is searched in interface order with first-valid exit; derived interfaces retain
a full minimum-selection pass. Arbitrary graphs and explicit control mode use
the original prefix counts. The complete seeded relation certificate matches.

Actual owner checks: 34 native tests pass, including forged-proof, exact-count,
pin/alias/derived-interface, UNSAT, resource-exhaustion and old/new full replay
controls. Strict lint and Rust 1.78 all-target checks pass in crypto. This
workspace's hashed-ecdl-tensor package/all-target check also exits 0. The native
source/fixtures are byte-identical; integration lockfiles remain separate.

Evidence and the inspected diagram/plot/PDF are retained in
[crypto's pinned receipt](https://github.com/isogeny-labs/crypto/blob/c866ee97f4a8f90a85cd95dc19e99cc71c97e01f/research/hashed_ecdl_speed_20261029/README.md), under
research/hashed_ecdl_speed_20261029/ (review: crypto PR #2891). It includes a source manifest and actual
failed setup/test records. The 31-versus-1 assignment result is one four-bit
regression case, not a measured runtime or cryptographic-size speedup.

The frozen profiling and matched baseline/candidate performance panel is
blocked by missing S3 checkpoint transport/authenticated native execution.
No scientific run, benchmark, calibrated operation ratio, S/rho or runtime
confidence interval is claimed. Keep those requirements, the independent
general audit and both actual challenge solves open. Historical Python results
and the old native validation/source receipt are preserved unchanged.

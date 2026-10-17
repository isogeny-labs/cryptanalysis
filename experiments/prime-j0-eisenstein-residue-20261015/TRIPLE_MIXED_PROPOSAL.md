# A 76-tripling mixed Eisenstein radix for joint secp256k1 multiplication

The new schedule uses four norm-6481 quotient steps and twelve norm-58807
steps. Reverse Horner evaluation therefore applies `4*4+12*5=76` point
triplings, sixteen rotations, and sixteen projective additions. The checked
recurrence gives terminal norm at most 45,089 and both signed terminal
coordinates have absolute value below 450. This fits the existing nine-bit
direct-seed table and its dynamic Q-point graph. The 77- and 78-tripling
paths remain opt-in controls for the full-cost comparison.

The prior 77-step schedule uses three norm-6481 quotient steps and thirteen
norm-58807 steps. Reverse Horner evaluation therefore uses
`3*4+13*5=77` point triplings, sixteen rotations, and sixteen projective
additions. The checked recurrence gives terminal norm at most 5059 from
the same uniform initial bound. Its terminal coordinates have absolute value
below 150, so the opt-in evaluator raises its signed lookup limit to 150
and requests those points through the existing dynamic Q-table planner.
The earlier 78-tripling path remains available as a paired control.

The mixed recurrence evaluates `aG+bQ` using two quotient steps in radix
`81+omega` (norm 6481) followed by fourteen in radix `243+omega` (norm
58807). Reverse Horner evaluation applies fourteen `243+omega` point steps
and then two `81+omega` steps. Their fixed operator count is
`14*5+2*4=78` j=0 triplings, sixteen rotations, and sixteen projective
additions. The existing fixed `81+omega` and `243+omega` recurrences each
use 80 triplings. Digit additions, Q-table construction, inversions, memory,
and conversion are separate costs and determine the eventual wall result.

## Uniform initial bound and terminal proof

In the certified scalar lattice, the basis vectors `W` and `V` satisfy
`Q(W)=Q(V)=Q(W+V)=n`, where `n` is the secp256k1 subgroup order and
`Q(a,b)=a²+3ab+3b²`. For floor-cell remainders `0≤x,y<n`, the floor
representative `(xW+yV)/n` has

```text
Q((xW+yV)/n) = (x²+y²−xy)/n ≤ n.
```

If `x≤y`, then `x²+y²−xy = y²−x(y−x) ≤ y² ≤ n²`; the other case is
symmetric. The native scalar reducer chooses the nearest of four corners,
including the floor corner, so its selected representative inherits this
bound when its certified corner decision matches the exact four-corner
minimum. The Lean theorem exposes that selector comparison as a hypothesis.

Each radix step uses the existing digit bound and weighted norm inequality
`100D Q(next) ≤ 101 Q(current)+10100D`. Starting from `Q(initial)≤n`, two
steps with `D=6481` followed by fourteen with `D=58807` give
`Q(terminal)≤647<5000`. The terminal uses the existing norm-5000 table.
The [Lean module](TripleMixedRadix.lean) proves the lattice geometry,
selected-corner implication, numeric recurrence, exact mixed quotient
terminal statement, and shared two-scalar point Horner composition. It
builds with pinned Lean 4.34.1; the [proof verifier](verify_triple_mixed_lean.py)
records the build and `#print axioms` output in
`triple-mixed-lean-check.json`. The quotient-ring-to-native signed-limb
refinement, reciprocal corner decision, and curve-operation refinement
remain explicit implementation proof obligations.

For the 77-step path, the Lean module also proves the exact 3+13 recurrence,
its application to the quotient sequence, terminal coordinate range,
two-scalar Horner composition, and the tripling count. The pinned verifier
also audits the 76-step 4+12 recurrence, exact quotient terminal statement,
coordinate range, Horner composition, and tripling count: nineteen checked
declarations in total.

| 76-step result | Lean declaration | Exact bridge or hypotheses | Verification |
| --- | --- | --- | --- |
| Uniform starting norm | `selected_initial_norm_bound` | Exact lattice floor equations and selected-corner norm no larger than the floor corner | Checked |
| Sixteen-step terminal norm `≤45089` | `mixed_76_step_terminal_bound` | Initial norm `≤n`; four norm-6481 and twelve norm-58807 weighted step inequalities | Checked |
| Exact quotient terminal | `mixed_76_quotients_terminal` | Radix division identities and digit norm bounds at every step | Checked |
| Signed terminal coordinates `<450` | `mixed_76_terminal_coordinates_in_table` | Terminal pair norm `≤45089` | Checked |
| Two-scalar point recurrence | `two_scalar_mixed_76_horner` | Abelian addition and both radix endomorphism homomorphisms, with trace lengths 4 and 12 | Checked |
| Fixed tripling count `76` | `mixed_76_horner_tripling_count` | Integer arithmetic | Checked |

The checked statements are conditional at the native boundary: the
signed-limb recoder, corner selector, and curve-operation implementation
still require refinement checks against these hypotheses. The verifier
records every module build and `#print axioms` result under pinned Lean 4.34.1.

## Native implementation and replay

The opt-in [native recoder and evaluator](joint_mixed78.rs) reuse the
existing radix-81 and radix-243 digit selectors and the radix-243 Q-table
planner. The [command](rho_restart_joint_mixed78.rs) charges target Q-table
preparation and restart evaluation together. The
[hash-checked overlay](native_rho_restart_mixed78_overlay.py) adds the arm
after the pinned radix-81 and radix-243 overlays.

The local ARM64 release binary SHA-256 was
`f7f684d90314525f962668690e3a03387a6cec35724247c0016b20f89da8ec82`.
The [independent replay](triple-mixed-local-replay.json) verified 393 exact
point outputs over the frozen one- and 128-restart fixtures, alternate Q
points, 128 fresh seeded scalar pairs, and five edge cases. The first frozen
restart constructed 17 Q points; the 128-restart stream constructed 1,851.
Those figures identify the Q graph as a material part of the cost.

The archived parent source references eight temporary atlas binaries that
were absent from the local source archive. The first build failed on those
missing `include_bytes!` files. For this local correctness replay, the
missing files were supplied as empty diagnostic shims for modes outside this
path; that binary is not a complete reproducible benchmark artifact. The
replay receipt records this condition, and its elapsed fields are correctness
diagnostics only. A portable build must recover the real atlas bytes or
defer those unrelated atlas loads through an audited source change, then
freeze the full source and Linux binary hashes.

The opt-in [77-step recoder](joint_mixed77.rs), [runner](rho_restart_joint_mixed77.rs),
and [hash-checked overlay](native_rho_restart_mixed77_overlay.py) extend the
78-step implementation. The [frozen independent fixture](mixed77-independent-fixture.json)
is regenerated by [its script](mixed77-fixture-generator.py) using
`cryptography`'s secp256k1 scalar multiplication. The
[77-step local replay](triple-mixed77-local-replay.json) records 257 exact
output checks across frozen one- and 128-case runs and a fresh 128-case
same-point fixture. Its binary used the same diagnostic empty atlas shims
for unrelated modes; its elapsed fields are correctness diagnostics only.

The opt-in [76-step recoder](joint_mixed76.rs) and
[runner](rho_restart_joint_mixed76.rs) are added to the frozen portable
77-step source by a [hash-checked overlay](native_rho_restart_mixed76_overlay.py).
The [portable 76-step verifier](verify_portable_mixed76.py) builds this
source with no atlas placeholders and checks 257 mixed-76 outputs plus five
control outputs against the frozen and independent fixtures. Its
[receipt](triple-mixed76-portable-replay.json) retains the exact source and
binary hashes; local elapsed fields remain correctness diagnostics.

The [portable overlay](native_rho_restart_mixed77_portable_overlay.py)
replaces twelve machine-local compile-time atlas includes with lazy runtime
loads. An optional atlas mode requires `EISENSTEIN_ATLAS_DIR` and fails if
its bytes are unavailable; the joint rho-restart paths do not use that
directory. The benchmark source also omits archived test-only modules after
the release code, which contain machine-local paths; the executed release
functions remain in the source. The [portable verifier](verify_portable_mixed77.py) assembles the
archived source, applies hash-checked overlays, builds a release binary with
no atlas placeholder bytes, and replays the frozen and independent fixtures.
The [portable replay receipt](triple-mixed77-portable-replay.json) records
the source and binary hashes, 257 mixed-77 exact outputs, and four comparator
mode outputs on local ARM64. The
workflow is configured to build and replay this path on pinned Rust 1.93.1
under Linux.
Its local elapsed fields remain correctness diagnostics until the isolated
same-point benchmark runs.

The verifier can emit the exact source transfer archive with `--bundle-out`.
The prepared 20-entry, 3,009,079-byte bundle has SHA-256
`0598b16fb66efda38515bc2a3685c9ff38b3c2e797ca66d7e7c0a2451e0a998c`.
It contains Cargo inputs, all executed Rust source, compile fixtures, both
replay fixtures, and a source manifest. It contains no atlas shims or
machine-local absolute paths in Rust source. Transfer and Tier 1 measurement
remain subject to the existing RunPod source-egress approval gate.

## Decision gate

First compare the one-restart 77- and 78-step paths with the frozen
`243+omega`, `81+omega`, and OpenSSL arms on the same public point, charging Q preparation,
evaluation, and output conversion. Use the serial Tier 1 RunPod queue with
alternating pairs, exact replay, host counters, and bracketing A/A controls
under the [joint benchmark contract](RHO_JOINT_BENCHMARK_PLAN.md). The
focused [Tier 1 panel generator](make_tier1_mixed77_panel.py) freezes 112
serial one-restart pairs: mixed-77 against mixed-78, fixed radix-243,
fixed radix-81, and OpenSSL, bracketed by three OpenSSL A/A controls.
It requires the new pod ID, executable and `libcrypto` hashes, exposed CPU,
and exact source bundle before producing the manifest and rules.
The 76-step path needs the same serial one-target comparison after its own
source bundle and Linux binary are frozen; its 76-tripling count alone is an
operator-count improvement, not a wall-time result.
The [independent panel auditor](analyze_tier1_mixed77.py) regenerates those
rules, replays the fixture point through separate curve arithmetic, verifies
all source and runtime artifact hashes, reads every raw arm and pair ledger,
and gates the paired interval on complete runs and A/A controls. Missing,
failed, or noisy pairs remain recorded and leave the aggregate unknown.
Its rejected-preflight diagnostic produced zero valid pairs and unknown
comparison statuses; it is a failure-semantics check, not timing evidence.
The 128-restart stream asks the separate batch-amortization question. The three
saved triplings per restart become a measured improvement only if the full
charged interval passes that gate.

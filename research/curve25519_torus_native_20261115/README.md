# Curve25519 torus/S4: Rust qualification and route criteria

## Current native recovery and four-point scope

See the current [source-linked report](reports/recovery-v4/REPORT.md),
[diagram](reports/recovery-v4/pipeline.svg) and
[PDF](reports/recovery-v4/report.pdf). The bounded native four-point M=1
controls match the complete oracle for member/nonmember targets; final
consumer tests report nine unit tests and one process-level test passing.
PCC-20261115-47a01f. [pcc:unverified]

The report's shared-store pointer is tracked by the
[publishing handoff](reports/recovery-v4/PUBLISHING.md); its upload receipt
and current-head artifact check remain required before landing.

Bounded native root recovery is implemented: structured Singular output,
gcd(f,X^p-X), bounded splitting and triangular assignments, followed by
the original equations, rational membership/lifts and actual signed point
sums. `prepare-tree` and `recover-tree` accept public summation-tree cards
of arity 2–8 with one or four membership branches. Errors, malformed frames
and exhausted recovery limits are inconclusive; empty output is not an
absence certificate.

The preserved [three-point native controls](evidence/native-recovery-v3/)
match their complete M=1 oracle. Actual-field four-point tests also exercise
a synthetic basis isolating a known assignment, membership/sign validation
and mutations. A synthetic basis tests recovery, not discovery by a solver.
PCC-20261115-ec9f29 records the earlier three-point controls; later logs and
records are linked by the current report. [pcc:unverified]

The [route criteria](ROUTE_CRITERIA_V3.md) explicitly separate the four-point
collision theorem, finite solver promise and asymptotic cost claim. A failure
of one does not disprove all representations or index calculus. The shared
[proof/cost obstruction](https://github.com/isogeny-labs/crypto/blob/98b6b736a53412ef86f02f9e789edc393af1fc20/problems/curve25519-torus-four-point-decomposition.md)
tracks gamma<1 and the still-open family/phase assumptions.
The original `ROUTE_CRITERIA.md` remains byte-identical for its published PCC
record; the extension has its own immutable snapshot and record
PCC-20261115-13362e. [pcc:unverified]

New commands, after freezing an immutable qualifier:

```sh
qualifier prepare-tree PUBLIC_TREE.json NEW_DIRECTORY
qualifier recover-tree PUBLIC_TREE.json NATIVE_TRANSCRIPT NEW_DIRECTORY
qualifier native-tree-controls /absolute/path/to/Singular NEW_DIRECTORY
```

The last command is restricted to constructed actual-field M=1 diagnostics,
four summands, four CPU seconds/five wall seconds/768 MiB per native process.
It cannot dispatch full-base jobs. A full-base solve has not been run.
Current reproduction also requires the tree source pin in TREE_DEPENDENCY.json;
the older DEPENDENCY.json pins the unchanged three-leaf library.
Check out the TREE_DEPENDENCY revision for both current crates; the historical
three-leaf source hashes still match at that revision. Shared source is in
[crypto PR #4364](https://github.com/isogeny-labs/crypto/pull/4364).

## Historical qualification, revision 2

The original qualification and report below remain historical evidence.
Their pending-root-recovery statements describe that earlier revision.

This study consumes the reusable Rust circuit compiler in the adjacent
`isogeny-labs/crypto` checkout, `tools/torus-s4`. It freezes a native qualifier,
serializes solver inputs, and checks known triples after compilation. The
[route rejection criteria](ROUTE_CRITERIA.md) distinguish proof of a scoped
exclusion from a failed quantitative promise or a parked implementation.

The final producer qualification reports all five frozen actual-field cases
compiled and both supplied known triples passing separate circuit and
point-sum checks. Three full-M inputs have 395 variables and 396 quadratic
equations; the two M=1 controls have 17 and 18 respectively. The consumer's
three development tests pass. No full-M solver was invoked. [pcc:unverified]

See [protocol and pending solver gate](PROTOCOL.md),
[raw harness tests](harness-final-tests.log),
[immutable qualification evidence](evidence/qualification-v2/),
[diagram](reports/pipeline.svg), and [PDF](reports/report.pdf).
PCC records: `PCC-20261115-9d157e` (producer qualification),
`PCC-20261115-638ca4` (criteria scope). Standing remains unverified until a
trusted signed verdict is recorded; the producer's manifests are not that verdict.

From the cryptanalysis repository root, with the pinned adjacent crypto
checkout described by DEPENDENCY.json:

```sh
cargo test --locked --release --manifest-path research/curve25519_torus_native_20261115/Cargo.toml
cargo build --locked --release --manifest-path research/curve25519_torus_native_20261115/Cargo.toml
research/curve25519_torus_native_20261115/target/release/curve25519-torus-qualification freeze /tmp/torus-qualifier-new
/tmp/torus-qualifier-new/qualifier qualify \
  research/curve25519_torus_native_20261115/cases \
  research/curve25519_torus_native_20261115/known-triples.json \
  /tmp/torus-qualification-new
```

All output paths must be new. Retain each immutable qualifier and its manifest;
rebuild to another path after changing source. The source dependency is a path
so it can be developed without Cargo cloning a multi-gigabyte monorepo. Before
reproduction, check out the exact crypto revision in DEPENDENCY.json and check
its listed source digests. Cargo.lock alone does not pin a path dependency.

`check CASE.json TRIPLE.json` checks three decimal-string Montgomery u values
through membership, rational lifts, signs, group addition and circuit evaluation.
It is a candidate checker, not an independent signed verifier or root solver.
The full-M triangular-root recovery and aggregate-CPU runner remain pending.

Fixtures came from the preceding campaign (seed 2026111508). They are public
regression data, not a fresh held-out yield sample. The source case files retain
historical kind hints for provenance; serialized case.json removes those hints
and no scalar generation labels are supplied to the compiler. Two uniform
raw targets have no asserted nonexistence result. Work is before cofactor
clearing on the actual p and A, using one torus coset.

The native Singular M=1 backend control is recorded in the linked crypto study.
The larger EKS pilot remains pending native runner/image integration and live
cost/capacity readback. No cloud build/job or substitute integration fixture
was submitted. The protocol lists the exact missing execution obligations.

Sources: crypto/src/bin/curve25519_family.rs, crypto/src/ecc/field.rs,
[RFC 7748](https://www.rfc-editor.org/rfc/rfc7748),
[RFC 9380](https://www.rfc-editor.org/rfc/rfc9380),
[Petit–Kosters–Messeng 2016](https://people.maths.ox.ac.uk/petit/files/16PKC_primeECDLP.pdf),
and [Buresh-Oppenheim et al.](https://www.cs.toronto.edu/~toni/Papers/homo-icalp.pdf).
KB wrapper exits 127 and no KB MCP is exposed; primary sources and repository
code were the fallback. The lead-atlas YAML fetches returned decoding errors.
No novelty is inferred from those access gaps.

Canonical leaderboard/progress graphs are unchanged: this study adds
qualification and scoped decision criteria, with no admitted timing comparison.
The report PDF was rendered from its committed LaTeX/SVG and visually inspected.

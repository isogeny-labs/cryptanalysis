# Curve25519 torus/S4: Rust qualification and route criteria

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

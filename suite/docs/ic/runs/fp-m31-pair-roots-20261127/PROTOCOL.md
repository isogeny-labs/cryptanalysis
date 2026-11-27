# M31 reusable pair-root index: frozen local protocol

This protocol tests a target-independent signed pair-root index for the native
`prime-field-auxiliary-ic` m=3 and m=4 decomposition path. It is a local,
producer-run engineering comparison for cryptanalysis PR #2005 and workspace
PR #192, not an independently admitted speedup or a new PCC claim.
[pcc:unverified]

## Public instance and source freeze

- Field: p=2147483647.
- Curve: y^2=x^3+2x+14, prime order N=2147505293.
- Generator: G=(1,814455902).
- Coordinate-only targets: Q0=(2144058214,807222724) and
  Q1=(1764015007,688050509).
- Factor base: native norm-one torus depth 7, direct-control arithmetic, with
  every selected point checked in the order-N subgroup.
- Baseline source: parent commit b4e8b162c60c2cd5837d30c51c2d616c12e5d38b.
- Candidate: the commit that adds the lazy canonical signed-pair root index.
- Rust 1.88.0, release profile. Record exact binary SHA-256 values.

No target scalar is supplied to either worker. A returned decomposition is
counted only after native group replay against the input coordinates.

## Frozen panel

Use SplitMix64 target streams 0x8a5cd789635d2dff and 0xd94f3a6c42b81705,
one per public target. For each implementation, target, and m in {3,4}, run
4096 coordinate queries after one untimed process warm-up. Run paired order
ABBA then BAAB for four measured observations per cell. Each observation
includes pair-index construction, query processing, and replay in its cold
wall time. Retain setup and query time separately as descriptive components.

Controls:

1. Existing exhaustive p=127 and p=8191 m=3/m=4 tests must pass.
2. Baseline and candidate must return exactly the same relation presence and
   canonical signed terms for every query. Any mismatch invalidates timing.
3. An A/A candidate binary-hash control uses the same schedule and must not
   show a systematic order effect larger than the candidate/baseline effect.
4. Preserve all failures and capped cells. Per-cell wall cap is 60 seconds;
   no smaller prefix may replace a capped arm after outcomes are known.

The primary observable is cold nanoseconds per completed query. The secondary
observables are setup nanoseconds, relation count, and m=3/m=4 query
nanoseconds. Success for this engineering stage is a lower paired median cold
cost with exact row parity; a null result or regression is retained. This
panel alone does not qualify an end-to-end IC speedup because it does not time
rho, isolation, full relation collection through recovered scalar, or signed
independent evidence admission. [pcc:unverified]

## Frozen complete-recovery follow-up

After the fixed-prefix row-parity screen passes, run one complete coordinate-
input recovery on Q0 with each exact baseline/candidate source. Use torus depth
7 direct-control arithmetic, m=4, relation seed 9961743651143974399,
`walk_lanes=64`, `max_queries=100000`, `max_relations=512`,
`max_proof_nodes=4194304`, and a 180-second process cap. Charge base/workspace
construction, relation search, sparse elimination and certificate replay in
the reported cold wall. The input contains only public curve and point
coordinates; neither worker receives the target scalar.

The candidate succeeds only if it returns a locally replayed certificate and
the recovered scalar independently reproduces Q0 under native multiplication.
The baseline is not replaced or downscaled if it caps. A completed matched
pair supports only a producer-local end-to-end engineering comparison; it
still lacks admitted isolation, matched rho and signed independent evidence.
[pcc:unverified]

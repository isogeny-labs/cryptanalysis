# Exact dual-end partial-sum support on the N41 public point

The unpinned N41 phi-chain now has exact finite support constraints at both
ends: 1,788 forward-pair masks on `partial0` and 3,577 target-conditioned
suffix-pair masks on `partial8`. The forward support comes from all 3,600
signed choices for leaves 0 and 1; six choices have no finite reciprocal-phi
coordinate. The backward support comes from all 3,600 signed choices for
leaves 10 and 11 and the verified public-point endpoint. Every one of the
twelve leaf codes stays free. The dual-end query reached its 240-second cap
without a terminal solver state.

## Construction and verification

The [frozen protocol](protocol.json) identifies the prior corrected suffix
formula, public point, solver, code and resource caps. The previous suffix
formula SHA-256 is
`104b2dde30da29113538a88f218246174ebbaedef4e4fbab51ae2715f8c67253`.
The dual-end formula SHA-256 is
`c624b7e43075c221fe18b513307600cdfab6208f4a7c34ff99e1e1f9e8f569d2`.
The [builder](build_sage.py) enumerated the signed forward pairs and appended
membership implications for `partial0` variables 74–114 to the exact prior
formula. [audit_sage.py](audit_sage.py) independently re-enumerated the pair
outputs, verified the six exceptional cases, and checked every newly appended
XCNF record byte for byte. It returned
`PASS_DUAL_END_GROUP_AND_XCNF_AUDIT`. Generic pair-list completeness and
witness properties are [checked in Lean](PROOF_MAP.md); the concrete curve and
XCNF bridge is covered by the Sage audit.

| Unpinned public-point arm | Exact status | Parent wall | Sampled combined peak RSS |
| --- | --- | ---: | ---: |
| Corrected suffix support only, prior paired run | `BOUNDED_UNKNOWN_ARM_WALL_CAP` | 240.089 s | 395,231,232 B |
| Forward and backward support | `BOUNDED_UNKNOWN_ARM_WALL_CAP` | 240.124 s | 401,178,624 B |

The two arms used the same one-public-point workload, one CryptoMiniSat
worker, solver flags, and 4 GiB RSS cap. The prior arm is retained in its own
frozen run; this follow-up ran the dual-end arm under the same 240-second
parent cap. Neither arm has a terminal SAT or UNSAT line. The
[receipt verifier](verify.py) returned `REPLAY_PASS` for the dual-end formula,
command, raw logs, and resource record. These ordinary-host capped timings
measure search limits, not a paired online speedup.

## Next algorithmic gate

Both support constraints are logical consequences of the existing chain
equations; adding them as selector clauses did not make the search terminal
under this cap. The next gate is an external exact
group-index test: form a reusable forward pair-sum table, compute
target-conditioned residual keys from a right partial family, and reject an
entire family on an absent key. The archived N41 two-plus-one join has an
independently replayed public-point relation and provides a positive control.
Measure the number of families rejected and exact witnesses expanded on
frozen N41 inputs before using the corresponding indexed oracle inside a
larger N131 decomposition search.

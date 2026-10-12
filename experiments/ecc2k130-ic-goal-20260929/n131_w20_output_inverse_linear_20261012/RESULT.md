# Inverse-output linearization on a fresh N131 W20 target

The W20 seven-pair point-decomposition equation admits an exact
inverse-output form: if `ab=1`, then
`aP(s)+(1+h²)a²+h²=0` is equivalent to
`P(s)=(1+h²)a+h²b`. The [Lean theorem](OutputLinearization.lean)
checks the equivalence under the characteristic-two ring laws and `ab=1`,
with no reported axioms. The implemented circuit exposes 131 linear
source-product equations per pair while retaining the exact inverse-trace
endpoint gates and six S3 links. Its constructed seven-pair assignment
satisfies **423,142 clauses and 73,844 native XOR rows**.

The [new one-point workload](public_target.json), ID `586ce0d6c0fd`, is
on `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, curve `y²+xy=x³+1`, prime subgroup order
`680564733841876926932320129493409985129`. The checked repository
[Sage runtime receipt](sage_runtime_info.json) was saved before
`make_target.py` generated the point and its `[4]` raw preimage. The
independent checked-Sage [fixture replay](target_replay_result.json) verifies
the seed-to-scalar derivation, generator, target, raw preimage, and reciprocal.
The target-generation scalar is in [private_fixture.json](private_fixture.json)
for independent replay; `linear.py ordinary` reads only the public target
and the solver receives only its frozen XCNF. All seven source pair codes,
pair outputs, endpoint inverse witnesses, output inverse witnesses, S3
intermediates, and branch bits are unpinned in the public search.

The source remains the frozen W20 span of `t..t²⁰`, fixed seed 898618,
with 132,045 accepted pairs per slot and Frobenius rotations
`0,18,36,54,72,90,108`. The selected seven-window base has 3,697,260
usable points before folding and 263,959 folded columns. The pair-product
basis has [rank 19](basis_rank_result.json) in its 131 output bits, hence a
candidate product must obey 112 independent linear conditions. The present SAT circuit expresses
the 131 equations with 19 selector variables; eliminating the selectors
outside the solver is the next exact encoding gate.

| Frozen formula stage | Prior W20 inverse-trace | Output-inverse linearized |
| --- | ---: | ---: |
| Variables | 167,935 | 217,842 |
| CNF clauses | 352,337 | 423,142 |
| Native XOR rows | 48,134 | 73,828 |
| XCNF bytes | 10,390,466 | 11,914,495 |

The new encoding grows the formula by 49,907 variables and 25,694 XOR
rows. Counts are based on the earlier [ordinary build receipt](../n131_w20_inverse_trace_20261012/ordinary_build_result.json)
and the new [fresh-target build receipt](ordinary_build_result.json).
The latter pins the formula hash; [protocol.json](protocol.json) and
[solver_protocol.json](solver_protocol.json) pin source, target, solver,
caps, and flags before the public attempt.

The ordinary-target search used one CryptoMiniSat worker,
`--maxtime=600`, a 615-second parent cap, and a 4-GiB child RSS cap.
The [result receipt](solver_result.json) records `BOUNDED_UNKNOWN` after
615.054 seconds, 514.701 sampled CPU seconds, 485,998,592 sampled peak
child RSS bytes, and 3.471 million conflicts in the last logged restart.
The [raw stdout](solver.stdout.txt) shows Gaussian elimination being
disabled during search; stderr is empty. There is no terminal model to
feed the prepared [XCNF auditor](audit_model.py) and checked-Sage
[curve replay](replay_model.py). This status preserves the full failed
bounded attempt; it supplies neither a natural relation-yield estimate
nor an end-to-end IC online time.

Formula construction took 2.881 seconds and serialization 0.014 seconds
in a separate process before the solver run. The older W20 search used
a different public point, so its conflict count or wall time is not a
paired performance comparison. Host-level CPU isolation was unavailable.
Candidate ID remains `null` while verified ordinary relations, useful
rank, factor logs, target scalar recovery, and matched same-point rho
accounting are pending. The [proof map](PROOF_MAP.md) identifies the exact
Lean theorem and the remaining concrete-field formalization bridge.

The next focused test is to row-reduce the exact 131-by-19 pair-product
matrix before SAT encoding. Its 19 pivot coordinates can recover the
source selectors from `(1+h²)a+h²b`, leaving 112 parity checks that the
solver can use without runtime Gaussian elimination. A checked
constructed assignment and a frozen same-point bounded query can decide
whether that representation improves search enough to justify further
ordinary N131 relation collection.

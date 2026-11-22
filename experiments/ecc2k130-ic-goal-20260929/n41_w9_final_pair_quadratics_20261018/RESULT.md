# A table-free final-pair root gate from two quadratics

## Contribution

The N41 target-conditioned final-pair gate now uses the fixed-seed
pair-output quadratic followed by the target S3 quadratic. This removes
the 284-row lookup while preserving **all 284 independently audited
target-translated roots**. The exact Boolean circuit passed the archived
relation and rejected all 32 frozen reachable controls. It has **128,017
variables and 353,073 total constraints**, smaller than the preceding
direct two-quartic circuit. In a frozen one-worker 20,000-conflict probe,
its paired decision ratios were **0.696/0.696** and wall ratios were
**0.433/0.335** against the direct gate. That passed the predeclared N41
ordinary-query promotion gate.

## Method and exact instance

The field is `GF(2)[u]/(u^41+u^3+1)` and the curve is `y²+xy=x³+1`, curve
ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`. The
public point is `Q=(1936680952394,910597499030)`. Five aligned W9 pair
slots have rotations `(0,0,12,12,24)`, 71 allowed source codes each and
four signed states per code. All five eight-bit codes, the preceding
41-bit reciprocal, final pair-output reciprocal and shared target root
remain free in the circuit. The complete IC `candidate_id` is `null`.

For final source product `p` and pair-output reciprocal `u`, impose
`C u²+p u+H=0`, where `H` is the rotated half-trace constant and `C=1+H`.
For public target reciprocal `t` and shared root `w`, impose
`(1+(tu)²)w²+tu w+(t²+u²)=0`. The latter is the reciprocal-x S3 link
between the final pair and the target. The first-three-pair F4 norm,
preceding-pair quartic `f(w)=0`, allowed-code rules and folded-column
collision exclusions are retained. The [proof map](PROOF_MAP.md) gives
the elimination identity and checked Lean proofs in both directions,
including the singular case, under the explicit source-splitting
hypothesis. It also records the remaining concrete field/curve bridge.

## All-code root and Boolean audits

The [Sage protocol](audit_protocol.json) froze the source, public target,
284-row translated table, previous independent root audit, checked
[runtime](sage_runtime_info.json) and a 120-second/4-GiB envelope.
The [all-code result](audit_result.json) checked **71 pair quadratics,
142 pair-output roots, 142 target S3 quadratics and 284 shared roots**.
Their outputs equal the independently translated signed-state roots for
every final code and state. No S3 quadratic lost its leading term. The
arithmetic interval took **2.013 s**, with **255,787,008 B** self peak RSS.

The [build protocol](build_protocol.json) pinned that audit before
Boolean construction. The [builder](build.py) checked one complete
satisfying archived assignment and 32 rejecting source-valid controls.
Its measured interval was **28.387 s** including controls, with
**155,533,312 B** self peak RSS under the 300-second/4-GiB envelope.
The [read-only verifier](verify.py) checks frozen source hashes, all
root sets and Boolean decisions, XCNF counts, 163 unpinned code and
reciprocal input bits, Lean output and raw solver streams.

| Circuit | AND gates | Variables | CNF clauses | Native XOR rows | Total constraints | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct two-quartic root | 113,361 | 129,751 | 341,901 | 16,268 | 358,169 | 11,119,913 |
| Pair plus S3 quadratics | **111,680** | **128,017** | **336,899** | **16,174** | **353,073** | **11,020,550** |

## Frozen solver probe and ordinary query

The [probe protocol](probe_protocol.json) fixed serial
direct/quadratic/quadratic/direct order, one CryptoMiniSat worker, 20,000
requested conflicts, 170-second solver limit, 180-second parent cap and
4-GiB sampled combined RSS. All arms ended `INDETERMINATE_CONFLICT_CAP`
with monitors passing. The quadratic arms made **31,602 decisions** at
the conflict boundary versus **45,386** for each direct arm. Their
wall times were **7.007/5.629 s**, versus **16.184/16.815 s** for the
adjacent direct arms. The predeclared gate required at most 80% of paired
decisions and at most 125% of paired wall; both pairs passed. The
[aggregate probe](probe_result.json) retains every raw stream and arm
receipt. These are ordinary-host stage diagnostics.

The [query protocol](query_protocol.json) fixes the same public point and
unpinned formula, exact solver binary, one worker, 590-second solver limit,
600-second parent cap and 4-GiB sampled combined RSS. A SAT model, if
produced, is independently replayed against the five signed source-pair
points, the preceding and final pair reciprocals, and the exact curve.

The [query receipt](query_result.json) records **`BOUNDED_UNKNOWN`,
`WALL_CAP`** at **600.033 s** parent wall. The last flushed restart line is
restart 1,504 at approximately 1,011,000 conflicts. The solver stream
contains no SAT, UNSAT or INDETERMINATE terminal line; those conflicts are
search progress, not a relation-yield measurement. The monitor sampled
combined RSS 5,648 times, peaking at **327,467,008 B**, with no monitor
error. Stderr is empty; both raw streams are hash-pinned in the receipt.
The target-dependent circuit build and bounded query total **628.420 s**
of charged stage wall. Launcher checks and process startup are outside
those intervals. Independent model replay was conditioned on a SAT result
and was not invoked for this capped run.

## Next discriminator

The two quadratic equations still leave `u` and `w` as 82 free field bits.
For a source-valid code with nonzero product `p`, normalize the first
equation to `v²+v=C H/p²`; its two roots give
`u=(p/C)v`. For the target S3 equation with nonzero `A=1+(tu)²` and
`B=tu`, normalize to `r²+r=A D/B²` and recover
`w=(B/A)r`, choosing one bit for each quadratic root. The audited N41
domain has two roots in both stages and no `A=0` case; a scalable circuit
must retain explicit exceptional branches for other fields and source
codes. The next preflight should build this code-plus-two-choice-bit map,
measure inversion and half-trace costs, and test it against all 284 N41
source states and an independently checked N131 W29 source sample before
another ordinary query. This directly tests whether functionalizing the
quadratic witnesses improves search while respecting the source-bound
600-second/4-GiB N131 gate.

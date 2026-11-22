# A 284-row final-pair selector on the direct N41 quartic gate

## Contribution

The audited final-pair root table is now an exact **nine-bit selector** in
the direct N41 circuit. Each of its 284 valid values forces both the final
source code and its 41-bit target-translated root; the other four codes and
the preceding reciprocal remain free. The circuit passed the archived
relation and all 32 frozen reachable controls. Its formula has **123,824
variables and 355,594 total constraints**, with all **14,144 selector
clauses** independently checked against the serialized XCNF.

At fixed conflict counts the selector ran faster than the direct-root
baseline, but the first predeclared gate failed on decisions and a fresh
50,000-conflict holdout failed its same-formula noise check. These are
retained as distinct outcomes. A separately frozen exploratory ordinary
N41 query tests relation recovery under the one-worker/600-second/4-GiB
envelope without treating those stage timings as an admitted speedup.

## Exact construction and proof

The field is `GF(2)[u]/(u^41+u^3+1)` and the curve is `y²+xy=x³+1`, curve
ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`. The public
point is `Q=(1936680952394,910597499030)`. Five aligned W9 pair slots have
Frobenius rotations `(0,0,12,12,24)`, 71 allowed codes each and four signed
states per code. A complete IC pipeline remains `candidate_id: null`.

For each signed final-pair state `E`, the [independently audited table](../n41_w9_target_w_bdd_20261017/audit_result.json) stores its code and
`w=1/x(Q−E)`. The 284 `w` values are distinct, and the 71 final-pair
quartics split into exactly those four field roots per code. A nine-bit
selector accepts indices `0,…,283`, rejects `284,…,511`, and implies each
of the 49 output bits of its selected code/root pair. The final quartic
`g(w)=0` is therefore enforced by table membership. The remaining
preceding-pair quartic `f(w)=0`, first-three-pair F4 norm, allowed-code
rules and folded-column exclusions are retained. The [Lean proof](Selector.lean) checks the generic guarded-clause implication and row
completeness; the [proof map](PROOF_MAP.md) gives the finite N41 and
curve/source obligations.

## Frozen circuit and clause audit

The [build protocol](build_protocol.json) pins the source, target, panel,
284-row table, independent all-code root audit and checked
[Sage runtime](sage_runtime_info.json). The [builder](build.py) took
**61.270 s** including complete panel assignments, with **145,866,752 B**
self peak RSS under its 300-second/4-GiB envelope. The archived relation
selects row 111 of the canonically sorted table. The [read-only verifier]
(verify.py) finds precisely 228 invalid-index clauses and `284×49` guarded
output clauses in the XCNF; none of the 82 free code, reciprocal or selector
bits has a direct unit clause.

| Gate | AND gates | Variables | CNF clauses | Native XOR rows | Total constraints | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct two-quartic root | 113,361 | 129,751 | 341,901 | 16,268 | 358,169 | 11,119,913 |
| Final-root selector and one quartic | **107,990** | **123,824** | **339,891** | **15,703** | **355,594** | 11,392,596 |

## Frozen solver probes

The first [probe protocol](probe_protocol.json) fixed serial
direct/selector/selector/direct order, one worker, 20,000 requested
conflicts, a 170-second solver cap, 180-second parent cap and 4-GiB sampled
combined RSS. All four arms ended `INDETERMINATE_CONFLICT_CAP`, with monitors
passing. The selector/direct paired wall ratios were **0.512** and **0.526**;
its decision ratios were **3.323** in both pairs. The predeclared gate
required decision ratios at most 0.8, so it failed. The [aggregate receipt]
(probe_result.json) links all raw streams and per-arm results.

The subsequent [holdout protocol](holdout_protocol.json) fixed a fresh
50,000-conflict boundary and a wall-time gate: both paired selector/direct
ratios at most 0.75, and each same-formula A/A wall ratio at most 1.25.
All four [holdout arms](holdout_result.json) reached the conflict cap with
monitors passing. Paired wall ratios were **0.360** and **0.591**, while the
direct A/A ratio was **1.136** and selector A/A ratio was **1.444**. The
noise gate failed. The first holdout launch stopped before solver startup
because its protocol writer used the probe filename; that
[setup failure](holdout_attempt1.json) and byte-for-byte protocol recovery
are retained.

## Exploratory ordinary query

The [query protocol](query_protocol.json) fixes the same public point,
free first-four codes, free preceding reciprocal, free nine-bit selector,
exact solver binary, one worker, 590-second solver limit, 600-second parent
cap and 4-GiB sampled combined RSS. A SAT model is independently replayed
against all five signed source-pair states on the exact curve before a
relation is counted. This query is exploratory because the holdout noise
gate failed.

The [query receipt](query_result.json) records **`BOUNDED_UNKNOWN`,
`WALL_CAP`** at **600.055 s** parent wall. The last flushed restart line is
restart 772 at approximately 320,000 conflicts. The stream has no SAT,
UNSAT or INDETERMINATE terminal line; the restart count is search progress,
not a relation-yield measurement. The monitor sampled combined RSS 5,797
times, with a peak of **196,395,008 B** and no monitor error. Stderr is
empty, and the raw streams are hash-pinned in the receipt. The target-dependent
build and query sum to **661.325 s** of charged stage wall. Launcher checks
and process startup are outside those intervals. Independent curve replay
is conditioned on a SAT model and was not invoked for this capped run.

## Next discriminator

The selector exposes target-conditioned final-pair information early, but
its literal table is tied to the 284-row N41 source. The nominal N131 W29
source has 28 free canonical code bits and up to four signed states per
code. Directly extending this guarded-output scheme over all nominal
`2^30` states would require `2^30×159 = 170,724,950,016` output clauses
before the rest of the circuit; the actual usable N131 table is not yet
enumerated, so this is a nominal scaling projection rather than a measured
N131 formula. The next source-bound test should compute the final root from
the W29 code and a small branch choice through its pair equation and public
target, then impose the preceding-pair quartic without enumerating the
target-translated table. Freeze N41 correctness controls and a matched
ordinary-query gate before projecting that algebraic circuit to N131.

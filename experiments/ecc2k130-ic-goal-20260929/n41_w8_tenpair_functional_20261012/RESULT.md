# Functional S3 roots give a checked N41 ten-pair control and a bounded public search

An exact **forward-root circuit on the nonexceptional reciprocal chart**
reconstructs the frozen N41 ten-pair public-point witness from ten selected
source states and nine root bits. CryptoMiniSat solved that pinned control
in **0.255 seconds**, and an independent parser checked its model against
all **604,546 CNF clauses and 127,245 native XOR rows**. The same formula
with every source state and root bit free entered ordinary search on the
frozen public point and reached its **180-second parent cap** with active
restarts and `BOUNDED_UNKNOWN`. This establishes a functioning forward
arithmetic encoding and a measured unpinned search boundary.

The instance is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t^3+1)`, curve `y²+xy=x³+1`, subgroup order
`549756390943`, and cofactor four. The six-rotation W8 source has 125
rational masks, **B=1,000** usable signed-Frobenius points before folding,
and 117 folded columns in the prior exact geometry census. This circuit
uses ten free pair slots `(0,1,2,3,4,5,0,1,2,3)`, each selecting one of
140 signed pair states, with a ten-distinct-edge shield. Its target is the
same frozen public point `(920359962848,755404565011)` and all four raw
preimages used in the independently verified [unpinned ten-pair join](../n41_w8_tenpair_density_control_20261012/RESULT.md).
The stage remains a component (`candidate_id: null`).

For reciprocal inputs `a=1/x(P)` and `b=1/x(Q)`, write `p=ab`,
`A=1+p²`, and `C=(a+b)²`. The S3 point-sum equation is
`Az²+pz+C=0`, where `z=1/x(P+Q)`. The [builder](build.py) computes the
two Artin–Schreier roots of this quadratic from `a,b` and one Boolean
branch bit, using a deterministic Itoh–Tsujii inverse and binary-linear
half-trace. It handles `A=0` with the exact linear root `z=C`, checks the
original S3 equation, and requires nonzero reciprocal outputs. The nine
links follow a balanced ten-leaf tree and end at a four-way raw-target
selector. This chart preserves the known positive relation; identity and
zero-`x` intermediate sums require separate exceptional branches in a
complete solver.

The [checked-Sage audit](audit_result.json) independently reconstructed
all ten signed source points, nine intermediate group sums, root branches,
and raw target preimage one. It reported
`PASS_INDEPENDENT_SAGE_N41_FUNCTIONAL_ROOT_CHART 9`. The source and
positive chart were frozen in [audit_protocol.json](audit_protocol.json)
before that job, and the checked [Sage runtime](sage_runtime_info.json)
was saved first. The [solver protocol](protocol.json) then froze both
XCNFs, source and solver hashes, target, one worker, 180-second parent cap,
and 4-GiB combined RSS cap before control and ordinary search. A direct
complete-assignment check passed every row of both formulas in
[control_result.json](control_result.json).

| Stage | Exact result |
| --- | ---: |
| Ordinary variables / AND gates | 289,065 / 160,407 |
| Ordinary CNF clauses / native XOR rows | 604,526 / 127,245 |
| Ordinary XCNF bytes | 14,922,651 |
| Ordinary formula construction / serialization, measured separately | 0.764396 s / 0.011375 s |
| Pinned solver control | `SAT`, 0.255117 s, 125,943,808 B sampled peak |
| Unpinned public-point solver | `BOUNDED_UNKNOWN`, 180.024701 s, 296,337,408 B sampled peak |
| Unpinned actual restart rows / parent exit | 601 / `WALL_CAP`, exit `-9` |

The pinned [model audit](control_solver_audit.json) independently parses
all returned literals and every XCNF row. The unpinned
[query receipt](query_result.json) retains solver stdout/stderr hashes,
terminal absence, exact elapsed interval, RSS sample, and parent stop;
its [audit](query_audit_result.json) verifies the frozen identities and
restart count. Formula construction and solver search were run in separate
processes, so they are stage costs rather than a complete single-target
online interval. Local CPU times are exploratory without host isolation.

The contrast between a 0.255-second pinned solve and active unpinned search
at 180 seconds puts the remaining work in **target-conditioned selection of
source and root families**, rather than forward arithmetic evaluation after
those choices are known. The next method must reject whole families while
at least two internal sums remain unresolved; adding more source states or
projecting this circuit to N131 before that gate would not meet the frozen
one-worker, 600-second, 4-GiB promotion rule. Any extended circuit must
also cover the identity and zero-`x` exceptional sums. The source-bound
N41 exact join remains the comparison for full search work.

The [proof map](PROOF_MAP.md) gives the written root derivation, a checked
Lean structural soundness lemma, and the concrete arithmetic and circuit
formalization obligations that remain open.

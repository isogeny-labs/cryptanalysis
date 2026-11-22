# Complete XOR-interface peel for the frozen N131 public point

All **208,783 native XOR rows** in the archived Q1358 d10/m15 public-point
formula peel on variables outside the first three leaf-code words and the
two-bit endpoint selector. No row remains. Consequently, the native XOR
equations alone accept every assignment to those 32 interface bits, with
the formula's true variable fixed to one. A target-conditioned rejection
predicate on this interface must also use the formula's nonlinear CNF
constraints.

## Exact instance and experiment

The curve ID is `EC1N131Ckb1heb5f1998f20b`; the single public-point
workload ID is `3c1992b7c92f`. The official-Q XCNF SHA-256 is
`0a2f4b3e3acc8e26049921567b3c3b04b2a1eace4e86ccb8a193bd4cca29fd41`.
The checked Sage [mapping audit](mapping.json) rebuilt the source formula
and identified leaf-code variables 2–31, endpoint-selector variables 1855
and 1856, and constant-true variable 1. The [protocol](protocol.json) fixes
that interface and all source hashes before the peel.

For each native XOR row, [peel.py](peel.py) tracks variables outside the
interface. Whenever one such variable occurs in exactly one active row,
that row can be solved for the variable and removed. The algorithm repeats
until no degree-one variable remains. In this run it removed every row;
none was supported only on the interface. The [independent audit](audit.py)
used a separate LIFO elimination order, removed every row again, and solved
the rows in reverse for three frozen random interface assignments. It then
checked every one of the 208,783 original signed XOR records for each
assignment.

| Quantity | Producer | Independent audit |
| --- | ---: | ---: |
| Native XOR rows | 208,783 | 208,783 |
| Rows peeled | 208,783 | 208,783 |
| Residual rows | 0 | 0 |
| Full signed-XOR assignment replays | — | 3 |
| Script wall time | 0.768 s | 1.199 s |
| Peak RSS | 123,912,192 B | 164,806,656 B |

The one-worker producer completed within the frozen 600-second and 4-GiB
limits. The [read-only verifier](verify.py) checks the sources, interface,
result, independent replay and Lean receipts. A full peel proves that the
noninterface coefficient matrix has full row rank: in each active system,
the selected pivot column appears in exactly one remaining row. Reverse
substitution therefore satisfies any right-hand side induced by an
interface assignment.

## Claim boundary and next method

This result is about the native XOR subsystem. The archived XCNF also has
225,092 CNF clauses encoding nonlinear operations and exact factor-base
membership; those clauses can restrict or reject a prefix. The earlier
[three-leaf panel](../n131_phi_three_leaf_prefix_20261018/RESULT.md) fixed
16 ordinary prefixes in that full formula and each reached its 25-second
cap without a terminal decision. The prior fill-limited XOR projections
used different precomputation points and also reached their separate
580-second solver caps.

The next gate should derive a **sound nonlinear** constraint from one or
more partial-chain multiplication relations, involving the public target
and several leaf or pair sums. Freeze a planted witness and ordinary prefix
panel, verify every rejected prefix against the original formula, and
measure constraint construction plus rejection cost before another full
N131 query. Exact XOR-only projection onto these prefix variables is now
settled by this complete peel.

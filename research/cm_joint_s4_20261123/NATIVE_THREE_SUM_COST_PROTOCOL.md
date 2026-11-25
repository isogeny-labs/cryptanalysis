# Frozen same-target native S4 cost screen

## Amendment and question

This is an explicit amendment to the stopping rule in
[NATIVE_THREE_SUM_PROTOCOL.md](NATIVE_THREE_SUM_PROTOCOL.md).
That rule stopped after a native endpoint failed to increase
three-sum support. A lower hit rate can still be offset by a cheaper
coordinate solver. The P29 [same-point full-cost control](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/research/isogeny_relation_yield_scan_20261016/graph_native_point_control_20261124/complete_cost_control/REPORT.md)
has an example of that direction in its measured core time, without
attributing the difference to CM. This new screen therefore compares
the two native bases' **solve cost** on identical target points. The
earlier yield result and protocol remain intact. [pcc:unverified]

## Frozen instance and sample

Use the degree-five horizontal pair `E:y²=x³+4x+10` and
`E':y²=x³+888x+852` over `F_1009`, both of prime order `1069`,
with Sage's first degree-five edge. Use each curve's first four
liftable integer `x` values and both signs, exactly as in the
native-yield census. Fix `G=E.gens()[0]`, `Q=[271]G`, and Python
`random.Random(20261125)`. Draw `(a,b)` with `a` uniform in
`[0,1068]`, `b` uniform in `[1,1068]`; retain the first 64 nonzero
points `R=[a]G+[b]Q`. Use `phi(R)` on the endpoint. Keep the natural
stream, including failures; do not balance or select positives.
[pcc:unverified]

For each query, calculate exact signed three-sum membership from the
eight-point source and endpoint bases. Build the source and endpoint
S4 systems using the existing `panel.py` implementation and four
base-x roots per arm. Solve each system seven times, interleaving a
deterministically shuffled arm order per row and repeat. Retain every
solve wall time, build wall time, algebraic-closure satisfiability
verdict, and exact rational-point truth. Report all disagreements:
S4 Gröbner consistency over `F_1009` is not by itself a rational
witness. [pcc:unverified]

The primary cost comparison is the sum of per-query median Gröbner
solve times across the identical 64 targets, with map construction
and per-query builds reported separately. If either arm has a truth
mismatch, the measured times are only equation-system components,
not a valid relation-oracle throughput. No memory, independent host
repeat, full rank collection, descent, or rho timing is part of this
panel. It cannot establish an end-to-end speedup. [pcc:unverified]

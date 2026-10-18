# One global valid-code norm classifies the N41 two-pair source

**A single target-conditioned polynomial GCD per residual recovered the
archived N41 W11 code pair `(253,63)` and returned degree zero on all 24
frozen ordinary residuals.** The 25-row checked-Sage run completed in
**56.703 s** parent wall with **337,674,240 B** sampled combined peak RSS,
within one worker, a 120-second child alarm, a 125-second parent cap and
4 GiB. Every root set agrees with the prior independent native census of
all `281²` valid-code pairs per residual.

## Exact operation

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[u]/(u^41+u³+1)`, with `y²+xy=x³+1`. The W11 source has 281 valid
codes and distinct rotated products `p_c`, `q_c` in its first and second
pair slots. For target residual `T`, let `F_T(X,Y)` be the frozen 13-term
bidegree `(4,4)` pair resultant. Form

`N_T(X)=∏_{c valid} F_T(X,q_c)` and `A(X)=∏_{c valid}(X+p_c)`.

The first polynomial has degree 1,124 on every frozen residual; the
second is a target-independent degree-281 source vanisher. A root of
`gcd(N_T,A)` is exactly a valid first product for which some valid second
product makes the resultant zero. Root localization returns its code,
after which evaluating its 281 quartics returns the second code. The
[proof map](PROOF_MAP.md) gives the finite-product Lean theorem and the
remaining concrete polynomial-GCD formalization obligation. The
resultant itself is an exact necessary two-pair relation condition under
its prior split-quadratic hypotheses; every returned code pair is checked
against the archived signed curve-sum replay.

The positive residual `(1434452595080,1460136977354)` comes from the
independently replayed unpinned N41 public relation. The 24 controls are
frozen public-point-derived residuals from the same source panel. The
[protocol](protocol.json) binds the source coefficient file, checked Sage
runtime, exact command, targets, worker count and caps. `candidate_id` is
null while this is a point-decomposition component.

| Frozen panel | Global norm/GCD outcome | Independent native census |
| --- | --- | --- |
| Positive residual, index 0 | GCD degree 1; code pair `(253,63)` | Same pair, exact group replay |
| Ordinary residuals, indices 1–24 | GCD degree 0 on every row | No resultant roots in valid-code domain |

Across the 25 target-dependent intervals, quartic construction took
**5.225 s**, balanced norm products **4.789 s**, and GCD plus root
localization **40.968 s**. Their sum plus minor dispatch costs is
**51.047 s**. The reusable source vanisher took **0.111 s**. Median
target interval was **2.040 s**. These measured stage costs are much
larger than the frozen native direct census's roughly 0.01 s per target
row on this small source; the contribution is a whole-source algebraic
operation with a different scaling path, not a measured N41 wall win.

The first `python3` wrapper invocation failed before worker launch because
that interpreter lacked `psutil`; [attempt0.json](attempt0.json) records
`PRODUCER_FAILURE`. The first completed implementation scanned all 281
first products after GCD. The second used the GCD degree and direct linear
root when possible. Both completed two residuals and are preserved as
v1/v2 artifacts. The third, identical algorithm to v2, completed all
25. [verify.py](verify.py) checks their frozen hashes, caps, outcomes and
every final root set against the independent native census.

The [N131 W20 subset pilot](../n131_w20_global_norm_pilot_20261018/RESULT.md)
measures this operation on the actual challenge field. Its larger-source
wall and memory determine whether a packed or factored kernel is needed
before attempting the full 132,045-code source. A complete relation query
would also have to charge every target-derived residual and independently
replay signed source points and distinct folded columns.

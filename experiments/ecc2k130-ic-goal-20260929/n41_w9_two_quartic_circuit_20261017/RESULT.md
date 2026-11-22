# A compact characteristic-two Bezout gate for the N41 five-pair source

## Contribution

A symmetric four-by-four Bezout determinant eliminates the shared 41-bit intermediate reciprocal from the last two N41 W9 pair equations while keeping all five source codes and the preceding reciprocal free. Its characteristic-two evaluation uses seven diagonal terms and one squared three-term pairing. The resulting full five-pair Boolean circuit has **148,526 variables and 409,826 total constraints**, compared with 223,299 and 706,619 for the prior exact joint-residual BDD on the same public point and source. These are reductions of **33.49% in variables** and **42.00% in constraints** for the joint representation.

The exact quartic Bezout value agreed with Sage's matrix determinant and polynomial resultant on a frozen panel: one archived relation gave zero and all 32 source-valid reachable controls gave nonzero values. The emitted Boolean circuit reproduced all 33 decisions and passed a complete positive assignment check. Its ordinary one-worker query is recorded separately below.

## Method and exact instance

The field is `GF(2)[u]/(u^41+u^3+1)` and the curve is `y²+xy=x³+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`. The public point is `Q=(1936680952394,910597499030)` with reciprocal `t=1988710223364`. The five aligned W9 source-pair rotations are `(0,0,12,12,24)`; each has 71 allowed codes and four signed states per code. The component has `candidate_id: null` while its full IC relation, rank, linear-algebra, and target recovery pipeline remains unspecified.

Let `f(w)=R(w;z,p3,H3,C3)` and `g(w)=R(w;t,p4,H4,C4)` be the two exact quartics defined and checked in the [preceding result](/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/n41_w9_two_quartic_resultant_20261017/RESULT.md). Write their coefficients in ascending powers as `f0,...,f4` and `g0,...,g4`, and set `k_mn=f_m g_n+f_n g_m` for `m>n`. The Bezout matrix is

```text
[ k10       k20          k30          k40 ]
[ k20   k21+k30      k31+k40         k41 ]
[ k30   k31+k40      k32+k41         k42 ]
[ k40       k41          k42          k43 ]
```

Over characteristic two its determinant is `d0 d1 d2 d3 + Σ_{i<j} B_ij² d_k d_l + (B01 B23+B02 B13+B03 B12)²`, where `d_i=B_ii` and `{k,l}` complements `{i,j}`. The [Lean module](BezoutDet.lean) checks both the quartic Bezout quotient and this determinant reduction for an arbitrary commutative ring with explicit characteristic-two hypothesis. The classical determinant-resultant identity is stated as Lemma 2.24 in [Constant-Depth Arithmetic Circuits for Linear Algebra Problems](https://epubs.siam.org/eprint/3RADN6DUV6MDWSDXSKBP/full); the [proof map](PROOF_MAP.md) records the remaining Lean bridge and the concrete curve assumptions.

For the quotient identity, expand `f(X)g(Y)+f(Y)g(X)` by unordered exponent pairs `(m,n)`. Each coefficient is `k_mn`, and `(X^mY^n+X^nY^m)/(X+Y)` is the finite sum `Σ_{r=0}^{m-n-1} X^(m-1-r)Y^(n+r)` for `m>n`; collecting terms gives the displayed matrix. For the determinant, inverse permutations have equal products and cancel in characteristic two. The surviving involutions are the identity, six single transpositions and three double transpositions; the latter form the squared three-term pairing. This proves the short formula used by the Boolean builder. The cited Bezout determinant identity then identifies its zero set with a common quartic root under the recorded degree conditions.

## Frozen arithmetic and circuit checks

The [Sage protocol](bezout_protocol.json) pins its 33-row panel, field/curve source, fixture, script, prior result and checked [runtime receipt](sage_runtime_info.json). The [Sage result](bezout_result.json) reports 1/1 positive and 0/32 control zeros, with equality to Sage's ordinary matrix determinant and polynomial resultant on every row. Arithmetic time was **2.595 s** and self peak RSS **225,525,760 B**, outside launcher setup.

The [build protocol](build_protocol.json) pins the complete builder dependency graph, panel and arithmetic audit before construction. Its [receipt](build_result.json) records 33/33 correct circuit decisions, a complete satisfying assignment for the archived relation, and these ordinary-host diagnostic measurements:

| Formula | Variables | CNF clauses | Native XOR rows | Total constraints | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frozen five-pair base with explicit `w` | 123,218 | 323,673 | 15,811 | 339,484 | 10,757,041 |
| Prior exact joint-residual BDD | 223,299 | 690,808 | 15,811 | 706,619 | 18,070,603 |
| Bezout elimination with free codes | **148,526** | **391,183** | **18,643** | **409,826** | **13,285,051** |

The builder used 129,802 AND gates and 175,636,480 B peak self RSS. Its 43.486 s complete wall includes 34.318 s for the 33 panel assignment replays; the other recorded phases sum to 9.168 s. The [read-only verifier](verify.py) checks all frozen hashes, XCNF counts, Lean output, and that none of the 81 code/`z` input wires has a unit clause. These are circuit and correctness diagnostics on the ordinary host.

## Bounded ordinary query

The [query protocol](query_protocol.json) fixes the public point and formula, exact CryptoMiniSat binary, one solver thread, a 590-second solver limit, a 600-second parent wall cap and 4-GiB sampled combined-RSS cap. No code or reciprocal input is supplied from the archived witness. A SAT model, if produced, is frozen and independently replayed against all five signed source-pair states by [Sage model replay](replay_model_sage.py) before counting a relation.

The [query receipt](query_result.json) records `BOUNDED_UNKNOWN`, `WALL_CAP`: the parent stopped the solver at **600.074 s** with no SAT, UNSAT or INDETERMINATE terminal line. It sampled combined RSS 5,795 times, with a peak of **317,734,912 B** and no monitor error. The last flushed restart line was restart 486 at approximately 161,000 conflicts; it is search progress, not a relation-yield measurement. The solver stderr is empty, and the raw stdout/stderr hashes are retained. The conservative assembled target-dependent stage total is **643.559 s**, comprising the 43.486 s complete circuit build and the 600.074 s query. Launcher checks and process startup are outside those intervals. The ordinary-host result is censored; it does not select a faster IC pipeline.

## Second iteration: affine geometry of the fixed-code fibers

The prior independently Sage-replayed joint support has 79,424 usable `(w,z)` rows. The [frozen affine census](affine_result.json) groups them by the two final source codes and measures the GF(2) affine rank of their `z` coordinates. Exactly **77 of 5,041** code pairs are excluded by column collisions; every other pair has 16 distinct `z` coordinates and **affine dimension 15**. An [independent Sage matrix-rank replay](affine_audit_result.json) reproduced all **4,964** ranks from the 79,424 frozen rows. The arithmetic intervals were 0.683 s for the integer-bit census and 15.262 s for Sage; the latter used the checked launcher and runtime receipt. The first Python attempt computed the ranks but failed while writing its receipt because of a variable-name error; its [source, protocol and failure record](affine_attempt1.json) are retained as `PRODUCER_FAILURE`.

This census closes the proposed shortcut through a low-dimensional affine span *within each fixed code pair*: each 16-point fiber has the maximum possible affine rank. It does not exclude nonlinear constraints or relations shared across different code pairs. The next discriminator is a source-bound construction of those lower-degree shared constraints or a circuit propagation improvement that makes the exact Bezout gate decisive before the full first-three-pair norm search. Freeze a fresh N41 ordinary query and project its N131 size before promotion; the present capped query does not pass that gate.

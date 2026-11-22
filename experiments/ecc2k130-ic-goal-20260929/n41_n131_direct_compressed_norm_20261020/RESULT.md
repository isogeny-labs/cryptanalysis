# Direct compressed recurrence for affine source-block norms

The four-direction N131 norm can be built directly as a quartic in its
linearized block invariant. A paired checked-Sage run measured **0.318 s**
and **0.218 s** for this construction on the two frozen N131 target laws,
against **69.50 s** and **127.47 s** for expansion in the original source
coordinate. Each pair was checked coefficient-for-coefficient in the
original bivariate ring. These are ordinary-host stage measurements with
method order reversed across targets; the observed ratios were 219 and
585. The algorithm removes most of the norm construction cost while
preserving every tested exact block decision.

## Recurrence

Let `Y=L_B(p)` for an existing additive source block `B`, and let
`δ=L_B(b)` for a new independent direction `b`. Put `Z=Y²+δY`, the
invariant of the doubled block. Any current quartic `F(Y,q)` has the
unique form `U(Z,q)+Y V(Z,q)` with `deg_Z U≤2` and `deg_Z V≤1`. Its
translated norm is

`F(Y,q)F(Y+δ,q)=U(Z,q)²+δU(Z,q)V(Z,q)+ZV(Z,q)²`.

The implementation updates only five polynomials in `q` and the
linearized coefficients of `L_B`. It never constructs the intermediate
degree-64 polynomial in `p` during search. The explicit formulas and
the structural norm implication are proved in
[QuadraticBlockNorm.lean](QuadraticBlockNorm.lean) over an arbitrary
characteristic-two commutative ring. The [proof map](PROOF_MAP.md) records
the concrete field and curve bridges.

## Frozen controls and measured screening

| Field and target law | Width | Tested left prefixes | Right source dimension | Exact GCD result | Median GCD time |
| --- | ---: | ---: | ---: | --- | ---: |
| N41 independently replayed public-relation residual | 4 | all 16 | 8 | Prefix 14 degree 1; other 15 degree 0 | 0.186 s |
| N131 constructed positive | 4, 5, 6 | 0 and 1 at each width | 32 | Prefix 0 degree 1 at each width; prefix 1 degree 0 | 2.17, 5.63, 15.14 s |
| N131 ordinary frozen public point | 4, 5, 6 | 0 and 1 at each width | 32 | Both prefixes degree 0 at each width | 1.17, 3.63, 25.44 s |

Every specialized norm was checked against an independent product of
all `2^width` quartics. The N41 all-prefix decisions and N131 width-four
decisions also match the preceding expanded-norm receipts. At widths
four, five, and six the compressed coefficient supports contain 258,
514, and 1,026 terms, respectively. The full N131 sampled run took
110.174 s with 287,916,032 bytes self-reported peak RSS. The N41 run
took 3.868 s with 240,795,648 bytes self-reported peak RSS. These are
component measurements on an ordinary host, not isolated online DLP
comparisons.

The exact N131 field is `GF(2)[u]/(u^131+u^13+u²+u+1)` and curve
`y²+xy=x³+1`, ID `EC1N131Ckb1heb5f1998f20b`. Its W33 source has 32
free canonical code bits, seed mask 898618, and pair rotations `(0,18)`.
The constructed positive uses codes `(3,16722)`. The frozen public point
is `(877610862732227974378969808549299291499,
2063336771837286479337213121437715536874)`.
The N41 control uses `EC1N41Ckb1h7d5e80d3c4d0`, field polynomial
`u^41+u³+1`, four variable code directions `[2,0,1,3]`, and source
codes `(228,60)`. The component has `candidate_id: null` because a
complete relation collector, factor-base log system, target descent, and
single-target comparison have not been specified as one candidate.

The right-subspace GCD is now the main measured cost. Linear projections
from the two sampled public prefixes give about **10.0**, **15.5**, and
**54.1 single-worker years** for widths four, five, and six across all
`2^(32-width)` N131 left prefixes, before source validity or later IC
phases. These are extrapolations from two fixed prefixes per width, not
full-scan measurements or distribution estimates. The recurrence is
useful inside a larger joint constraint, but scanning one left family
block by block does not meet the 600-second N131 relation gate. The
next experiment must bind at least two still-free outer source families
to the public target before enumerating residuals, and compare its
charged whole-family rejection against this exact GCD baseline.

## Evidence and replay

`n41_protocol.json`, `n131_protocol.json`, and
`build_bench_protocol.json` froze source hashes, exact inputs, worker
count, caps, and method order before their runs. The checked Sage
launcher wrote [sage_runtime_info.json](sage_runtime_info.json) before
measurement. The source-bound wall caps were 120, 300, and 240 seconds;
all completed within cap. The scripts did not enforce an RSS watchdog,
so their peak figures are observations rather than a 4-GiB compliance
certificate for the eventual relation gate. Every result has
`candidate_id: null` and retains its protocol hash.

Run `python3 verify.py` here to audit hashes, statuses, earlier direct
norm decisions, exact-product flags, paired coefficient identities, and
Lean axiom output. Regeneration needs a fresh artifact directory because
producers require result files to be absent. All Sage jobs must launch
through `/Volumes/SSD990/cryptanalysis/sage -python`.

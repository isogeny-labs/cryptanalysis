# Affine-block norm compression and N131 transfer

The exact quartic resultant for two source products admits a reusable
left-block norm. For a four-direction product subspace `B`, its 1,386-term
expanded norm equals a 258-term polynomial in the degree-16 linearized
vanishing polynomial `L_B(p)` and the right product `q`. This identity was
checked coefficient-for-coefficient in the N41 and N131 fields. The N41
source control retained exactly the prefix containing its independently
verified public relation. The N131 constructed control retained its known
source block; eight frozen blocks of the ordinary N131 public-point
resultant each had exact right-subspace GCD degree zero.

## Construction and proof

For a two-product eliminant `H(p,q)` and an additive source-product block
`B`, define `N_B(p,q) = ∏_{b∈B} H(p+b,q)`. Every translation `t∈B`
permutes these factors, hence `N_B(p+t,q)=N_B(p,q)`. The monic polynomial
`L_B(p)=∏_{b∈B}(p+b)` is additive. Over the coefficient field `F(q)`, the
invariant ring is `F(q)[L_B(p)]`: divide an invariant polynomial by
`L_B`, observe that its remainder is invariant, and subtract the remainder
at zero. The difference has all `|B|` elements of `B` as roots but degree
less than `|B|`, so it is zero. Repeating the division gives the claimed
representation. For a four-dimensional block, `deg_p N_B=64` and
`deg L_B=16`, yielding `N_B=Σ_{i=0}^4 A_i(q)L_B(p)^i`.

The producer forms `L_B` by `L_new(X)=L(X)^2+L(b)L(X)` and forms the norm by
`N_new(p,q)=N(p,q)N(p+b,q)`. It extracts `A_i` by descending powers of
`L_B` and asserts zero residual. For each tested prefix it compares the
compressed specialization to an independent 16-factor product. The
right-subspace test computes `gcd(N_B(p_base,q),L_R(q))`. At N131 the
degree-`2^32` polynomial `L_R` is evaluated modulo the degree-64 norm
through the same linearized recurrence; it is never expanded.

`AffineNorm.normFn_translate_span` is a checked Lean 4 theorem for the
full binary-span translation symmetry, with arbitrary characteristic-two
commutative ring, basis list, and base function. The polynomial invariant
ring bridge and concrete finite-field coefficient identity remain Sage
certificates; see [PROOF_MAP.md](PROOF_MAP.md).

## Frozen inputs and measured diagnostics

| Field and target law | Block test | Norm build | Exact screen | Result |
| --- | ---: | ---: | ---: | --- |
| N41, independently replayed ordinary public relation residual, W9 source | All 16 four-bit prefixes, eight-bit right source | 1.423 s | 16 exact GCDs within 7.210 s total | Prefix 14 alone has degree 1 |
| N131, W33 constructed positive | Eight frozen four-bit prefixes, 32-bit right source | 28.571 s | Median GCD 1.749 s | Prefix 0 has degree 1; seven have degree 0 |
| N131, W33 ordinary frozen public point | Same eight prefixes | 30.243 s | Median GCD 1.212 s | All eight have degree 0 |

The N131 field is `GF(2)[u]/(u^131+u^13+u^2+u+1)`, curve
`y²+xy=x³+1`, curve ID `EC1N131Ckb1heb5f1998f20b`. The two source
products use rotations 0 and 18; the constructed positive's source codes
are `(3,16722)`. The N41 source control uses
`EC1N41Ckb1h7d5e80d3c4d0`, polynomial `u^41+u^3+1`, source-product
directions in code-bit order `[2,0,1,3]`, and known code pair `(228,60)`.
The eight N131 prefixes were fixed as `[0,1,2,3,5,7,11,13]` before the
run. Each prefix covers 16 left source codes. The right-subspace GCD
includes all `2^32` N131 right source codes algebraically, though a root
would still need a curve-point witness check before promotion to a
relation. `candidate_id: null` because this remains a point-decomposition
component, not a complete IC candidate.

The N41 compressed norm has coefficient supports `65,63,65,62,3` for
powers zero through four. Its 16 compact specializations had median
0.0219 s, versus 0.0210 s for direct 16-quartic products; the median exact
GCD is 0.1510 s. These timings are ordinary-host stage diagnostics, not
Tier 1 online DLP measurements. The N131 sampled run took 86.933 s total,
with 284,213,248 bytes maximum reported RSS. Its protocol declared one
worker, a 180-second wall cap and 4 GiB memory ceiling; the script enforced
the wall cap but did not implement a memory watchdog.

The direct four-bit blocking does not meet the W33 scan-cost gate: there
are `2^28` left prefixes, and multiplying the measured median 1.212 s
public-point GCD by this count gives about 10.3 single-worker years,
before source validity, rank, linear algebra or target descent. This is
a linear extrapolation from eight fixed prefixes, not a full-run
measurement. The next design step is a joint constraint on **two or more
unfixed left-code blocks** or a right-subspace rejection cheaper than the
degree-64 modular GCD; a larger version of this one-block scan alone has
no measured route to the N131 goal.

## Receipt sequence and replay

The first frozen N41 script asserted that the positive root belonged to
the width-zero singleton. Its exact-product equality passed, then the
positive-scope assertion failed because code 228 enters at width one.
`first_attempt_failure.json` retains that status and protocol hash. The
frozen retry passed exact-product and GCD checks at widths zero through
four; the positive-root condition was applied at widths one through four.
The compression and N131 runs have separate frozen protocols and hashes.

Run `python3 verify.py` here to check all source hashes, protocol hashes,
terminal statuses, sampled rows and Lean axiom output. New Sage executions
must use the checked repository launcher, for example:

```sh
/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/n131_transfer_sage.py
```

The scripts require their output files to be absent, so regeneration uses
a fresh copy and freshly frozen protocols. The saved
`sage_runtime_info.json` records the accepted Sage installation before
these measured jobs. The original protocols record their first execution
paths under `/private/tmp`; `verify.py` maps those paths to this copied
artifact directory without changing their hashes.

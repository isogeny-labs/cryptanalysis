# Public-fixture audit of three p+1 leads

Date: 2026-11-25. Scope: the two pasted attachments supplied in this task,
the cited published constructions, and exact local Sage calculations. All
local observations below have **producer-only standing** `[pcc:unverified]`;
the replay is a check, not an independent signed PCC verdict.

## Reproduce the local calculations

```sh
sage -python research/p1_smoothness_leads_20261125/verify.py
```

The command prints the committed [`run.json`](run.json). It uses SageMath
10.10.rc0, field characteristic 10007, and exact arithmetic. The source and
output SHA-256 values at this run are:

```text
f2ae4481f746816e728e76a24d22c5587b7a056db73cfe8aca79eccf4643319a  verify.py
e95a79a2a8d87f49cd753f089aa063fe932388a051bd36e513f4a3baf6499122  run.json
```

The `msolve` parametrizations are stored as `.out.gz` files. The
[post-run archive amendment](OUTPUT_ARCHIVE_AMENDMENT.md) explains the
lossless encoding change; `output_archive.json` records each original
uncompressed SHA-256. Run `sage -python
research/p1_smoothness_leads_20261125/archive_outputs.py` after generating
all solver outputs to reproduce the committed archive layout.

## Track 1: proposed msolve panel

`msolve` 0.11.0 is installed locally. The requested files
`m4_L20_w5.ms`, `m4_L24_w6.ms`, and `m4_L28_w7.ms` are absent from this
checkout's tracked files, and an exact-name search of the adjacent
cryptanalysis worktrees/artifact directory found none. The attachment supplies
neither their defining systems nor the curve, target, and factor-base seeds.
Consequently the requested maximum Macaulay step degree and matrix time on
those *same systems* have not been reproduced. `[pcc:unverified]`

The nearest published prime-field cost equation is

\[
C=P(p,m)+\frac{m!p}{d^{m-1}}T(E,m,L)+d^\omega,
\]

with factor-base size \(d\), \(m\) summands, and relation-system solver cost
\(T\). This is a partial heuristic model: the paper does not establish the
asymptotic behavior of \(T\). For the first attachment's \(p=15359,d=6\), the
expected attempts to obtain \(d\) relations are 2559.83 for \(m=3\), or
1706.56 for \(m=4\), before multiplying by \(T\). Its displayed two-\(f_3\)
chain has three factor-base coordinates and one target coordinate, hence uses
\(m=3\) in this model. These are derived counts, not timed costs.

Source: [Petit, Kosters, Messeng, §§3.1–3.3 and conclusion](https://christophe.petit.web.ulb.be/files/16PKC_primeECDLP.pdf).

### Independent matched `msolve` pilot at \(p=15359\)

This **does not replace** the missing L20/L24/L28 inputs. The committed
`generate_msolve_pilot.py` freezes \(E:y^2=x^3+2x+8\) of prime order
15581, one target, six
curve-eligible x-roots per arm, and three shared roots that provide the same
known positive relation. The Cayley arm takes the six roots of
\(\operatorname{Re}(X+i)^6-15213\operatorname{Im}(X+i)^6\); the comparison
arm replaces the other three roots with a seeded selection outside that coset.
The generated input files, fixture JSON, compressed raw `msolve -v 2` logs, and solver
outputs are committed beside this report. `[pcc:unverified]`

```sh
sage -python research/p1_smoothness_leads_20261125/generate_msolve_pilot.py
/usr/bin/time -p msolve -f research/p1_smoothness_leads_20261125/pilot_cayley.ms -o research/p1_smoothness_leads_20261125/pilot_cayley.out -v 2 > research/p1_smoothness_leads_20261125/pilot_cayley.log 2>&1
/usr/bin/time -p msolve -f research/p1_smoothness_leads_20261125/pilot_matched.ms -o research/p1_smoothness_leads_20261125/pilot_matched.out -v 2 > research/p1_smoothness_leads_20261125/pilot_matched.log 2>&1
gzip -n -9 research/p1_smoothness_leads_20261125/pilot_cayley.log research/p1_smoothness_leads_20261125/pilot_matched.log
```

Both arms gave ideal degree 6. Parsing every F4 round in the raw logs gives
194 rounds per arm with **identical** ordered tuples of step degree, selected
pair count, outstanding pair count, matrix rows, and matrix columns. Their
maximum step degree was 10. Reported overall solver times were 0.09 s
(Cayley) and 0.09 s (comparison), below a useful timing resolution and from
one run each. This pilot supports a finite, matched **null structural
observation**, not an asymptotic rank theorem or a timed speedup.
`[pcc:unverified]`

### Eight-target frozen follow-up

The [frozen protocol](PANEL_PROTOCOL.md) and `panel.py` were committed before
execution. The run retained all 16 inputs, outputs, compressed logs, and
`panel/summary.json`. `validate_panel.py` separately enumerated every
three-point decomposition with the curve group law and checked the solver
input/output/log hashes; see `panel_validation.json`. All 16 processes exited
zero, and all four predefined positive controls produced solutions in both
arms. `[pcc:unverified]`

| Target | Cayley / matched group-law decompositions | Cayley / matched F4 rounds | Geometry equal? |
|---|---:|---:|:---:|
| shared `+++` | 6 / 6 | 194 / 194 | yes |
| shared `-++` | 6 / 6 | 194 / 194 | yes |
| shared `+-+` | 6 / 12 | 194 / 164 | no |
| shared `++-` | 6 / 12 | 194 / 164 | no |
| scalar 1 | 0 / 0 | 22 / 22 | yes |
| scalar 137 | 0 / 0 | 22 / 22 | yes |
| scalar 271 | 0 / 0 | 22 / 22 | yes |
| scalar 997 | 0 / 0 | 22 / 22 | yes |

Every arm reached maximum F4 step degree 10. The two geometric differences
coincide with **six additional valid decompositions** in the matched-root arm;
the independently enumerated counts equal `msolve`'s ideal degrees 6 and 12.
Thus these two cases do not isolate a Cayley-specific solver effect. The six
equal-count pairs have identical ordered F4 round geometry. Wall times remain
single-run, subsecond diagnostics and are not used for a speed claim.
`[pcc:unverified]`

### Equal-decomposition confound check

The [balanced protocol](BALANCED_PROTOCOL.md) and `balanced_panel.py` were
committed before eight further solver calls. The comparison base kept the
three shared roots and used eligible extras `[5118,1869,3300]`, selected by
a deterministic group-law filter before solver execution. All eight targets
then had exactly the same decomposition counts in the two arms: six on each
positive control and zero on each scalar control. `[pcc:unverified]`

All eight balanced solver calls exited zero. The independently re-enumerated
group-law counts equaled the balanced arm's ideal degrees, and every ordered
F4 round-geometry sequence matched the already retained Cayley reference:
194 rounds for each positive control, 22 for each zero-relation control,
maximum step degree 10 throughout. `validate_balanced.py` checks the
compressed-log, input and output hashes and recomputes these comparisons;
see `balanced/summary.json` and `balanced_validation.json`.
This is a finite null structural result under equal solution counts. It does
not establish a general invariant, a full index-calculus cost, or a timing
advantage. `[pcc:unverified]`

## Track 2: twisted Edwards symmetry

For \(a=3,d=2\) over \(\mathbb F_{10007}\), the attachment's displayed
\(S_3^{\rm TE}\) vanishes on the checked relation with y-coordinates
\((4,8,5929)\). As written, it has **nine** monomials, not eight. Its resultant
\(S_4^{\rm TE}\) has 57 monomials in Sage's expanded representation. We checked
two even-sign substitutions symbolically; a single-sign substitution changes
the polynomial. These are exact assertions in `verify.py`, not an \(F_4\)
timing result. `[pcc:unverified]`

The twisted Edwards y-coordinate summation polynomial, the even signed
permutation group \(D_n\), and invariant-coordinate Gröbner reduction already
appear in [Faugère, Gaudry, Huot, Renault, *Using Symmetries in the Index
Calculus for Elliptic Curves Discrete Logarithm*, §§2.3 and 4.1](https://citeseerx.ist.psu.edu/document?doi=f9e44d0863407d01137386b10ef130caef6e4c74&repid=rep1&type=pdf).
Their cost result concerns point decomposition over extension fields and
depends on a regularity hypothesis. A polynomial's group order \(2^{m-1}\)
does not itself imply an eightfold wall-time reduction for an arbitrary
`msolve` input. One must construct the invariant-coordinate system, preserve
the factor-base equations, and measure full solver work on matched inputs.

An odd-order group \(E(\mathbb F_p)\) has no rational point of order two.
Every twisted Edwards model has \((0,-1)\), a rational point of order two.
The attachment's claim that a prime-order curve such as P-256 can acquire
Edwards coordinates over \(\mathbb F_{p^2}\) is also false. Write
\(n=\#E(\mathbb F_p)\) and \(t=p+1-n\). For odd \(p\) and odd \(n\), \(t\)
is odd, and the standard extension-order identity gives

\[
\#E(\mathbb F_{p^2})=(p+1-t)(p+1+t)
=n\bigl(2(p+1)-n\bigr),
\]

which is odd. Hence neither \(\mathbb F_p\) nor \(\mathbb F_{p^2}\)
contains the required two-torsion point. For a short Weierstrass model,
its two-torsion polynomial \(x^3+Ax+B\) has no root over \(\mathbb F_p\);
as a separable cubic it is irreducible, so its first roots occur over
\(\mathbb F_{p^3}\). This identifies the first possible extension for
two-torsion, not a guarantee of a twisted Edwards model there. Even after
passing to a suitable extension, one must show that the sign action
preserves the embedded \(E(\mathbb F_p)\) factor base. See
[Bernstein et al., *Twisted Edwards Curves*, §2](https://cr-yp-to.viacache.net/newelliptic/twisted-20080313.pdf)
for the order-two point and
[NIST SP 800-186](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-186.pdf)
for P-256's prime order and cofactor one. The displayed group-order identity
independently checks the quadratic-extension obstruction. `[pcc:unverified]`

## Track 3: isogeny network

The attachment's \(E_0:y^2=x^3-3x+12\) over \(\mathbb F_{10007}\) has order
\(10074=2\cdot3\cdot23\cdot73\), so it does not exercise its claimed
prime-order setting. As a corrected public fixture, `verify.py` uses
\(E:y^2=x^3-3x+7\), order \(10193\) prime. Sage finds five rational prime-degree
isogenies for degrees at most 19: \(7,11,11,19,19\). The dual identity
\(\hat\phi_i\phi_i(R)=[\ell_i]R\) holds on the checked target. `[pcc:unverified]`

For each codomain's coordinate-bound set \(x<250\), the dual pullback sizes
are 262, 258, 256, 276, 262. Their sum is 1314; their actual union has
1246 points. All ten pairwise intersections are nonempty (sizes
6, 2, 2, 4, 10, 16, 10, 12, 6, 6). Hence “the pulled-back bases are disjoint”
is false even on this prime-order fixture. `[pcc:unverified]`

There is a stronger exact accounting rule. If \(n=\#E(\mathbb F_p)\) is prime
and \(\gcd(n,\ell_i)=1\), then \(\phi_i\) is a bijection between the two
groups of rational points. Set \(\mathcal F_i=\phi_i(\mathcal F_0)\) to share
factor-base logarithms exactly. By injectivity,

\[
\phi_i(R)=\sum_j\phi_i(P_j)\quad\Longleftrightarrow\quad
R=\sum_j P_j.
\]

Thus that *exactly shared* construction gives the same decomposable target
set on every curve; it supplies no best-of-\(K\) relation-probability gain.
Coordinate-defined \(\mathcal F_i\) may give different chances, but their
pulled-back union determines the actual unknown count, and each attempted
curve has evaluation and solver cost. The draft's exponents are conditional
on disjoint bases, independent hits, equal solver costs, and uncharged
network construction. They are not a universal lower bound.

### Exact two-summand network census

The [network protocol](NETWORK_PROTOCOL.md) was committed before execution.
`network_hits.py` enumerates the exact two-summand hit sets on the same
prime-order fixture for every rational target in \(E(\mathbb F_{10007})\),
using the smaller coordinate bound \(x<20\). It normalizes each codomain
point back to its unique preimage under \(\phi_i\) by
\([\ell_i^{-1}]\hat\phi_i\). This normalization makes each arm's hit set
comparable on the same base-curve target. The exact counts are in
[`network_hits.json`](network_hits.json). `[pcc:unverified]`

| Arms | Factor-base sizes | True base union | Two-summand hit sizes | True hit union | Independent-hit counterfactual |
|---|---|---:|---|---:|---:|
| Five isogenous curves | 22, 10, 16, 26, 30 | 104 | 237, 51, 129, 339, 451 | 1,161 / 10,193 | 0.113396 |
| Base curve plus five | 22, 22, 10, 16, 26, 30 | 126 | 243, 237, 51, 129, 339, 451 | 1,373 / 10,193 | 0.134533 |

At this bound the five bases are pairwise disjoint, whereas their hit sets
have pairwise intersections of 1 to 15 targets. The network-only union hit
probability is \(0.113902\), close to the \(0.113396\) independent-hit
counterfactual for these unequal arms. It is \(2.574\) times the strongest
single-arm hit probability, while the true factor-base union contains 104
points versus that arm's 30. Every coordinate-bound set contains both \(P\)
and \(-P\); the normalized isogeny pullbacks preserve this pairing. Since the
group has odd prime order and none of these bases contains the identity, the
104 network points form exactly 52 sign pairs, while the strongest arm's 30
points form 15. These are the distinct logarithm variables after applying
\(\log(-P)=-\log(P)\), before any further relation reduction. Thus the
same \(104/30=52/15\) dimension ratio survives the elementary sign
compression. This confirms a finite best-of-five hit gain, but also the
corresponding larger logarithm system. It does not establish
that the network beats selecting its best arm once precomputation, per-arm
solver calls, and linear algebra are charged. The earlier \(x<250\) dual-image
overlap calculation and this normalized-preimage \(x<20\) calculation use
different bounds and set definitions; neither implies universal disjointness
or universal overlap. `[pcc:unverified]`

### Cold relation-rank and same-target descent check

The [cold protocol](COLD_NETWORK_PROTOCOL.md) was committed before the run.
`cold_network.py` constructs one two-summand sum table per arm, collects
known-scalar relations in the fixed scan excluding the target's construction
scalar, compresses \(P,-P\) pairs, solves each full-rank system over
\(\mathbb F_{10193}\), and verifies every recovered base logarithm by scalar
multiplication. The same target is \(R=137G\) throughout; 137 is used to
construct the public fixture and only for final answer verification, not as a
relation. The program's exact output is [`cold_network.json`](cold_network.json).
All six arms reached full rank. `[pcc:unverified]`

| Route | Sign variables | Sum-table additions | Precomputation queries | Target-descent queries | Target shift |
|---|---:|---:|---:|---:|---:|
| Base curve reference | 11 | 253 | 738 | 16 | 15 |
| Strongest isogenous arm | 15 | 465 | 802 | 37 | 36 |
| Five-arm network | 52 total | 1,260 | 6,345 | 9 | 1 |

The network found a target relation sooner online, but its five full-rank
precomputations required 6,345 membership queries versus 802 for the
strongest isogenous arm. Including descent gives 6,354 versus 839 queries
under this fixed scan. The program also charged 1,260 versus 465 group
additions to build the respective sum tables. It checked that the recovered
scalar reproduces \(R\). This is a finite cold-work counterexample to treating
the best-of-five hit probability alone as a speed result. Its sum-table
decomposition oracle is not an F4 solver; isogeny construction/evaluation,
group-point generation, and sparse linear-algebra operation counts are not
included in the two charge columns. The counts therefore do not establish a
general cost ordering or a comparison with rho. `[pcc:unverified]`

For secp256k1, \(\psi(x,y)=(\beta x,y)\) and \(\beta^3=1\) do preserve
\(x^r=1\) exactly when \(3\mid r\). This supplies orbit relations among
factor-base logarithms. It is an instance of the known GLV endomorphism;
an end-to-end index-calculus benefit still needs matched relation and linear
algebra costs. See [libsecp256k1's source explanation of \(\beta\) and
\(\lambda\)](https://github.com/bitcoin/bitcoin/blob/master/src/secp256k1/src/scalar_impl.h)
and [Faugère et al. on orbit reduction](https://citeseerx.ist.psu.edu/document?doi=f9e44d0863407d01137386b10ef130caef6e4c74&repid=rep1&type=pdf).

## Next admissible experiments

1. Obtain the three exact `.ms` inputs or their generator plus frozen seeds;
   record source hashes, curve/target identity, `msolve -v 2` output, wall and
   CPU times, and the same-input reference before comparing regularity.
2. If pursuing Edwards symmetry on a prime-order target, exhibit an
   invariant-coordinate system whose factor-base and descent equations
   retain the sign action over the *original* rational point set. Without
   that bridge, a timing comparison on a different curve tests a different
   problem.
3. For the isogeny network, replace the sum-table oracle with matched native
   decomposition systems, measure per-curve isogeny and F4 costs, and charge
   sparse linear algebra on the same frozen target. The exact base unions,
   hit intersections, and one full-rank relation/descent scan above provide
   controls. Compare cold total work against the single-curve and matched-rho
   references before drawing an end-to-end conclusion.

# Xedni decay leads: evidence ledger and prospective tests

Date: 2026-11-18

Status: research triage for the frozen rank-decay program. No natural
16--32-bit rank panel, Magma cross-check, discovery, or replication result is
reported here. Prior producer results are labeled separately from prospective
hypotheses; neither is a claim that the decay heuristic has been defeated.

## What would count

The primary finite-range claim is about the signed model
`q(p)=kappa*p^beta`, where the JKSST `1/p` scale is `beta=-1`. A mechanism is
interesting only if it survives fresh held-out data and yields a nontrivial
target-bearing relation, not merely a small discriminant, low curve rank, or a
bounded-box relation. The frozen decision additionally requires at least 30
certified nontrivial useful recoveries, useful events at three adjacent sizes
in both discovery and fresh replication, and simultaneous conservative lower
bounds `beta>-0.8` for the separate curve-rank and selected-recovery endpoints
under both unresolved allocations and both denominators. The conditional
Poisson, frozen binomial-cloglog, and cluster-robust sensitivities must all
pass, along with PARI/Magma rank agreement and complete charged work. See
[`PROTOCOL.md`](PROTOCOL.md), [`POWER.json`](POWER.json), and
[`analyze.py`](analyze.py).

Curve rank and selected-point recovery are co-primary but logically separate.
`rank(E(Q))>=r` does not prove that the chosen `r` points are independent; an
exact useful selected-point relation can exist on a curve whose full rank is
at least `r`. The analyzer therefore never converts `CERT_GE` into a recovery
failure. [pcc:unverified]

That is deliberately stronger than finding one surprising curve. A constant
factor in `kappa` does not defeat the decay exponent, and an offline family
search is not an online ECDLP improvement unless its full search cost is
charged. [pcc:unverified]

## Prior evidence already in the workspace

Everything in this section predates the six prospective arms below. It sets
priors and controls; it is not natural rank-decay evidence.

### Boxed-relation sweep: negative evidence for the old lift

The frozen toy sweep scheduled 504,304 rows and retained 500,242 admissible
rows. It found 572 certified bounded-box relations. Of these, 476 were line
relations, three were single-point torsion, and only 96 were non-line. There
were 13 non-line events at `p>=127` and none above `p=4093`. The pooled fitted
signed slope over `p>=127` was `-1.174`; the family slopes were `-1.412`
(`generic`) and `-1.105` (`j0`). At `p=65521`, 150,057 trials produced no
hit. These outcomes support, rather than challenge, `1/p`-scale decay for that
bounded detector.

The pooled Poisson dispersion diagnostics were 2.87 overall, 1.04 for
`generic`, and 4.05 for `j0`. The natural experiment therefore needs fresh
curves, source/prime clustering, and a conservative sensitivity analysis; the
old nominal Poisson intervals are too narrow for two pooled series.

Source: [`../xedni_lift_success_20261112/RESULTS.md`](../xedni_lift_success_20261112/RESULTS.md).

### Higher-point plane cubics: feasibility, not a decay lead yet

The frozen 1,600-row toy panel admitted 1,205 rows and certified 67 rational
relations. Relation rates rose with the number of selected points: 2.80%,
5.16%, 6.16%, and 8.54% for `r=6,7,8,9`. However, the pooled relation count
fell from 32/197 at `p=31` to 3/363 at `p=251`; 44/67 relations had zero target
coefficient, leaving 23 exact target recoveries. Balanced lifts produced
61/596 relations versus 6/609 for wide lifts. This establishes executable
toy feasibility and makes `r=7..9` worth a certified rank test. It does not
measure a slower exponent.

Source: [`../xedni_plane_group_20261117/RESULTS.md`](../xedni_plane_group_20261117/RESULTS.md).

### Local quotients: strong negative controls for incompatible CRT laws

The archived summaries report independence certificates for 20/20 selected
pairs in a small `p=47` population and 9,688/9,688 pairs in an optimized CRT
population. The right inference is narrow: uncontrolled or quotient-
incompatible local laws can force independence. Those rows do not test a
compatibility-engineered reverse-Mestre arm. The prospective local experiment
must compare compatibility, incompatibility, and matched CRT coefficient
growth separately.

Checked summary source: [`README.md`](README.md), “Prior evidence that sets
the bar.” The external lead record named
`LEAD-ICP-char0-lifting-xedni-smoothness` is referenced by several reports but
is not present in this workspace, so it is not treated as independent
evidence here.

### Public selectors and rank-one families: small signals, adverse baseline

The checked summary reports that an integral-slope shift increased exact
`(1,2)` hits from 2 to 6 in 30,008 ordered queries. A nonisomorphic rank-one
holdout found 40 distinct rational-relation queries in 9,875,576 queries, but
the directly testable finite-field relation appeared earlier in every holdout
field. This is enough to justify held-out public-selector controls. It is not
evidence for an online advantage or exponent change.

Checked summary source: [`README.md`](README.md), “Prior evidence that sets
the bar.”

### Lift optimization and target origins: representation mechanisms only

The exact affine-coset optimizer preserves incidence and congruence, and its
frozen `p=67` radius-1/2/4 neighborhood found the same 56-bit discriminant as
Babai radius zero. It did not test point dependence. Likewise, changing the
chord origin transports a relation by an explicit coefficient formula; it
does not create source relation information. The target-origin and origin-
pencil work provides useful recovery/cost controls, but its natural panels
have not run.

Sources:

- [`../xedni_lift_optimizer_20261101/README.md`](../xedni_lift_optimizer_20261101/README.md)
- [`../xedni_target_origin_20261118/README.md`](../xedni_target_origin_20261118/README.md)
- [`../xedni_origin_pencil_20261118/README.md`](../xedni_origin_pencil_20261118/README.md)
- [`../xedni_target_relation_20261118/README.md`](../xedni_target_relation_20261118/README.md)

## Prospective six-arm extension, ranked

The rank is a test priority, not a claimed probability of success. All six
arms are frozen in [`AMENDMENT.md`](AMENDMENT.md); none has natural outcome
data.

| Priority | Arm | Testable hypothesis | Necessary controls | Clean falsifier |
| ---: | --- | --- | --- | --- |
| 1 | M1 normalized-height bank | A constant-size public bank can make `log(abs(Delta_min))/max_i hhat(P_i)` fall with `p`, invalidating the finite-range height-ratio premise and enriching held-out nontrivial useful recovery. | Balanced, random bank member, minimum equation discriminant, minimum global-minimal discriminant, minimum normalized ratio, permuted score; certified maps to minimal models. | No held-out ratio trend, or a trend without replicated useful recovery after bank-search cost. |
| 2 | M2 compatible/incompatible CRT | Quotient-compatible reverse-Mestre residues increase dependence beyond no-local and neutral matched-CRT arms, while deliberately incompatible residues suppress it. | Same source tuple, auxiliary primes, CRT modulus, and candidate budget; `A_none`, strict and `+1/+2` reverse-Mestre, neutral CRT, incompatible control, pairwise-coprime canary. | Compatible arm does not beat neutral matched CRT, or any apparent gain disappears per proposal after rejections/coefficient growth. |
| 3 | M3 public nonlinear selector | A coefficient-independent nonlinear coordinate/chart score predicts nontrivial useful lifts on held-out sources without first finding the finite-field relation. | Fixed `K`, balanced, uniform bank member, permuted score; forbid rank, relation vector, target scalar, and post-relation p-adic defects; direct finite-field relation search first. | No held-out enrichment, only line relations, or direct source search finds the same usable relation earlier/cheaper. |
| 4 | M4 `r=7..9` cubic family | A genuinely nonisomorphic cubic bank crosses the interpolation wall and produces slower useful-recovery decay than `r<=6`. | Prefixes of one ordered nine-point tuple, random cubic, M1 selectors, fixed `K`; certified cubic-to-Jacobian map for every point and origin. | Missing point map, enrichment only in any-of-`K` rather than charged per proposal, zero target coefficients, or no replicated slope change. |
| 5 | M6 public rank-one predictor | A predictor trained only on development seeds can select nonisomorphic low-rank/useful models from public pre-rank invariants on a fresh holdout. | Disjoint train/holdout seeds, random candidate, permuted labels, fixed `K`, all timeouts, and direct source relation testing. | Holdout enrichment vanishes, does not yield target recovery, or direct finite-field testing remains earlier and cheaper. |
| 6 | M5 isogeny neighbors | A small-degree isogeny neighbor with unusually favorable public height/discriminant invariants raises useful-lift yield after transport. | Frozen degrees, every neighbor, explicit `phi` and dual `psi`, coordinate-isomorphic control, source curve, random and invariant-selected neighbor; `gcd(deg(phi),q)=1`. | No invariant/recovery effect after enumeration and maps, or the result is merely an equivalent DLP representation. |

M1 and M2 should be crossed: local conditions could improve quotient
compatibility while making the characteristic-zero coefficients and height
ratio worse. Reporting either marginal contrast alone would hide that trade.
[pcc:unverified]

### M1 certificate and measurement details

For every bank member retain the construction discriminant, global-minimal
discriminant, canonical heights on the certified minimal-model isomorphism,
height Gram matrix, regulator, conductor, and the status of any lower-bound
certificate. Freeze `K` across `p`. Report the selected member, a uniform
member from the identical bank, and a permuted-score winner. A score computed
after rank or relation search is circular and invalidates the row.

The current PARI adapter supplies exact minimal-model maps, discriminants, and
conductor, plus canonical-height and selected height-Gram determinant values
checked at two precisions. Those height quantities are numerical, the selected
determinant is not asserted to be the full Mordell--Weil regulator, and PARI
does not supply the rigorous global minimum-height lower-bound certificate
needed for the strongest interpretation. The adapter records that status as
unavailable rather than promoting the numerical value. [pcc:unverified]

Primary mechanism response:

```text
R = log(abs(Delta_min)) / max_i hhat(P_i).
```

The rank/recovery endpoint remains separate. A smaller `R` without an
invertible target-bearing relation is `MECHANISM_ONLY`.

### M2 compatibility certificate

At every auxiliary prime retain good reduction, exact curve order, incidence
rank, every common quotient order, point images in the quotient, and a
compatibility verdict. Match the compatible, neutral, and incompatible arms
on the same auxiliary primes and modulus. The pairwise-coprime canary checks
the vacuous-common-quotient edge case; it is not evidence that compatibility
was substantively tested. `I_incompatible` and size-matched diagnostic arms
cannot enter the primary estimand.

### M3 public nonlinear construction boundary

A valid selector can use only frozen public coordinates and invariants. It
cannot use a relation vector, a rank result, a target scalar, or a defect
defined only after a relation has been found. The selector must be published
before the holdout and evaluated against a permutation null. Every rational
relation must be reduced and replayed in the named source subgroup. Because a
rational relation necessarily gives a source relation, direct source relation
testing is a mandatory baseline, not an optional diagnostic.

Field omission inside one JSON object is not enough to enforce this boundary:
the complete source record contains private ordered scalars for later replay.
A natural executor must derive a hash-linked redacted public record, launch the
selector/lift/relation proposer in a process that can read only that object,
and give the private source record only to a separate replay evaluator. A
`uses_source_scalars=false` field is an assertion, not an anti-circularity
certificate. [pcc:unverified]

### M4 point-map gate

Ranking a convenient Jacobian without mapping the selected cubic points is
not evidence. Each admitted row needs a certified nonisomorphic cubic, a
cubic-to-Jacobian map, mapped origin, mapped selected points, good reduction,
and source-relation replay. Q-isomorphic duplicates remain charged and are
deduplicated only in the curve-weighted summary.

### M5 transfer obligations

For source subgroup order `q` and isogeny degree `ell`, require
`gcd(ell,q)=1`, trivial kernel intersection on the subgroup,
`psi(phi(P))=[ell]P`, and exact inverse target recovery. Rationally isogenous
elliptic curves have the same Mordell--Weil rank, so an isogeny cannot by
itself create a rank drop; the only plausible mechanism is a better public
representation for a subsequent lift. Neighbor enumeration, maps, rejected
degrees, and duplicates are part of its cost. The companion transfer audit is
[`TRANSFER_ASSESSMENT.json`](TRANSFER_ASSESSMENT.json).

### M6 development/holdout boundary

The predictor is frozen after a named development panel. Holdout labels,
rank-tool output, timeouts, and relation vectors cannot feed feature design or
candidate selection. Report calibration and selection rates, not just the
best selected model. A predictor that finds low rank but not a nontrivial
invertible target relation has not advanced Xedni.

## Exact denominator and censoring controls

Every frozen factor cell is keyed by stage, panel, arm, prime, bit size, curve
family, lift strategy, local profile, and `r`. Its roster must contain exactly
indices `0..planned_trials-1`; missing rows and unknown fields are errors.

For rank, define:

```text
A = certified upper bound < r
G = certified lower bound >= r
U = every straddling, missing, timed-out, failed, or contradictory case
N = A + G + U among admitted ranked configurations
q_min = A/N
q_max = (A+U)/N.
```

The staged tool rule is asymmetric and must remain frozen. A PARI
`CERT_GE` row enters `G` without an unnecessary Magma call. A PARI `CERT_LT`
row enters `A` only after Magma also certifies `<r`. When PARI returns a
certified interval straddling `r`, a compatible Magma interval may resolve
either side. A missing/timed-out PARI result cannot be rescued by Magma alone,
and an unconfirmed PARI low-rank event stays in `U`. Contradictory certified
intervals also stay in `U` and block the decision.

The analyzer also reports `A/N_proposed` and `(A+U)/N_proposed`. Local and
construction rejects are failures per proposal, while certificate failures
remain unresolved. Recovery has an independent three-state certificate;
unknown recovery is not inferred to be failure from exact rank, and unknown
rank is not substituted for unknown replay.

The frozen binomial-cloglog and hierarchical cluster bootstrap are computed by
[`sensitivity.py`](sensitivity.py). The bootstrap
it resamples the three prime clusters within bit-size, then source/curve
clusters within each sampled prime. Its replicate count must be at least
`ceil(2*M/alpha)` to resolve the Bonferroni tail. The artifact is accepted only
when its row-set, protocol, implementation, and trusted-freeze digests match,
its parameters equal the semantic `analysis` section of `FREEZE.json`, and all
reported bounds exactly reproduce. An asserted lower bound is not evidence.

Two global unresolved allocations are not a rigorous slope envelope. For
example, with certified counts `(10,7)` and unknown counts `(90,93)` at
`(p,4p)`, all-failure has `beta=-0.257` and all-success has `beta=0`, but the
mixed allocation `(100,7)` has `beta=-1.918`. Production classification is
therefore hard-blocked until the signed-beta lower bound is minimized over
every per-prime interval `S_i in [A_i,A_i+U_i]` for all three required models.
The two named corners remain diagnostics, not an adversarial proof.

Production is independently hard-blocked until each row is executable-bound
to the frozen roster, prime manifest, stage seed, and the actual raw
rank-adapter and relation-certificate digests. Self-declared JSON identifiers
do not satisfy that provenance obligation.

Production is also hard-blocked until all proposed relations and coexistence
classes are retained under a deterministic any-useful rule. Finding or
rejecting one candidate cannot certify that no other useful relation exists;
without an exhaustive relation-lattice or independence certificate, ranked
non-successes remain `UNKNOWN` rather than negative events.

Report both of these populations:

1. configuration-weighted results, where every admitted configuration counts;
2. distinct-Q-isomorphism-class-weighted results, where repeated models count
   once but their construction cost is retained.

For every candidate-bank panel also report:

- per-candidate rate;
- any-of-`K` rate per source tuple;
- conditional rate among admitted candidates;
- unconditional rate per proposed source tuple;
- the identical quantities for the random and permuted-score controls.

`K` cannot grow with `p` unless that growth is the named estimand and its full
cost is included. Do not discard duplicate curves, duplicate relation vectors,
timeouts, local rejects, or failed lifts from proposal denominators.

## Exact work controls

Charge and retain, per row:

- source-generation candidates;
- local-construction candidates;
- lift candidates;
- rejected and duplicate candidates;
- public group operations, including direct finite-field relation search;
- PARI and Magma rank/descent calls and wall time;
- CPU seconds, peak resident bytes, and retained bytes;
- map construction, isogeny enumeration, height/minimal-model work, relation
  enumeration, scalar recovery, replay, and every failed attempt.

No setup reuse is assumed across fresh source instances. A mechanism lead can
be reported before a cost win, but an end-to-end attack claim needs the total
cost per verified target recovery compared with a matched single-target
Pollard-rho baseline. [pcc:unverified]

## Additional directions reviewed and deprioritized

- **Coordinate-isomorphic lifts alone:** rank is unchanged under Q-isomorphism.
  Keep them as leakage/cost controls, not independent evidence.
- **Relation-biased or rank-biased lift selection:** circular unless the
  relation/rank oracle cost is charged. A public pre-rank selector is M3/M6;
  an oracle selector is only an upper bound.
- **Covers and larger Jacobians:** require explicit forward/recovery maps,
  kernel and exceptional-locus checks, subgroup preservation, and complete
  dimension/genus cost. A larger Jacobian does not erase the source DLP; no
  workspace result supplies the missing advantage certificate.
- **Field extensions:** source coordinates generally force the residue-degree
  cost. Moving the same subgroup to a larger field is a representation change,
  not a rank-decay mechanism.
- **Origin pencils:** the coefficient transport identity is useful for
  recovery enumeration, but transported relations still reduce to public
  source relations. Treat as a costed subroutine inside M3, not a new entropy
  source.
- **More aggressive bounded coefficient search:** the old detector was already
  dominated by line relations. A larger box changes detector power and cost;
  it does not certify curve rank or a slower exponent.

## Stop and escalation rules

Stop an arm as `NULL_IN_SCOPE` after its prospectively powered holdout and
fresh replication fail the named mechanism and useful-recovery endpoints.
Use `BLOCKED` when a required map, rank backend, or certificate is absent.
Use `MECHANISM_ONLY` for an invariant or rank signal without useful target
recovery. Only `REPLICATED_USEFUL_SIGNAL` warrants expanding an arm, and even
that label does not itself classify the primary decay model as defeated.

The highest-value next experiment, if resources permit, is the crossed
M1-by-M2 calibration at 16 and 18 bits with all certificate and work fields
retained. The first scale escalation should occur only after that calibration
shows the tools, denominators, and selectors behave as frozen. No high-bit
sentinel can substitute for the powered discovery/replication decision.

## Primary sources

1. M. J. Jacobson Jr., N. Koblitz, J. H. Silverman, A. Stein, and E. Teske,
   “Analysis of the Xedni Calculus Attack,” *Designs, Codes and Cryptography*
   20 (2000), 41--64, DOI `10.1023/A:1008312401197`, especially Sections 3.2,
   4, 5.1, 5.2, and 5.4; primary PDF:
   <https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf>.
2. J. H. Silverman, “The Xedni Calculus and the Elliptic Curve Discrete
   Logarithm Problem,” *Designs, Codes and Cryptography* 20 (2000), 5--40,
   DOI `10.1023/A:1008319518035`.
3. T. Fisher, “The invariants of a genus one curve,” *Proceedings of the
   London Mathematical Society* 97 (2008), 753--782,
   DOI `10.1112/plms/pdn021`, for the direct ternary-cubic invariant context.

Repository reports cited above are producer artifacts unless they carry a
separate standing claim. Planned, blocked, synthetic, or underpowered work is
not a natural decay result.

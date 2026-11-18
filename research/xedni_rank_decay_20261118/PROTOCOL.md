# Prospective Xedni rank-decay falsification protocol

Date: 2026-11-18

Status: prospectively specified before the scalable generator, rank adapters,
prime manifest, or any natural outcome. No natural row may be generated until
the implementation, exact tool images, source hashes, seeds, manifests, and a
`FREEZE.json` are committed and `scripts/checkpoint.sh gate` exits zero without
a bypass. [pcc:unverified]

## Requested question and claim boundary

Test primes from approximately `2^16` through `2^32`, controlling independently
the public target-independent lifting strategy, `r` (the number of selected
points), and the small-prime conditions in Silverman's original algorithm. The
falsification target is meaningfully slower decay than the finite-range `1/p`
model suggested by Jacobson--Koblitz--Silverman--Stein--Teske (JKSST) Theorem
4.1. A positive result must concern certified selected-point dependence and
useful recovery, not merely a relation found in a bounded coefficient box.
[pcc:unverified]

The theorem is conditional. Lemma 4.1 assumes

```text
log |Delta| >= C1 max_i hhat(P_i)
```

and uses Lang's conjectural height lower bound to obtain an absolute relation
coefficient bound `C2`; the final counting argument is approximately
`(2*C2)^r/p`. The experiment separately tests the finite-range rate and the
height-ratio premise. It cannot refute an unconditional theorem that the paper
does not state. The paper's rough constants are already vacuous at 16--32 bits,
so `DEFEATED_IN_SCOPE` below means the preregistered finite-range model only.
[pcc:unverified]

## Source population and prime manifest

Bit sizes are `b in {16,18,20,22,24,26,28,30,32}`. Before any natural row, a
committed manifest generator derives three distinct `b`-bit primes per size
from master seed `xedni-rank-decay-20261118-v1`. It hashes `seed|b|slot`, maps
the digest to an odd candidate below `2^b`, and takes the first prime at or
below that candidate, rejecting duplicates and values below `2^(b-1)`. Exact
primes and the generator hash are frozen before execution. [pcc:unverified]

Every trial uses a fresh curve. Curve-family strata are `generic`, a
nonsingular `y^2=x^3+a*x+b` with independently sampled residues, and `j0`, a
nonsingular `y^2=x^3+b`. PARI `ellcard`/SEA supplies the cardinality. Points
are sampled using Legendre-symbol tests and Tonelli--Shanks; no `O(p)` square
table or `O(p)` point-count loop is permitted. Orders are certified from the
cardinality and its exact factorization. One ordered maximum-size source tuple
is generated per source instance; smaller `r` arms use frozen randomized
prefixes without outcome-dependent reselection. [pcc:unverified]

## Independent factors

### Point count

The executable short-Weierstrass stratum is `r in {2,3,4,5,6}`. The requested
general-cubic stratum `r in {7,8,9}` remains in the manifest but is blocked
until there is a certified plane-cubic-to-Jacobian conversion and an explicit
map for every selected point. Ranking an unrelated Jacobian model is invalid.
[pcc:unverified]

### Lift strategy

Each source/local instance is paired across:

- `balanced`: least-absolute CRT representatives of point coordinates;
- `wide`: balanced representatives plus independent public multiples of the
  full CRT modulus from `{-1,0,1}`;
- `optimized`: the same balanced incidence coset passed through the existing
  exact LLL, rational-Babai, and bounded discriminant optimizer.

All strategies retain identical residue classes and incidence constraints.
Record coefficient height, discriminant, conductor, `max hhat(P_i)`, the ratio
`rho=log|Delta|/max hhat(P_i)`, all rejected candidates, CPU time, and memory.
The strongest named escape hatch is a public lift for which `rho` decreases
with `p` while useful target-bearing relations persist. [pcc:unverified]

### Silverman/JKSST local conditions

JKSST Section 3.2 defines the exact reverse-Mestre condition at `ell` as

```text
#E(F_ell) = ell + 1 - floor(2 sqrt(ell)).
```

For each `r`, local primes are taken in increasing order from `7..97`, skipping
primes with fewer than `r` usable affine points, until their product `M` first
reaches `p`. Every local incidence matrix must have rank `r`. Local tuples use
the same public scalar labels in compatible cyclic subgroups; images in common
torsion quotients are checked so the local data do not force independence.
Construction failures are retained, never silently resampled away.
[pcc:unverified]

The paired modern arms are:

- `A_none`: no auxiliary local constraint (`M=1`);
- `B_reverse_mestre`: exact reverse-Mestre residues at the frozen primes;
- `P_neutral_crt`: identical local primes and modulus size, but nonsingular
  local curves with cardinality nearest `ell+1`, under the same rank and
  compatibility checks.

`B` versus `A` measures the total effect including CRT inflation; `B` versus
`P` isolates the low-point-count trace effect at matched CRT cost. A historical
`C_size_matched` calibration arm uses no local conditions at a source modulus
of comparable size to `M*p`, as in JKSST Section 5.4, but it is not pooled with
the fixed-`p` factorial estimand. Reverse-Mestre `+1` and `+2` are secondary
diagnostics only. [pcc:unverified]

## Lift, reduction, and recovery certificates

Each admitted row certifies that the rational model is nonsingular with good
reduction at every required prime; all selected points lie on it exactly and
reduce to their named source/local points; all coefficient residues and
incidence rows hold; any rational relation reduces to the corresponding source
relation; and target recovery occurs only with an invertible induced target
coefficient and exact scalar replay. [pcc:unverified]

Reduction is a one-way group homomorphism on admitted good integral points: a
rational relation implies a source relation. No inverse map or preservation of
independence is assumed. [pcc:unverified]

## Rank and dependence classification

Retain three distinct endpoints: full curve rank below `r`, dependence of the
selected points, and useful target recovery. Full rank `<r` is sufficient but
not necessary for selected-point dependence, and a low-rank curve without an
invertible target-bearing relation is not a Xedni success.

```text
CERT_LT  iff a certified upper bound rank(E(Q)) < r;
CERT_GE  iff a certified lower bound rank(E(Q)) >= r;
UNKNOWN  otherwise.
```

PARI `ellrank` returns unconditional `[lower,upper,s,L]`; only these inequalities
classify a row. PARI tiers are capped at 60 and 300 seconds. Every `UNKNOWN`
and apparent event is sent to Magma `RankBounds`/2-descent at 300 and 1,800
seconds. Missing Magma, timeouts, or disagreeing bounds remain `UNKNOWN`.
Retain exact tool versions/image digests, commands, transcripts, return codes,
CPU, RSS, and proof flags. Selected-subgroup rank, exact relation, saturation,
height-pairing status, and source recovery are recorded separately; floating
height determinants are not certificates. [pcc:unverified]

## Censoring and estimands

For each cell let `A` be `CERT_LT`, `G` be `CERT_GE`, `U` be unresolved, and
`N=A+G+U`. Report `q_min=A/N` and `q_max=(A+U)/N`. Every conclusion must survive
adversarial allocation of unresolved rows; otherwise it is `UNRESOLVED`.
Timeout and construction-failure rates are reported by cell. [pcc:unverified]

The rare-event model is binomial with complementary-log-log link:

```text
S[p,c] ~ Binomial(N[p,c], q[p,c])
log(-log(1-q[p,c])) = alpha[c] + beta[c] log(p).
```

Lift, `r`, local arm, curve family, and predeclared interactions are factors;
source curve and prime are clusters. Use a cluster bootstrap or beta-binomial
sensitivity analysis because the prior toy sweep had pooled Poisson dispersion
2.87 overall and 4.05 for `j0`. Holm correction follows the primary global
test. Useful dependence/recovery uses the same model as a co-primary endpoint.
[pcc:unverified]

## Power, stages, and decision rule

At `p=2^32`, 30 expected events require about `1.29e11` trials under `1/p`,
`5.03e8` under `p^-0.75`, and `1.97e6` under `p^-0.5`, per cell before the
factorial expansion. Even zero events needs about `5.03e7` trials to reject
`q>=p^-0.75` at 95%. Small high-bit samples are sentinels for gross departures,
not powered tests of `-1` versus `-0.75`. [pcc:unverified]

Execution stages are:

1. `controls`: known-rank curves, planted dependencies, independent controls,
   residue mutations, and parser tests; excluded from inference.
2. `calibration`: bits 16 and 18, two rows per cell; tool/cost feasibility only.
3. `sentinel`: all bits, five rows per cell; explicitly underpowered.
4. `discovery`: bits 16--24 with exposure computed before outcomes for the
   `p^-0.75` alternative and a separately committed resource allocation.
5. `replication`: identical matrix with fresh seed/primes, launched only after
   the discovery threshold is crossed.

Classify `DEFEATED_IN_SCOPE` only with at least 30 doubly certified nontrivial
useful events above the frozen lower cutoff; a simultaneous confidence bound
showing decay exponent `<0.8` (equivalently slope `beta>-0.8` in the signed
`q=kappa*p^beta` convention); survival under adversarial unresolved allocation;
fresh-seed replication with PARI/Magma agreement; no domination by trivial
line relations; and complete work accounting. Any missing condition leaves the
heuristic not defeated. A conditional local arm speaks only for that selected
population unless known proposal probabilities reconstruct the unconditional
population. [pcc:unverified]

## Cost-reduction and end-to-end boundary

A separately frozen two-phase design may rank all outcome-blind proxy positives
plus a known random sample of proxy negatives. Population fractions must use
the exact inclusion probabilities. A rank- or relation-informed sampler without
known weights is circular. Complete cost includes source generation, local
rejection, lift, rank/relation work, linear algebra, recovery, verification,
memory, and failed attempts. No stage result is an end-to-end advantage until
that total beats matched single-target Pollard rho. [pcc:unverified]

## Sources

1. M. J. Jacobson Jr., N. Koblitz, J. H. Silverman, A. Stein, and E. Teske,
   “Analysis of the Xedni Calculus Attack,” *Designs, Codes and Cryptography*
   20 (2000), 41--64, DOI `10.1023/A:1008312401197`; primary PDF:
   <https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf>, Sections 3.2, 4,
   5.1, 5.2, and 5.4.
2. J. H. Silverman, “The Xedni Calculus and the Elliptic Curve Discrete
   Logarithm Problem,” *Designs, Codes and Cryptography* 20 (2000), 5--40,
   DOI `10.1023/A:1008319518035`.
3. `../xedni_lift_success_20261112/PROTOCOL.md` and `RESULTS.md`.

A planned or underpowered stage is not a completed decay experiment.

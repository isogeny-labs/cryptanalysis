# One exact inverse filter matches complete source pair images at three primes

The [source-free evaluator](inverse_filter.py) takes rational points on
`C: y²+y=x³−7` and `E: y²=x³+432`, checks the exact degree-12
resolvent, and evaluates the exact rational branch to
`B: y²=x³−16`. It returns a verified B point or an explicit status
for an exceptional input. Complete finite-field runs at p=883, 887,
and 997 find that its **valid pair set equals the independently
recorded level-432 source-pair image** at each prime.

| Prime | C order | E order | Rational resolvent pairs | Verified B branches | Branch exceptions | Source chains / distinct (C,E) pairs | Source-pair multiplicities |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 883 | 837 | 931 | 864 | 864 | 0 | 864 / 864 | 864 single |
| 887 | 888 | 888 | 872 | 864 | 4 undefined y inverse, 4 zero denominator | 872 / 864 | 856 single, 8 double |
| 997 | 1008 | 1008 | 1800 | 1800 | 0 | 1800 / 1800 | 1800 single |

The [protocol](protocol.json) was frozen before this run and hashes
the resolvent, B branch, coordinate maps, complete source datasets,
and corrected p887 orbit shards. The pure-Python [screen](screen.py)
enumerates every affine C point and every rational E x-coordinate,
uses Horner evaluation of the specialized resolvent, then calls the
public evaluator on each root. It preserves every result in
hash-listed shards in [result.json](result.json). The evaluator also
checks both input curve equations, the B curve equation, and the
degree-three B-to-E isogeny equation. Its status contract distinguishes
off-curve input, a nonroot pair, zero branch denominator, undefined
y inverse, branch equation failure, and a valid B point.

The independent [checked-Sage audit](audit_sage.py) factors each
specialized resolvent over each prime field, lifts all rational E
points, re-evaluates the B branch in Sage field arithmetic, and
compares the complete pair/output dictionary. It separately recovers
source C coordinates from the four modular j maps at p=883 and p=887,
joins the frozen source B outputs, and compares the exact source-pair
set and B branch. At p=997 it joins the existing 1,800 original C/E
source rows with the independently audited B-fiber allocation. The
[audit receipt](audit.json) records zero missing valid source pairs
and zero incorrect B branches at all three primes. It also tests the
public evaluator's off-curve and nonroot statuses. The
[Sage runtime receipt](sage-runtime-info.txt) identifies the checked
local build.

At p=887, the eight exceptional resolvent pairs are exactly those in
the preceding [p887 inverse experiment](../hecke-432-prime887-inverse-pair-20261025/RESULT.md).
The four E=(322,0) exceptions select x_B=806, which has no rational
B point; the other four have branch numerator and denominator both
zero. The 864 valid pairs include eight with two source kernel chains.
Consequently this evaluator returns the correct B point on the
measured valid domains; it does not choose a unique level-432 chain
at a double source fiber.

## Proof map

| Result | Proof or replay |
| --- | --- |
| Each complete rational resolvent pair set and branch status table | Pure-Python full C/E scan and independent checked-Sage factorization and field evaluation, with hash-bound inputs and output shards. |
| Equality of valid pairs and source-pair image at p=883, 887, 997 | Independent modular-coordinate/source joins and exact set comparison in `audit_sage.py`. |
| Containment plus equal distinct-pair counts implies equality | Pinned Lean theorem `CrossPrimeInverseFilter.source_pairs_perm_valid` proves this for duplicate-free lists using only bundled Std. It keeps containment, duplicate-freeness, and equal lengths as explicit hypotheses. |
| 864 valid plus eight exceptional p887 pairs | Lean theorem `p887_count_partition` checks the arithmetic; disjointness and concrete membership come from the complete audits. |

The [Lean build](formal/build-output.txt) passes and `#print axioms`
reports only standard `propext`, `Classical.choice`, and `Quot.sound`
for the list theorem, and no axioms for the count identity. The
[dependency record](formal/DEPENDENCIES.json) pins Lean and records
the proof boundary. The concrete finite-field computations and modular
coordinate maps remain executable arithmetic evidence rather than
Lean definitions; a general theorem over arbitrary primes remains
open. `lean4checker --fresh` is unavailable on this host.

Replay from the repository root:

~~~sh
python3 experiments/hecke-432-inverse-filter-crossprime-20261025/screen.py
./sage --runtime-info
./sage -python experiments/hecke-432-inverse-filter-crossprime-20261025/audit_sage.py
cd experiments/hecke-432-inverse-filter-crossprime-20261025/formal && lean PairEquality.lean
cd .. && shasum -a 256 -c SEAL.sha256
~~~

The next constructive step is a symbolic saturation of the degree-12
resolvent by the rational branch denominator and B-curve condition.
Its result must explain the p887 exception locus and retain all chain
candidates above valid pairs, including the eight double fibers.

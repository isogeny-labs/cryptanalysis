# H114 — multiradix carry cohomology over the `[2],[3],[5]` permutohedron

Freeze date: 2026-11-17. No H114 candidate point may be scored before this
file, `PROTOCOL.json`, `CURVES.json`, and draft PR #4622 are published.

## Requirement-to-evidence contract

| Requested requirement | Frozen evidence or acceptance test |
| --- | --- |
| A mechanism distinct from H111--H113 | Combine three pair windings through CRT and check the six-order braid hexagon; do not rescore H113's single `w23` base-six word. |
| A public digit candidate | Freeze exactly 11,520 constant predicates before data; forbid curve-sized tables, fitted coefficients, independent post-run limb choices, and interpolation. |
| A complete experiment | Score all 28 rows and 9,096 nonidentity targets, retain every contingency table and tie, and decode every target for every eligible exact ID. |
| Matched controls | Random global sections, histogram-matched labels, coordinate isomorphisms, torsion sections, limb ablations, hexagon checks, and verifier tampering. |
| A proof | Lean must prove the six path identities, pair-winding ranges, braid coherence, CRT uniqueness, and the conditional base-30 decoder without assuming measured exactness. |
| A research PR | Protocol, implementation, failures, raw evidence, independent verification, report, visual and proof receipts remain attached to PR #4622 or its paired verifier PR. |

Status at freeze: protocol only. Candidate data, exact IDs, decoders, runtime
measurements, external novelty, and a generic ECDLP algorithm are not
established.

## Question

H113 retained the bounded integer winding from the two paths `[2]∘[3]` and
`[3]∘[2]`, then asked for one base-six digit. H114 adds multiplier five and
uses all three pair faces. Can the public triple

```text
(w_35(Q) mod 2, w_25(Q) mod 3, w_23(Q) mod 5)
```

after one fixed generator-aware channel and fixed alphabet permutations,
supply the canonical scalar modulo 30?

The mechanism is a bounded first-formal-layer experiment over `Z/p²Z`. Its
six multiplication orders form the `S3` permutohedron. The braid/hexagon
residual is required to vanish exactly; it is a structural certificate, not a
proposed signal. The proposed signal is the CRT combination of the three
bounded face windings.

## Algebraic object

Let `E/F_p` have prime subgroup order `r`, with `p != r` and
`gcd(30,r)=1`. Let `s:E(F_p)->E(Z/p²Z)` be a coordinate-fixed Hensel section,
with `s(O)=O`. For `n in {2,3,5}` define

```text
h_n(Q)       = [n^(-1) mod r]Q,
C_n^s(Q)     = [n]s(h_n(Q)) - s(Q),
kappa_n^s(Q) = t(C_n^s(Q))/p mod p,
```

where each `kappa` is represented in `{0,...,p-1}`. For distinct positive
multipliers `a,b`, the two multiplication paths give

```text
[a]C_b^s(Q/a) + C_a^s(Q)
  = [ab]s(Q/(ab)) - s(Q)
  = [b]C_a^s(Q/b) + C_b^s(Q).
```

Therefore

```text
N_ab(Q) = a*kappa_b(Q/a) + kappa_a(Q)
           - b*kappa_a(Q/b) - kappa_b(Q)
w_ab(Q) = N_ab(Q)/p
```

is integral. Canonical representatives imply the generic bound

```text
-b <= w_ab(Q) <= a.
```

H114 uses

```text
w_23 in {-3,-2,-1,0,1,2},
w_25 in {-5,-4,-3,-2,-1,0,1,2},
w_35 in {-5,-4,-3,-2,-1,0,1,2,3},
```

with every winding at identity defined as zero.

## Six paths and braid coherence

For a permutation `(a,b,c)` of `(2,3,5)`, define its represented first-layer
path height

```text
K_abc(Q) = a*b*kappa_c(Q/(a*b))
           + a*kappa_b(Q/a)
           + kappa_a(Q).
```

The corresponding lifted path telescopes to

```text
[30]s(Q/30) - s(Q),
```

so all six path heights are congruent modulo `p`. Adjacent transpositions give
scaled pair windings. The two reduced paths from order `235` to `532` must
agree as integers:

```text
w_23(Q) + 3*w_25(Q/3) + w_35(Q)
  = 2*w_35(Q/2) + w_25(Q) + 5*w_23(Q/5).
```

The producer must check all six lifted group paths, all adjacent height
differences, exact divisibility by `p`, every pair range, and this braid
identity independently. A nonzero residual invalidates the run.

## Generator-aware channels

For each pair winding `w` and public `(G,Q)`, freeze the same eight integer
channels used in H113:

```text
raw          = w(Q)
plus         = w(Q+G)
minus        = w(Q-G)
forward      = w(Q+G)-w(Q)
backward     = w(Q)-w(Q-G)
curvature    = w(Q+G)-2*w(Q)+w(Q-G)
anchor_plus  = w(Q+G)-w(Q)-w(G)
anchor_minus = w(Q-G)-w(Q)-w(-G).
```

One candidate ID selects one channel name, and that same channel is applied to
all three winding limbs. Independent channel selection per limb is forbidden.

## Frozen 11,520-predicate family

For the selected channel, reduce

```text
z2 = channel(w_35) mod 2,
z3 = channel(w_25) mod 3,
z5 = channel(w_23) mod 5.
```

Enumerate every permutation `pi2`, `pi3`, and `pi5` of the corresponding
residue alphabet in lexicographic order. Set

```text
d2 = pi2[z2],  d3 = pi3[z3],  d5 = pi5[z5],
digit = (15*d2 + 10*d3 + 6*d5) mod 30.
```

The coefficients are the standard CRT idempotents. Cross eight channels with
`2!*3!*5! = 1,440` maps, giving exactly 11,520 predicate IDs:

```text
channel:<name>:pi2:<..>:pi3:<...>:pi5:<.....>.
```

The target label for `Q=[k]G` is `k mod 30`. Retain the complete `30 x 30`
contingency matrix, score, all best ties, every exact ID, and the intersection
of exact IDs over all rows. The same exact ID must survive all 28 canonical
rows. No formula may be added, removed, relabeled or fitted after any score is
observed.

## Conditional base-30 recovery

If one public predicate returns `d=m mod 30` for each current nonidentity
point `R=[m]G`, update

```text
R <- [30^(-1) mod r] (R - [d]G).
```

The canonical scalar becomes `(m-d)/30`. Repeating for at most
`Nat.log 30 m + 1` queries reconstructs `m`; verify the final candidate by
`[m]G=Q` independently. Run the decoder for every row-wise exact ID and for
every ID in the 28-row intersection. No fallback search or generic collision
step is allowed.

## Frozen cohort

Use the seven exact prime-order ICV1 curves in `CURVES.json`. Their orders are
all coprime to 30. The first affine point in lexicographic `(x,y)` order is the
base generator; relabel it by multipliers `1,2,3,5`. This gives 28 rows and
9,096 nonidentity targets, matching H111--H113 exactly.

For every evaluated point, check:

1. base-field point, root, inverse and multiplication identities;
2. every Hensel equation and reduction modulo `p`;
3. all lifted doubles, triples, quintuples and mixed kernel subtractions;
4. projective curve equations, unit formal coordinate, divisibility by `p`,
   and represented formal values;
5. three pair-winding numerators and bounds, six path heights, every adjacent
   difference and the braid identity;
6. all channel residues, CRT recombination, contingency cells and predicate
   scores.

Any mismatch invalidates the run. Stopping is exhaustive.

## Frozen controls

- **Random global sections:** on the first two curves, eight replicates each.
  A deterministic first-layer offset is assigned once per point and reused in
  every occurrence, preserving the section-cocycle identities.
- **Histogram-matched labels:** on the first two curves, eight deterministic
  Fisher--Yates shuffles each of the canonical `k mod 30` label vector. The
  full 11,520-way selection is repeated without changing class counts.
- **Coordinate isomorphisms:** repeat the multiplier-one canonical rows for
  the first two curves under `(x,y)->(lambda²*x,lambda³*y)`, `lambda=2`.
- **Prime-to-p torsion section:** construct the unique first-layer torsion lift
  of every point. All three pair windings and all six path differences must be
  zero.
- **Braid/path positive control:** every lifted path and formal congruence must
  agree for canonical and random sections; the integer braid residual must be
  zero.
- **Limb ablations:** for reporting only, rescore with each of the mod-2,
  mod-3, and mod-5 limbs replaced by zero. Ablations cannot qualify as the
  candidate or enlarge the exact-ID intersection.
- **Tamper rejection:** the independent verifier must reject a modified path
  coefficient, CRT limb, and scalar label.

## Determinism

Use SplitMix64 with the standard wrapping constants recorded in
`PROTOCOL.json`. A control seed is the first eight big-endian bytes of

```text
SHA256(domain || 0x00 || curve_slug || 0x00 ||
       decimal(generator_multiplier) || 0x00 || decimal(replicate)).
```

Permutation enumeration is lexicographic. Signed residues use Euclidean
reduction into `{0,...,m-1}`. Serialization order is curves, generator
multipliers, scalar labels, controls, channels, `pi2`, `pi3`, then `pi5`.

## Accounting and artifacts

Implement the producer and independent verifier in Rust. Historical Python
artifacts may be read but are not extended. Record separately:

- base-field additions, doublings, scalar multiplications and inversions;
- `p²` lift constructions, lifted additions/doublings, quintuple paths,
  kernel operations, formal extractions and modular operations;
- cached versus uncached reuse of `kappa_2`, `kappa_3`, and `kappa_5`;
- pair-winding, six-path, channel, CRT and predicate evaluations;
- decoder queries, subtractions, inverse-30 multiplications, final EC checks,
  memory, stored elements and advice;
- producer enumeration work versus hypothetical online work. One online
  channel query may use the three pair windings at `Q-G,Q,Q+G`; anchored
  channels also charge the six pair-winding values at `G,-G` as setup.

Wall time is environment metadata, not a speed claim. The result requires raw
evidence or a content-addressed manifest, source-independent verification,
tamper receipts, a readable report, editable SVG plus PNG, an inspected PDF,
and repository claim standing where applicable.

## Acceptance and falsification

The bounded candidate passes only if:

1. every arithmetic, path, braid, range, cohort and tamper check passes;
2. one identical predicate ID is exact on all 28 canonical rows;
3. every one of the 9,096 targets is reconstructed with that ID and passes an
   independent EC check;
4. the exact predicate receives a uniform mathematical proof beyond toy data;
5. complete charged construction, online, verification and failed-attempt
   costs are retained.

An empty 28-row intersection, generator instability, any missed scalar,
control-equivalent fit without exactness, or any structural failure rejects
this frozen family. It does not reject every function of multiplication
carries or establish a generic lower bound.

## Prior-art boundary

Repository evidence includes H111's rejected first-layer binary parity family,
H112's second-digit protocol, and H113's binary/trinary winding construction.
H114 differs by using three pair faces, the `S3` braid certificate, and one
predeclared CRT digit family.

Primary context checked before the freeze:

- Invernizzi and Taufer, [Multiplication polynomials for elliptic curves over
  finite local rings](https://arxiv.org/abs/2302.03650).
- Huang, Kueh, and Tan, [Lifting Elliptic Curves and Solving the Elliptic Curve
  Discrete Logarithm Problem](https://doi.org/10.1007/10722028_22).
- Yasuda, [The Elliptic Curve Discrete Logarithm Problems over the p-adic Field
  and Formal Groups](https://doi.org/10.1007/978-3-642-12827-1_9).
- Hochschild and Serre, [Cohomology of Group
  Extensions](https://www.sas.rochester.edu/mth/sites/doug-ravenel/otherpapers/hochschild-serre.pdf).

The shared research KB and sibling lead-atlas command were unavailable; four
KB queries and the failed wrapper calls are recorded in the session log. The
bounded fallback did not locate this exact CRT/permutohedron experiment. That
supports only a repository-distinct hypothesis, not external novelty.

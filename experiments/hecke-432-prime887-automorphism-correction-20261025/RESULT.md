# The corrected p=887 rational B fibers are uniformly eight-to-one

The normalized level-432 map to B: y² = x³ − 16 has **872
noncuspidal rational source points** over F_887 and **109 affine image
points**, each with **eight** rational source points. The prior
6/7/8/9 fiber histogram came from retaining eight j=1728 base-model
chain representatives that form four geometric automorphism orbits,
while omitting four distinct orbits on the j=1728 quadratic-twist
model. Replacing four duplicate base representatives with the four
twist orbits gives the uniform 8:109 histogram. The affine image set
is unchanged. The eight rational cusps map to the identity, so the
full image remains 110 of the 888 B points and its complement remains
778.

The [frozen protocol](protocol.json) binds the raw chain census,
earlier image rows, coordinate maps, and executed isogeny code by
SHA-256. The [corrected receipt](result.json) records every special
orbit, the four removed row indices, the four added twist outputs,
and hashes for four [corrected row shards](corrected-00.json). The
original p=887 files remain byte-for-byte historical inputs.

| Source class | Earlier retained chain rows | Corrected geometric orbits |
| --- | ---: | ---: |
| Generic j | 856 | 856 |
| j=0 base and twist | 8 base, 8 omitted twist | 8 shared orbits |
| j=1728 base | 8 | 4 |
| j=1728 twist | 8 omitted | 4 distinct from base |
| **Corrected noncuspidal total** | **872 retained rows** | **872 points** |

For j=0, the source automorphism x ↦ ζx, where ζ³=1,
and the base-to-twist x scaling t³=5 match all eight twist chains
to eight base chains. For j=1728, x ↦ −x pairs the eight paths
on each model into four orbits. The base-to-twist scaling would
require t²=5; checking both choices over F_887² finds no cross-model
orbit match. The corrected count agrees with the independent
weight-two Hecke count of 880 rational level-432 points minus eight
rational cusps.

The [checked Sage producer](rebuild_sage.py) evaluates one chain
representative from each missing twist orbit with the existing
modular map. Their B outputs are (808,797), (484,0), (808,90), and
(484,0). Each was already in the former affine image. The four
base representatives removed had B outputs (326,49), (72,765),
(326,838), and (72,122). Those seven affected B fibers all become
size eight; the remaining 102 fibers already had size eight.

## Independent replay and inverse fibers

The [arithmetic audit](audit.json) rebuilds the corrected source
keys and B fibers from the hash-bound shards, counts B(F_887)=888 by
integer square tables, checks every B and E curve equation, and
recovers the original X_0(27) C coordinate from all four modular
j-functions. Every corrected chain has exactly one rational C
coordinate. The corrected pair map has **218 C points** and **864
distinct (C,E) pairs**: 856 have one chain and eight have two.

The separate [special-orbit audit](orbit_audit.json) reconstructs
all degree-16 and degree-27 kernel polynomials, checks each
automorphism orbit and both cross-model comparisons, and re-evaluates
the four twist map outputs. Both audits pass. The checked Sage
[runtime receipt](sage-runtime-info.txt) identifies the accepted
local build.

This second-prime result sharpens the direct inverse contract:
a (C,E) input may have two rational chain preimages at an exceptional
fiber. At p=887, four double pairs arise at E=(322,0) from terminal
sign fixed points; four more arise from collisions between distinct
chain prefixes. An inverse evaluator must retain both paths in these
cases.

## Proof map

| Result | Evidence and formalization |
| --- | --- |
| j=0 base/twist equivalence and j=1728 four-plus-four orbits | Full kernel-polynomial transformations in the producer and independent Sage replay. The actual elliptic-curve isomorphism and modular coarse-quotient bridge remain open in Lean. |
| Corrected 872-point source partition | Explicit orbit representatives, raw chain census, Hecke point count, and pinned Lean P887OrbitCount.corrected_source_card for the finite-set implication from disjoint 856, 8, 4, and 4 strata. |
| Uniform eight-point B fibers and 109-point affine image | Four new forward map evaluations, complete corrected row shards, and independent B-curve and fiber audit. The concrete 887-field map is not encoded in Lean. |
| 864 distinct (C,E) pairs, eight double fibers | Complete corrected source join and independent C-coordinate evaluation using source/intermediate/target j-functions. |

The [Lean build](formal/build-output.txt) checks both finite-set
implications with only standard propext, Classical.choice, and
Quot.sound foundations; [dependencies](formal/DEPENDENCIES.json) pin
Lean and Mathlib. Full formalization of the geometric automorphism
action and the modular-map evaluations remains open.

Replay from the repository root through the checked launcher:

~~~sh
./sage --runtime-info
./sage -python experiments/hecke-432-prime887-automorphism-correction-20261025/rebuild_sage.py
python3 experiments/hecke-432-prime887-automorphism-correction-20261025/audit.py
./sage -python experiments/hecke-432-prime887-automorphism-correction-20261025/audit_orbits_sage.py
cd experiments/hecke-432-prime887-automorphism-correction-20261025
shasum -a 256 -c SEAL.sha256
~~~

The earlier p=887 result and the p=907/p=919 comparison tables
should be updated after their existing Conductor write reservations
are released. This versioned correction supplies the exact rows and
receipts for that change.

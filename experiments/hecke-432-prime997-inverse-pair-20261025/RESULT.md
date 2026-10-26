# The degree-12 resolvent recovers all 1,800 rational level-432 pairs at p=997

Independent enumeration of \(C(\mathbf F_{997})\) and the exact degree-12
resolvent produces **1,800 rational \((C,E)\) pairs**. Each pair has one
recorded level-432 kernel-chain key, and every one of the 1,800 source
records appears. The exact rational branch evaluates at every pair and
produces the previously established 78 affine \(B\)-image points.

## Frozen method and complete result

The [protocol](protocol.json) froze SHA-256 identities for the exact
\(x_E\) resolvent, rational \(B\) branch, source-pair table, kernel-chain
census, and exact \(B\)-image partition before the inverse screen ran.
The producer used the repository's checked Sage launcher; its
[runtime receipt](sage-runtime-info.txt) records the accepted build.

The producer enumerates the 1,007 affine points of
\(C:y^2+y=x^3-7\), specializes the degree-12 polynomial at each,
factors over \(\mathbf F_{997}\), and lifts rational \(x_E\) roots to
\(E:y^2=x^3+432\). It retains each root multiplicity, every branch
status, and the matched source index in six [pair shards](pairs-00.json).

| Quantity | Result |
| --- | ---: |
| \(\#C(\mathbf F_{997})\), \(\#E(\mathbf F_{997})\) | 1008, 1008 |
| Affine \(C\) points screened | 1007 |
| Rational \((C,E)\) pairs | 1800 |
| Matched source records and distinct kernel-chain keys | 1800 |
| Extra or missing pairs | 0, 0 |
| Defined, verified \(B\) branches | 1800 |
| Affine \(B\) points reached | 78 |

The rational \(x_E\)-root-count histogram over affine \(C\) points is
602 with zero roots, 243 with two, 108 with four, and 54 with eight.
Every lifted rational pair has \(x_E\)-root multiplicity one. The
specialized polynomial has degree 12 at 1,002 affine \(C\) points and
is a nonzero constant at five. No specialization vanished identically.
The complete status counts and source-index correspondence are in the
[result receipt](result.json) and its six hash-bound shards.

## Independent full-field audit

The separate [audit](audit.json) constructs all \(C\) and \(E\) points
with integer square tables, then evaluates the specialized resolvent by
Horner's rule at **every** rational \(E\) x-coordinate. Its full-field
pair set equals the producer's 1,800 pairs. It independently checks
the unique source index, joins each pair to its level-432 two- and
three-path keys and terminal \(j\) values, re-evaluates the \(B\)
branch, and checks the \(B\) equation and degree-three isogeny
relation. It finds zero failures and the same 78-point affine image.

The kernel-chain join identifies records in the frozen source census;
the existing [original-C audit](../hecke-432-original-C-lift-20261025/RESULT.md)
checks their source and intermediate modular \(j\) maps. The next
construction will recover these chain keys directly from \((C,E)\).

## Proof map

| Result | Verification |
| --- | --- |
| Exact finite-field pair set and unique chain joins | Complete Sage enumeration, six pair shards, and independent full-field integer audit. The concrete 997-field table is not encoded in Lean. |
| Equality from exhaustive root and source cardinalities | Pinned Lean InversePair.source_pairs_eq_resolvent_pairs proves that source containment and equal cardinality 1800 imply equality. Its hypotheses are supplied here by the two exhaustive computations. |
| Rational \(B\) branch at each pair | Exact branch identity from the preceding experiment, plus 1800 direct modular-field replays in both producer and audit. |

The [Lean build receipt](formal/build-output.txt) records a successful
build and #print axioms with only propext, Classical.choice, and
Quot.sound; [dependencies](formal/DEPENDENCIES.json) pin the toolchain
and Mathlib. lean4checker --fresh is unavailable on this host. A
kernel-checked encoding of the entire finite-field enumeration and
generic modular inverse map remains a separate proof step.

Replay from the repository root:

~~~sh
./sage --runtime-info
./sage -python experiments/hecke-432-prime997-inverse-pair-20261025/enumerate_sage.py
python3 experiments/hecke-432-prime997-inverse-pair-20261025/audit.py
cd experiments/hecke-432-prime997-inverse-pair-20261025
shasum -a 256 -c SEAL.sha256
~~~

The next constructive experiment is to derive a modular inverse from
\((C,E)\) directly, then compare the resulting kernel-chain data to
these 1,800 unique keys without using the census for lookup.

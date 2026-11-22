# The p887 degree-12 resolvent identifies 864 valid source pairs after eight explicit exceptions

The exact degree-12 resolvent has **872 rational (C,E) pairs** over
F_887. The exact rational B branch is defined and verifies on **864** of
them. Those 864 pairs equal the pair image of all **872 corrected
noncuspidal level-432 source chains**: 856 pairs have one chain and eight
have two. The remaining eight resolvent pairs are branch exceptions, not
source pairs. The experiment therefore gives a complete finite-field
inverse filter at this prime, with candidate-set semantics at double
fibers.

The [protocol](protocol.json) was frozen before enumeration and hashes
the resolvent, branch, corrected source shards, census, and coordinate
maps. The checked-Sage [producer](screen_sage.py) enumerates all affine
C points, factors each specialized polynomial, lifts every rational
E point, and records root multiplicity and branch status in four
[pair shards](pairs-00.json). Its [runtime receipt](sage-runtime-info.txt)
identifies the accepted build. The [result](result.json) retains every
status, including exceptional pairs.

| Quantity | Complete p887 result |
| --- | ---: |
| C(F_887), E(F_887) group orders | 888, 888 |
| Affine C points screened | 887 |
| Rational resolvent pairs | 872 |
| Verified rational B branches | 864 |
| Undefined y inverse | 4 |
| Zero branch denominator | 4 |
| Corrected source chains / distinct source pairs | 872 / 864 |
| Source-pair multiplicities | 856 single, 8 double |
| Missing or extra *valid* pairs | 0 / 0 |

The [independent audit](audit.py) builds integer-field C and E point
tables and evaluates the degree-12 polynomial by Horner's rule at every
rational E x-coordinate. Its 872-pair set equals the producer's set.
Separately, it obtains the original C point from all four modular j
maps for every corrected source chain, computes E from its recorded B
point, and reconstructs the 864-pair image. It then independently
evaluates the B branch on every resolvent pair. The [audit receipt](audit.json)
records zero missing source pairs and zero branch mismatches.

The four pairs with E=(322,0) select x_B=806. That x-coordinate has no
rational B point; x_B=484 is another root of the 3-isogeny preimage
cubic and supports B=(484,0), but it is not the branch selected at
those four C points. The other four exceptions have C in
{(689,359),(708,652)} and E in {(706,164),(706,723)}. At each, both
the branch numerator and denominator vanish. Their E preimage cubic
has x_B=532 and rational B points (532,220) and (532,667); the
rational branch remains undefined at these C points. These coordinates
and the exact numerator/denominator values are in the audit receipt.

The specialized resolvent has degree 12 at 886 affine C points and is a
nonzero constant at one. None vanishes identically. Among its rational
x_E roots, 864 lifted pairs have simple roots and eight lifted pairs
have multiplicity two (four valid branches and four zero-denominator
exceptions). Root multiplicity is retained as a diagnostic;
the B branch and source comparison determine the inverse result.

## Proof map

| Statement | Current evidence |
| --- | --- |
| Complete 872 rational resolvent pairs | Exhaustive checked-Sage root enumeration and independent all-C/all-E integer-field Horner scan. |
| Exactly 864 valid B branches | Producer and independent audit of numerator, denominator, B equation, and 3-isogeny preimage cubic. |
| Equality to corrected source-pair image and 856/8 multiplicity split | Hash-bound corrected source shards, four modular j-map coordinate recovery, independent pair join, and complete set comparison. |
| Finite-set implication from containment and equal cardinality | `P887FinitePairFilter.source_eq_valid` states the exact structural implication; its Lean build is **partial** because this host currently cannot resolve `Mathlib.olean`. The concrete finite-field computations are not encoded in Lean. |

The [Lean source](formal/FinitePairFilter.lean) also states the
864-plus-eight partition implication, with explicit cardinality and
disjointness hypotheses. The pinned [toolchain and dependency record](formal/DEPENDENCIES.json)
and [failed build output](formal/build-output.txt) preserve the exact
open proof gate. No checked-proof claim is made for these declarations;
the readable finite-set proof is that containment of a finite 864-set
in another finite 864-set forces equality, and disjoint union adds the
864 valid and eight exceptional elements to 872.

Replay from the repository root:

~~~sh
./sage --runtime-info
./sage -python experiments/hecke-432-prime887-inverse-pair-20261025/screen_sage.py
python3 experiments/hecke-432-prime887-inverse-pair-20261025/audit.py
cd experiments/hecke-432-prime887-inverse-pair-20261025
shasum -a 256 -c SEAL.sha256
~~~

The next algebraic step is to saturate the resolvent by the branch
denominator and characterize the E=(322,0) section. A generic inverse
should preserve all rational source candidates at exceptional fibers,
then test them against the exact modular map.

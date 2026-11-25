# The exact rational image on 432a1 at p=997 has 79 points

The normalized level-432 map to the optimal curve
\(B=432a1:y^2=x^3-16\) has **78 affine image points** over
\(\mathbf F_{997}\). Its 36 rational cusps map to the identity,
giving **79 points in the full rational image**. Direct independent
enumeration gives \(\#B(\mathbf F_{997})=1008\), so **929 B points
lie outside that image**. This determines the exact value of the
earlier [79–217 image interval](../hecke-432-prime997-20261025/RESULT.md).

The [complete fiber receipt](fibers.json) assigns every one of the
1,800 noncuspidal rational level-432 source records to its unique
\(B\) point. The fiber-size histogram is

| Source points over one B point | Number of B points | Charged source points |
| ---: | ---: | ---: |
| 12 | 6 | 72 |
| 24 | 72 | 1,728 |
| **Total** | **78** | **1,800** |

Every fiber stays within the geometric degree-24 bound. Grouping by
the degree-three isogeny image in \(E:y^2=x^3+432\) resolves all 72
earlier projected fibers: six 12-point E fibers occupy one 12-point
B fiber each; sixty 24-point E fibers occupy one 24-point B fiber
each; and six 48-point E fibers occupy two 24-point B fibers each.
The other rational B preimages of those E points are unoccupied by
the level-432 source census.

## Producer and independent replay

The [protocol](protocol.json) froze p=997, source paths and SHA-256
digests, the 1,800 expected source records, the cusp count, group
order, prior image interval, and validation rules before this
assignment ran. `count_image.py` evaluates the exact
[rational B-coordinate branch](../hecke-432-b-coordinate-resolvent-20261025/branch_formula.json)
\(x_B=N(x_C,y_C,x_E)/D(x_C,y_C,x_E)\), then recovers
\(y_B=y_E x_B^3/(x_B^3+128)\). For each source it checks the C, E,
and B equations, the cubic x-isogeny relation, and membership in
the earlier independent list of three B preimages of the supplied
E point. It retains the source indices of every B fiber and every
failure or exceptional denominator. The [result receipt](result.json)
records zero failures, all 1,800 assignments, the exact counts, and
the fiber-file digest.

The separate [audit](audit.json) reads the frozen sources and fiber
partition anew. It evaluates the branch by Horner expansion in
\(x_E\), checks each source index occurs exactly once and maps to
its recorded B point, replays the E-to-B fiber allocation, and
counts \(B(\mathbf F_{997})\) by a direct table of quadratic
residues rather than the producer's Euler-criterion count. It finds
the same 78 affine image points, E-fiber histogram
\((6,60,6)\) at sizes \((12,24,48)\), B-fiber histogram
\((6,72)\) at sizes \((12,24)\), and group order 1008.

The underlying [complete all-\(j\) census](../hecke-432-prime997-20261025/census.json)
has 1,800 noncuspidal records. Its independent Hecke trace gives
1,836 rational level-432 points; the difference is 36 rational
cusps. The earlier [cusp-image control](../hecke-432-cusp-image-20261025/RESULT.md)
places their normalized B image at the identity. No affine source
record contributes that point. Thus the complete source census and
cusp control establish the full image count, rather than a sample
of an E-projected fiber.

## Proof map

| Result | Evidence and formalization |
| --- | --- |
| Exact 1,800-to-78 affine image partition | Frozen complete source census, explicit branch identity, full `fibers.json`, producer checks, and independent Horner audit. The concrete finite-field dataset is not encoded in Lean. |
| 72 degree-24 and six degree-12 B fibers | Complete source-index partition with zero duplicate or missing indices; independent per-E allocation and degree-bound checks. |
| Full image 79 and complement 929 | Cusp identity dependency, direct 1,008-point B count, and pinned Lean `ExactBImage.image_card_from_fiber_partition` and `complement_card_from_exact_image`. The Lean theorems prove the finite-set implications from the observed disjoint partition and group order. |

The [Lean source and build receipt](formal/) pin Lean 4 and Mathlib,
build both declarations, and retain their `#print axioms` output.
Only standard foundations appear; `lean4checker --fresh` is
unavailable on this host. Formalizing the full modular map and all
1,800 concrete source records in Lean remains open.

Replay from the repository root:

```sh
python3 experiments/hecke-432-prime997-exact-b-image-20261025/count_image.py
python3 experiments/hecke-432-prime997-exact-b-image-20261025/audit.py
cd experiments/hecke-432-prime997-exact-b-image-20261025
shasum -a 256 -c SEAL.sha256
```

The next experiment is to use the same exact branch to test
independently selected \((C,E)\) inputs against the degree-12
resolvent and then recover the corresponding level-432 kernel-chain
records. The present count supplies a complete p=997 reference set
for that inverse evaluation.

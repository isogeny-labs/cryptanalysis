# The full geometric level-16 fiber has 24 distinct E outputs

For the frozen original \(X_0(27)\) point \(C=(639,232)\) over
\(\mathbf F_{997}\), all **24** geometric cyclic level-16 lifts have
different images on \(E:y^2=x^3+432\). The 24 lifts and their images are
defined over \(\mathbf F_{997^4}\). Eight lifts are rational over
\(\mathbf F_{997}\), eight first appear over \(\mathbf F_{997^2}\), and
eight first appear over \(\mathbf F_{997^4}\). Their Frobenius orbits
respectively have lengths 1, 2, and 4. This separates the entire geometric
fiber of the degree-24 forgetful map above this C point, extending the
earlier rational-point census to every cyclic-16 subgroup in the fiber.

## Frozen instance and computation

The [protocol](protocol.json) chose the first original C point with eight
rational level-432 sources in the prior p=997 census: source curve
\([0,0,0,616,645]\), \(j=18\), indexed 27-chain 0, and
\(C=(639,232)\). The subgroup count is
\(3\cdot2^3=24\): a first 2-isogeny kernel has three choices and each
nonbacktracking continuation has two. Since 997 is odd, each such chain
identifies one geometric cyclic subgroup of order 16.

The [count record](count_result.json) enumerates 8, 16, and 24 such chains
over extension degrees 1, 2, and 4; degree 8 was unnecessary after the
complete count appeared. The degree-4 field is represented by
\(\mathbf F_{997}[u]/(u^4+4u^2+622u+7)\). The [evaluation record](evaluation.json)
preserves all 24 root-vector chains and outputs. For each chain, the Sage
evaluator reconstructs the exact 2-isogenies, transports the fixed 27-chain,
uses Weil-pairing-oriented quarter shifts, filters the C coordinate by
intermediate \(j(3\tau)\) and \(j(9\tau)\), and projects the resulting
point to E. Every row has status `PASS`.

| Field of first definition | Lifts | Distinct E outputs in that stratum |
| --- | ---: | ---: |
| \(\mathbf F_{997}\) | 8 | 8 |
| \(\mathbf F_{997^2}\) | 8 | 8 |
| \(\mathbf F_{997^4}\) | 8 | 8 |
| **Complete geometric fiber** | **24** | **24** |

The pure-Python [independent audit](audit.py) replays arithmetic in the
recorded quotient field, checks all E equations, 24 unique paths and images,
Frobenius equivariance and orbit lengths, and the eight rational outputs
against the earlier independent original-C census. Its [receipt](audit.json)
is `PASS_INDEPENDENT_GEOMETRIC_FIBER_AUDIT`.

## Geometric interpretation and proof map

**Conditional specialization lemma.** Let \(R\) be a mixed-characteristic
DVR with residue characteristic 997. Suppose the forgetful map
\(f:X_0(432)_R\to X_0(27)_R\) is finite étale of degree 24 near the
selected C point and the projected map \(g:X_0(432)_R\to E_R\) extends the
characteristic-zero E coordinate with the reduction evaluated here. Then
the pair \((f,g)\) is generically injective on the corresponding component.

To prove this, form \(X\times_C X\) near the selected point. Its diagonal
is both open and closed because \(f\) is finite étale. On the closed
off-diagonal part, the equalizer of the two E projections is closed since
E is separated. Its image in C is closed because the projection is finite.
The 24 distinct E outputs show that this image misses the selected special
C point. Hence a neighborhood of that point has no off-diagonal collision;
the neighborhood intersects the generic fiber, giving generic injectivity.
The finite-étale, extension, and reduction-identification hypotheses are
the exact remaining modular-model obligations before applying this lemma
unconditionally to the characteristic-zero pair map. Standard separation
and finite-étale facts are recorded in the [Stacks Project](https://stacks.math.columbia.edu/tag/01KH)
and its [étale chapter](https://github.com/stacks/stacks-project/blob/master/etale.tex).

| Result | Evidence and formalization |
| --- | --- |
| Complete 24-element cyclic-16 fiber | Nonbacktracking subgroup count and exact Sage enumeration in `count_result.json`; independent audit checks 24 unique recorded paths. |
| 24 distinct E outputs, Frobenius compatibility | `evaluation.json` and independent GF(997⁴) replay in `audit.py`. |
| Pairwise separation implies image cardinality 24 | `GeometricFiber.image_card_of_pairwise_separation`, checked Lean theorem with separation as an explicit hypothesis. |
| Characteristic-zero generic injectivity under the stated modular-model hypotheses | Written specialization proof above; formalization of integral modular maps, their reduction and finite-étale neighborhood remains open. |

The Lean theorem does not replace the concrete 24-row certificate or discharge
the modular-model hypotheses. The checked toolchain and Mathlib revision are
in [formal/DEPENDENCIES.json](formal/DEPENDENCIES.json); the exact build and
`#print axioms` output are in [formal/build-output.txt](formal/build-output.txt).

Replay from the repository root using the checked Sage launcher:

```sh
./sage --runtime-info
./sage -python experiments/hecke-432-geometric-fiber-20261025/count_sage.py
./sage -python experiments/hecke-432-geometric-fiber-20261025/evaluate_sage.py
python3 experiments/hecke-432-geometric-fiber-20261025/audit.py
```

The next proof step is to identify the integral extension of the normalized
E projection with the evaluated reduction and verify the finite-étale
neighborhood at this exact C point. Once established, the specialization
lemma gives a characteristic-zero degree-one result for the paired map.

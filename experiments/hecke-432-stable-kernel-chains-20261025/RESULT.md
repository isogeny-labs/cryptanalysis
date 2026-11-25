# Complete level-432 point census at p=883 and a finite-map image bound

An exhaustive rational-kernel-chain census gives **864 noncuspidal points of \(X_0(432)(\mathbf F_{883})\)**. An independent weight-two Hecke computation gives 888 total points, of which 24 are rational cusps, exactly corroborating the chain count. The optimal target curve \(B=432a1\) has 931 \(\mathbf F_{883}\)-points. Therefore every map \(X_0(432)(\mathbf F_{883})\to B(\mathbf F_{883})\), including the modular parametrization under study, leaves at least **43 target points without an \(\mathbf F_{883}\)-rational preimage**. This is a finite-field fiber bound for the exact field, level, and curve—not an extrapolation from the earlier 54 rational-generator inputs.

## Kernel-chain construction

For a cyclic order-432 subgroup \(C\), its characteristic subgroups \(C[16]\) and \(C[27]\) have coprime orders, and \(C=C[16]\oplus C[27]\). A rational cyclic \(\ell\)-subgroup for \(\ell=2,3\) corresponds to a rational root of the \(\ell\)-division polynomial: for \(\ell=3\), the root records the common \(x\)-coordinate of \(\pm P\). A cyclic subgroup of order \(\ell^k\) gives a length-\(k\) chain of rational \(\ell\)-isogenies. Conversely, a chain remains cyclic precisely when each step avoids the exact dual kernel of its predecessor. The producer enumerates every rational root at each step and excludes only that dual root. Sage's [isogeny reference](https://doc.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/ell_curve_isogeny.html) specifies the dual composition used for this check.

At \(p=883\), a Frobenius-stable cyclic order-432 subgroup can occur only when the trace is one of \(-52,-20,20,52\), by the [previous necessary-congruence screen](../hecke-432-rational-generator-fibers-20261025/frobenius_screen.json). Quadratic twisting sends \(t\) to \(-t\) and preserves the cyclic kernel lines. The census takes the positive-trace representative for each generic \(j\) and checks equal chain counts on its negative-trace twist. It separately scanned all sextic twists at \(j=0\) and quartic twists at \(j=1728\); none contributed a chain pair. Thus generic \(j\)-classes have no residual automorphism quotient beyond the sign automorphism, which fixes each subgroup.

| Trace of chosen representative | Curve classes scanned with that trace | Paired cyclic 16/27 chains |
| ---: | ---: | ---: |
| 20 | 48 | 432 |
| 52 | 18 | 432 |
| Total | 66 | **864** |

The initial \(j=6\) source has four cyclic 16-chains and three cyclic 27-chains. Its earlier rational generator matches pair \((1,1)\), while the cubic-extension generator matches pair \((1,0)\); the exact edge roots and quotient \(j\)-values are in `witness_chain_validation.json`. `audit_rational_subset_sage.py` then matches **all 54** earlier rational-generator subgroups to distinct entries of the full trace-20 chain census. `full_chain_census.json` retains every source model and ordered kernel route.

## Independent point count and image consequence

For \(p\nmid432\), the Eichler–Shimura point-count relation gives

\[
\#X_0(432)(\mathbf F_p)=p+1-\operatorname{Tr}\bigl(T_p\mid S_2(\Gamma_0(432))\bigr).
\]

The checked Sage calculation finds \(\dim S_2(\Gamma_0(432))=55\) and \(\operatorname{Tr}(T_{883})=-4\), hence \(\#X_0(432)(\mathbf F_{883})=888\). This uses the standard Eichler–Shimura relationship between weight-two cusp forms and the modular-curve Jacobian; see [Zagier's account](https://www.its.caltech.edu/~matilde/Zagier123ModularForms.pdf). Rational cusps are counted independently by denominator \(d\mid432\): if \(h_d=\gcd(d,432/d)\), the \(\varphi(h_d)\) cusps at that denominator are fixed by \(\mathbf F_{883}\)-Frobenius exactly when \(883\equiv1\pmod{h_d}\). The sum is 24 rational cusps out of 36 geometric cusps; the [cusp parametrization](https://www.mdpi.com/2075-1680/12/6/597) supplies the denominator and unit-class description. Thus \(888-24=864\) noncuspidal points, matching the independent isogeny-chain count.

The group \(B(\mathbf F_{883})\) has 931 points, as checked in the preceding [fiber census](../hecke-432-rational-generator-fibers-20261025/coverage_audit.json). A function from 888 points to 931 points has image size at most 888, so at least 43 target points lack a rational source point. `FiniteImageGap.at_least_forty_three_missing` proves this structural finite-map implication in Lean with arbitrary finite source and target types; its `#print axioms` output lists only `propext`, `Classical.choice`, and `Quot.sound`.

## Proof map and next computation

| Result | Certificate and formalization status |
| --- | --- |
| Cyclic 432-subgroups correspond to coprime cyclic 16/27 chains | Written group/isogeny argument; exact root and dual-kernel producer; rational and cubic witness replays; Lean elliptic-isogeny bridge remains open |
| Complete generic-\(j\) chain count 864 | Frozen full census over all 883 \(j\)-values and admissible traces; negative-twist parity checks; special-\(j\) scan |
| Total modular-curve point count 888 | Independent Hecke trace \(-4\) on a 55-dimensional cusp-form space |
| Rational cusp count 24 | Exact denominator/unit-class enumeration |
| At least 43 missing target preimages | `FiniteImageGap.at_least_forty_three_missing`, conditional on the exact point counts above; checked Lean proof |

The next implementation step is to evaluate the modular parametrization from a **kernel-chain record itself**. Its first two 2-isogeny edges give the degree-four quotient used by the quarter-shift construction; the remaining 2-edges and the 3-chain specify the transported order-four and order-27 subgroup schemes. Computing those transported kernels as polynomials over \(\mathbf F_{883}\) would avoid constructing generators over extensions of degree 18 or 36 and would permit all 864 source points to be mapped to \(B\). That image census will answer actual inverse-fiber coverage, beyond the guaranteed 43-point deficit.

Replay from the repository root through the checked launcher with `./sage -python experiments/hecke-432-stable-kernel-chains-20261025/enumerate_chains_sage.py`, `validate_witness_chains_sage.py`, `full_chain_census_sage.py`, `verify_point_count_sage.py`, and `audit_rational_subset_sage.py`. The protocols, Sage runtime receipt, full JSON results, Lean build log, and checksum seal bind the result. No IC candidate or one-target timing comparison is assigned to this exact modular-curve census.

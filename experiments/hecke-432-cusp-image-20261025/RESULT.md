# Cusp field and torsion control for the level-432 image

All **24 rational cusps** of \(X_0(432)(\mathbf F_{883})\) have fields of
definition contained in \(K=\mathbf Q(\zeta_6)=\mathbf Q(\sqrt{-3})\).
The curve \(B:y^2=x^3-16\) has **trivial torsion over K**: 7 and 13 split
in K and are primes of good reduction, while the two residue groups have
orders 7 and 9. For any torsion prime \(\ell\), reduction away from
\(\ell\) forces it to divide one of these orders; the two orders exclude
every \(\ell\). The arithmetic implication is checked in
`CuspArithmetic.no_torsion_prime_from_reduction_orders`.

The [noncuspidal kernel-chain evaluator](../hecke-432-kernel-transport-20261025/RESULT.md)
has 36 B images, none the identity. **If** that evaluator extends to a
\(\mathbf Q\)-defined morphism \(F:X_0(432)\to B\) normalized by
\(F(\infty)=O\), then the Manin–Drinfeld torsion theorem makes every cusp
image equal to \(O\): the difference of each cusp and \(\infty\) is torsion
in the Jacobian, so its image lies in \(B(K)_{\rm tors}=0\). Under this
explicit normalization and map-identity hypothesis, the whole rational
source image has **37** B points and **894** of the 931 B points have no
rational preimage. The missing bridge is to prove that the implemented
quarter-shift/coordinate-descent evaluator is that normalized morphism and
to verify its value at \(\infty\). Until then, the unconditional whole-source
gap remains the previously proved lower bound of 871.

The exact denominator calculation uses one cusp class for each unit modulo
\(h_d=\gcd(d,432/d)\), for every \(d\mid432\). Such a class is fixed by
\(883\)-Frobenius when \(883\equiv1\pmod{h_d}\). The producer enumerates
36 geometric cusps and 24 rational ones; each of the latter has
\(h_d\in\{1,2,3,6\}\). It independently enumerates all finite B points
over \(\mathbf F_7\) and \(\mathbf F_{13}\), then adds the identity to get
the group orders. `result.json` retains every denominator and residue
point. This is exact arithmetic, with no wall-time performance claim.

The Lean proof map is partial: `CuspArithmetic.rational_cusps_count` checks
the arithmetic sum, and `no_torsion_prime_from_reduction_orders` proves the
abstract prime-order contradiction conditional on reduction divisibility.
Formalized bridges from modular cusp fields and good-reduction torsion
injectivity to these hypotheses, and from the implemented evaluator to a
normalized morphism, remain open. The Lean build and `#print axioms` output
are retained; both checked declarations use only standard Lean foundations.

Replay `python3 experiments/hecke-432-cusp-image-20261025/cusp_torsion_control.py`
from the repository root. The next direct check is to compute the
quarter-shift map on a local parameter at \(\infty\), and then compare its
generic function-field expression with the implemented finite-field map.

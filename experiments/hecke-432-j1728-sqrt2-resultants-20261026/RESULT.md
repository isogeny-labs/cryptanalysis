# Exact reduction gate and bounded exceptional-prime classification

The source-`j=1728` level-432 C–E resolvent has no rational C–E pair at 275 of the 283 primes `7 ≤ p < 20000` with `p ≡ 11 (mod 24)`. An exact denominator-and-norm gate certifies these 275 cells. Exhaustive finite-field checks classify the eight exceptional primes `11, 131, 179, 227, 251, 419, 491, 1523`: rational C–E pairs occur at `11, 131, 227, 1523`, and the frozen inverse B-branch formula yields four valid C–E–B triples at `p=131`. An independent replay verifies all four triples on their curves and in the branch equation.

| Prime class, `7 ≤ p < 20000` | Count | Method | Rational C–E pairs | Valid C–E–B triples |
| --- | ---: | --- | ---: | ---: |
| Full reduction gate passes | 275 | Exact characteristic-zero certificate and modular nonvanishing | 0 | 0 |
| Exceptional: `11` | 1 | Direct enumeration and branch replay | 2 | 0, both zero denominator |
| Exceptional: `131` | 1 | Direct enumeration and branch replay | 4 | 4 |
| Exceptional: `179, 251, 419, 491` | 4 | Direct enumeration | 0 | 0 |
| Exceptional: `227, 1523` | 2 | Direct enumeration and branch replay | 2 each | 0, all zero denominator |

The counted object is the rational point on the specified C model together with an E point satisfying the exact C–E resolvent; the final column additionally applies the recorded inverse B-branch formula. The complete prime-by-prime output is [`bounded_result.json`](bounded_result.json). This is a bounded classification, with the cap and source certificates frozen before the gate computation in [`bridge_protocol.json`](bridge_protocol.json).

## Exact gate and proof

Let `K=Q[a]` be the degree-18 source-coordinate field in the [base factor certificate](../hecke-432-j1728-resolvent-field-20261026/factor_certificate.json), and `L=K[s]`, `s²=2`. The [relative-field certificate](../hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json) gives exact products `Q₄=u₄q₂q₂′` and `Q₈=u₈q₄q₄′`, where each primed factor is obtained by `s↦−s`. The [earlier Lean proof](../hecke-432-j1728-sqrt2-split-20261026/formal/FrobeniusSwapGate.lean) shows that a pair exchanged by Frobenius and satisfying a Bézout identity cannot vanish at a Frobenius-fixed point.

For a prime to pass the sufficient gate, it must avoid every rational coefficient denominator in both exact certificates and the rational norm numerators and denominators of six elements: the source-y denominator, base factorization unit, both relative units, and both conjugate-pair resultants. Norm nonvanishing ensures that each element remains nonzero in every residue specialization of the source-coordinate algebra. The source-y denominator keeps the source coordinate valid; the units preserve the product identities; and the resultants keep the conjugate factors coprime. In this congruence class `(2/p)=-1`, so coefficient Frobenius exchanges the two factors. Every rational resolvent root would then be a common root of a coprime conjugate pair, a contradiction. The new [`BoundedGate.lean`](formal/BoundedGate.lean) checks the final product step given both pair exclusions and nonzero unit.

[`resultant_norms_sage.py`](resultant_norms_sage.py) computed the two exact pair resultants in `K` and their rational norms. [`bridge_gate_sage.py`](bridge_gate_sage.py) added the omitted source-y denominator, units, and every coefficient denominator under the separately frozen bridge protocol. The resulting [`bridge_gate.json`](bridge_gate.json) gives exactly eight exceptions in this prime class below 20000. [`audit_norms_sage.py`](audit_norms_sage.py) recomputed all six norm values by determinants of multiplication matrices, independently of the number-field `.norm()` method; [`norm_audit.json`](norm_audit.json) passed. The two pair-resultant norm numerators have 214 and 1005 decimal digits, so the exact sufficient gate is retained as integer data rather than inferred from small-prime samples.

[`audit_bad_primes.py`](audit_bad_primes.py) exhaustively enumerated C points, resolvent roots, and E points at all eight exceptional primes. [`validate_pairs.py`](validate_pairs.py) applied the frozen inverse B branch; [`audit_branch.py`](audit_branch.py) independently replayed its four valid outputs and all zero-denominator classifications. [`bounded_gate_audit.py`](bounded_gate_audit.py) recomputed the entire `11 mod 24` prime list, denominator LCM, and divisibility decisions using Python's exact integers, and reconciled the direct cells. The statuses are `EXACT_DIRECT_BAD_PRIME_AUDIT`, `EXACT_SMALL_PRIME_BRANCH_CLASSIFICATION`, `PASS_INDEPENDENT_VALID_BRANCH_REPLAY`, and `PASS_BOUNDED_11_MOD_24_GATE_ACCOUNTING`.

## Proof map and verification boundary

| Result | Formal declaration / checker | Status |
| --- | --- | --- |
| Frobenius-fixed root excluded by swapped coprime factors | `J1728Sqrt2Split.no_fixed_root_of_swapped_coprime_factors` | Lean checked in the predecessor certificate |
| Product of two excluded pairs with nonzero unit has no root | `J1728BoundedGate.no_root_of_two_excluded_pairs` | Lean checked; `#print axioms` in [`lean-check.txt`](formal/lean-check.txt) |
| Exact degree-18 norms and 283-cell bounded classification | Sage exact arithmetic, determinant replay, finite-field enumeration, and Python accounting | Certificate checked; Lean formalization partial |

The Lean toolchain is pinned in [`formal/lean-toolchain`](formal/lean-toolchain). The remaining Lean bridge is the reduction of the explicit degree-18/36 rational coefficient arrays to each finite residue algebra, including norm nonvanishing and the eight direct finite-field enumerations. The present formal declarations preserve the structural hypotheses; they do not encode the large numerical certificates as Lean proofs. The rational norm numerators have unfactored residual factors beyond the frozen prime cap, so an all-prime exception list requires further factorization or a different valuation argument.

All local Sage runs used the repository's checked `./sage` launcher; [`sage-runtime-info.txt`](sage-runtime-info.txt) records its imported modules and native dispatch. This is an exact algebraic and finite-field diagnostic rather than a timed IC candidate comparison.

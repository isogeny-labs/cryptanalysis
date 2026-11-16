# Canonical norm proof map

The full written argument is [G3_NORM_DERIVATION.md](G3_NORM_DERIVATION.md).
Formalization is partial. Original producer4.35 and consumer4.34.1 gates
each compile/audit the same13 declarations with zero trusted declarations,
c88b36. Exact original-consumer bindings are recorded in
`evidence/g3-norm-lean-bindings-01/claims.json` and their local verdicts.
Local passes remain unsigned; main PCC standing is separate.
[pcc:unverified]

All declarations below are in `G3CanonicalNorm` in
`g3-norm-checker/lean/CanonicalNorm.lean`. The accepted foundations are
propext, Classical.choice and Quot.sound, or no axioms. No theorem assumes
a native evaluation or a custom axiom replacing the geometric result.
[pcc:unverified]

| Declaration | Exact important hypotheses and conclusion |
| --- | --- |
| principal_push_well_defined | Abstract integer modules; class and push preserve subtraction; push annihilates the kernel of class. Equal class implies equal push. |
| canonical_section_independence | Those same hypotheses; two sections of the class map. Their pushed representatives agree for every class. |
| descended_norm_additive | Those same hypotheses; class and push also preserve addition. The pushed section is additive. |
| plane_section_reference_independence | Those same hypotheses; the reference representatives have the same class. Subtracting either reference gives the same push. |
| exceptional_representative_correction | Any integer module. Subtracting canonical-minus-P0 from canonical-minus-P gives P0-minus-P. |
| monogenic_companion_characteristic | Any commutative ring. The explicit companion determinant expression equals the monic cubic used by the adapter. |
| monogenic_relation_evaluation | Any commutative ring and an actual T-cubed relation. The derived cubic vanishes at T. |
| repeated_cycle_multiplicity | Any integer module. The doubled-point cycle equals adding that point twice. |
| reduced_cycle_changes_nonzero_repeated_point | Any integer module and a nonzero repeated image point. Replacing multiplicity2 by1 changes the sum. |
| reverse_composition_from_surjective_pullback | Pull commutes with multiplication by2; norm composed with pull is2; pull is geometrically surjective. Derives pull composed with norm is2, without assuming that reverse conclusion. |
| odd_two_recovery | An integer module; ell kills x and2u+ell v=1. Multiplying2x by u recovers x. No primality or global group inverse is assumed. |
| two_way_odd_subgroup_recovery | Both actual composition identities supplied separately; the Bezout identity and pointwise ell-torsion in source and target. Derives both odd-subgroup recovery directions. |
| actual_odd_recovery_constants | The three explicit integer Bezout identities for ell37,89,331 and u19,45,166. |

The abstract class map can be interpreted first on divisors and the full
Picard group, then restricted to degree zero. The push map here is the
class of the pushed divisor, so a principal divisor maps to zero. The
statement does not incorrectly require a principal divisor to have zero
push as a raw divisor. The actual function-field-norm/divisor identity is
the missing geometric bridge supplying the kernel-annihilation hypothesis.
[pcc:unverified]

The following remain written/native: smooth actual curves and Picard
functors; the R2/R4 quotient's identification with the degree-three divisor
scheme; existence of affine/monogenic presentations and invariance for
every admissible presentation; principal-divisor pushforward via the
function-field norm; actual completed Ciani covers; V4 character separation
and torsion freeness of the homomorphism group; the product pullback's
geometric surjectivity and descent; identification with the original
canonical reducer. No conditional lemma is presented as their formal proof.
[pcc:unverified]

The producer's two unchanged modules and11 exact bindings cover separate
quartic/short-model/coordinate algebra and conditional transfer implications.
They are replayed as producer dependencies, rather than counted as new
consumer declarations. Native unit01c19a2e exhausts the full three rational
groups and tests both compositions. The all-admissible-chart argument is
written; the native alternate-chart controls cover eight typical classes
per field and do not enumerate every pair of choices. [pcc:unverified]

Failed Lean01 a5ecd7 contains the original failed final grind and dependent
sorryAx diagnostics; it is an unsuccessful source, not an accepted proof.
Frozen2b2a5e precedes the proof-body-only rewrite with all statements fixed.
Lean02 bdbc4f compiles13 declarations but fails the older consumer auditor's
removed APIs under4.35. Frozen e14270 precedes the two compatible original
gates. Neither verifier, auditor, trust manifest nor statement was changed
to obtain those passes. [pcc:unverified]

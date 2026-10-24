import Std

namespace FermatZero

def indicator {F : Type} [Zero F] [One F] [Add F]
    (power : F → F) (x : F) : F := 1 + power x

/-- Conditional soundness of the exact zero indicator. The finite-field
Fermat law and characteristic-two addition are explicit hypotheses. -/
theorem indicator_eq_one_iff_zero
    {F : Type} [Zero F] [One F] [Add F] [DecidableEq F]
    (power : F → F)
    (hzero : power 0 = (0 : F))
    (hnonzero : ∀ x : F, x ≠ 0 → power x = 1)
    (hadd_zero : (1 : F) + 0 = 1)
    (hadd_one : (1 : F) + 1 = 0)
    (h01 : (0 : F) ≠ 1)
    (x : F) : indicator power x = 1 ↔ x = 0 := by
  constructor
  · intro hi
    by_cases hx : x = 0
    · exact hx
    · have hp := hnonzero x hx
      have h0 : indicator power x = (0 : F) := by
        simp only [indicator, hp, hadd_one]
      exact False.elim (h01 (h0.symm.trans hi))
  · intro hx
    subst x
    simp only [indicator, hzero, hadd_zero]

/-- Arithmetic obligations of the fixed 1,2,4,5,10,20,40,41 chain. -/
theorem addition_chain_exponents :
    (2^1-1) + 2^1 * (2^1-1) = 2^2-1 ∧
    (2^2-1) + 2^2 * (2^2-1) = 2^4-1 ∧
    (2^4-1) + 2^4 * (2^1-1) = 2^5-1 ∧
    (2^5-1) + 2^5 * (2^5-1) = 2^10-1 ∧
    (2^10-1) + 2^10 * (2^10-1) = 2^20-1 ∧
    (2^20-1) + 2^20 * (2^20-1) = 2^40-1 ∧
    (2^40-1) + 2^40 * (2^1-1) = 2^41-1 := by
  decide

#print axioms indicator_eq_one_iff_zero
#print axioms addition_chain_exponents

end FermatZero

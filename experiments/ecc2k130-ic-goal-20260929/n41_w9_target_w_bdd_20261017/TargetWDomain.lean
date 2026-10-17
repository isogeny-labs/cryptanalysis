import Std
import Init.Grind.Ring.Basic

namespace TargetWDomain
open Lean.Grind

/-- Once a nonzero quartic has a complete split factorization, its zero
set is exactly the four listed target-translated coordinates. -/
theorem split_quartic_exact {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (k w r0 r1 r2 r3 : F) (hk : k ≠ 0) :
    k*((w+r0)*((w+r1)*((w+r2)*(w+r3))))=0 ↔
      w=r0 ∨ w=r1 ∨ w=r2 ∨ w=r3 := by
  have hzero (r : F) : w+r=0 ↔ w=r := by
    constructor
    · intro hz
      have hr := charTwo r
      grind
    · intro he
      rw [he]
      exact charTwo r
  constructor
  · intro h
    rcases Field.of_mul_eq_zero h with hk0 | hprod
    · exact False.elim (hk hk0)
    rcases Field.of_mul_eq_zero hprod with h0 | h123
    · exact Or.inl ((hzero r0).mp h0)
    rcases Field.of_mul_eq_zero h123 with h1 | h23
    · exact Or.inr (Or.inl ((hzero r1).mp h1))
    rcases Field.of_mul_eq_zero h23 with h2 | h3
    · exact Or.inr (Or.inr (Or.inl ((hzero r2).mp h2)))
    · exact Or.inr (Or.inr (Or.inr ((hzero r3).mp h3)))
  · intro h
    rcases h with h0 | h1 | h2 | h3
    · rw [h0, charTwo r0]
      grind
    · rw [h1, charTwo r1]
      grind
    · rw [h2, charTwo r2]
      grind
    · rw [h3, charTwo r3]
      grind

#print axioms TargetWDomain.split_quartic_exact

end TargetWDomain

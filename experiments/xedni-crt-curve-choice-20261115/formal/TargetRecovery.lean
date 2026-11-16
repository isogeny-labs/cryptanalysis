import Mathlib

/-!
Scalar recovery for the fixed prime-order xedni control. The hypotheses
state the reduced relation after substituting Pᵢ = Q - tᵢG in scalar
coordinates. The elliptic-curve witness is checked separately in Sage and
exact arithmetic; this file proves the field-algebra recovery step.
-/

namespace XedniCrtTargetRecovery

local instance : Fact (Nat.Prime 43) := ⟨by norm_num⟩

theorem recover_of_relation (w t₁ t₂ : ZMod 43)
    (h : (w - t₁) + 2 * (w - t₂) = 0) :
    w = (t₁ + 2 * t₂) / (3 : ZMod 43) := by
  have h₃ : (3 : ZMod 43) * w = t₁ + 2 * t₂ := by
    linear_combination h
  calc
    w = ((3 : ZMod 43) * w) / (3 : ZMod 43) := by
      have hne : (3 : ZMod 43) ≠ 0 := by decide
      field_simp
    _ = (t₁ + 2 * t₂) / (3 : ZMod 43) := by rw [h₃]

theorem recovered_scalar_29_11 :
    ((29 : ZMod 43) + 2 * 11) / (3 : ZMod 43) = 17 := by
  have h : ((17 : ZMod 43) - 29) + 2 * (17 - 11) = 0 := by norm_num
  exact (recover_of_relation 17 29 11 h).symm

theorem recovered_scalar_5_23 :
    ((5 : ZMod 43) + 2 * 23) / (3 : ZMod 43) = 17 := by
  have h : ((17 : ZMod 43) - 5) + 2 * (17 - 23) = 0 := by norm_num
  exact (recover_of_relation 17 5 23 h).symm

#print axioms recover_of_relation
#print axioms recovered_scalar_29_11
#print axioms recovered_scalar_5_23

end XedniCrtTargetRecovery

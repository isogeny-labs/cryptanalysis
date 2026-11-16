import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Int.Interval
import Mathlib.Tactic

namespace XedniFixedCurveAdmission

/-- For one fixed rank-one reduction image, admitting both entries of a pair
from a bounded coordinate interval limits the number of ordered pairs. -/
theorem selected_pair_capacity (q K T : ℕ) [NeZero q]
    (g : ZMod q) (torsion : Fin T → ZMod q)
    (A : Finset (ZMod q × ZMod q))
    (hadmit : ∀ pair ∈ A,
      (∃ t : Fin T, ∃ k : ℤ, -(K : ℤ) ≤ k ∧ k ≤ K ∧
        k • g + torsion t = pair.1) ∧
      (∃ t : Fin T, ∃ k : ℤ, -(K : ℤ) ≤ k ∧ k ≤ K ∧
        k • g + torsion t = pair.2)) :
    A.card ≤ (T * (2 * K + 1)) ^ 2 := by
  let I : Finset ℤ := Finset.Icc (-(K : ℤ)) (K : ℤ)
  let D : Finset (Fin T × ℤ) := Finset.univ.product I
  let S : Finset (ZMod q) := D.image (fun tk => tk.2 • g + torsion tk.1)
  have hsub : A ⊆ S.product S := by
    intro pair hp
    obtain ⟨⟨t₁, k₁, h₁lo, h₁hi, h₁⟩,
            ⟨t₂, k₂, h₂lo, h₂hi, h₂⟩⟩ := hadmit pair hp
    apply Finset.mem_product.mpr
    constructor
    · apply Finset.mem_image.mpr
      exact ⟨(t₁, k₁), Finset.mem_product.mpr
        ⟨Finset.mem_univ _, Finset.mem_Icc.mpr ⟨h₁lo, h₁hi⟩⟩, h₁⟩
    · apply Finset.mem_image.mpr
      exact ⟨(t₂, k₂), Finset.mem_product.mpr
        ⟨Finset.mem_univ _, Finset.mem_Icc.mpr ⟨h₂lo, h₂hi⟩⟩, h₂⟩
  have hA := Finset.card_le_card hsub
  have hS : S.card ≤ D.card := Finset.card_image_le
  have hI : I.card = 2 * K + 1 := by
    simp only [I, Int.card_Icc]
    omega
  have hD : D.card = T * (2 * K + 1) := by
    simp [D, hI]
  simp at hA
  nlinarith

#print axioms selected_pair_capacity

end XedniFixedCurveAdmission

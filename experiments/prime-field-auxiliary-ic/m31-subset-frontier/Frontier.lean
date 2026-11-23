import Mathlib.Tactic

namespace M31SubsetFrontier

/-- Nine disjoint obstructions each require a separate deletion. -/
theorem retained_bound {α : Type*} [DecidableEq α] (U S : Finset α) (hS : S ⊆ U)
    (hU : U.card = 500) (edges : Fin 9 → Finset α)
    (disj : Pairwise (fun i j => Disjoint (edges i) (edges j)))
    (hit : ∀ i, ∃ x ∈ U \ S, x ∈ edges i) : S.card ≤ 491 := by
  classical
  choose f hf he using hit
  have inj : Function.Injective (fun i => (⟨f i, hf i⟩ : ↥(U \ S))) := by
    intro i j eq
    by_contra h
    have same : f i = f j := congrArg Subtype.val eq
    exact Finset.disjoint_left.mp (disj h) (he i) (same ▸ he j)
  have hD : 9 ≤ (U \ S).card := by simpa using Fintype.card_le_of_injective _ inj
  rw [Finset.card_sdiff_of_subset hS, hU] at hD
  omega

theorem interior_above_chord (k : ℝ) (lo : 491 < k) (hi : k < 499) :
    (2*k^2 - 482162)*(497954-482162) >
      (498002-482162)*(2*k^2-6*(k-491)-482162) := by
  nlinarith [mul_pos (sub_pos.mpr lo) (sub_pos.mpr hi)]

theorem first_switch (f : ℝ) :
    (f+482162)/482162 ≤ (f+498002)/497954 ↔ 329*f ≤ 482162 := by
  constructor <;> intro h <;> linarith

theorem second_switch (f : ℝ) :
    (f+498002)/497954 ≤ (f+500000)/499940 ↔ 331*f ≤ 980020 := by
  constructor <;> intro h <;> linarith

/-- Even perfect coverage per finite pair gains less than 0.0121 percent. -/
theorem pair_efficiency_ceiling : (500000 / 499940 - 1 : ℚ) * 100 < 121 / 1000000 * 100 := by
  norm_num

end M31SubsetFrontier

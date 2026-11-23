import Mathlib

namespace SignedCapacity

/-- Signed coefficient vectors of length k and exact absolute sum m.
At the first coordinate choose zero, or a sign and magnitude i+1. -/
def Shell : ℕ → ℕ → Type
  | 0, m => Fin (if m = 0 then 1 else 0)
  | k+1, m => Shell k m ⊕ (Σ i : Fin m, Bool × Shell k (m-(i.val+1)))

instance shellFinite : (k m : ℕ) → Fintype (Shell k m)
  | 0, m => inferInstanceAs (Fintype (Fin _))
  | k+1, m => by
    letI (j : ℕ) : Fintype (Shell k j) := shellFinite k j
    unfold Shell
    infer_instance

def count : ℕ → ℕ → ℕ
  | 0, m => if m = 0 then 1 else 0
  | k+1, m => count k m + ∑ i : Fin m, 2 * count k (m-(i.val+1))

theorem card_shell (k m : ℕ) : Fintype.card (Shell k m) = count k m := by
  induction k generalizing m with
  | zero => simp [Shell, count]
  | succ k ih =>
    unfold Shell
    simp [count, Fintype.card_prod, ih]

abbrev Three := Shell 56 3 ⊕ Shell 56 1
abbrev Four := Shell 56 4 ⊕ Shell 56 2 ⊕ Shell 56 0

theorem three_card : Fintype.card Three = 234304 := by
  simp only [Three, Fintype.card_sum, card_shell]
  native_decide

theorem four_card : Fintype.card Four = 6566785 := by
  simp only [Four, Fintype.card_sum, card_shell]
  native_decide

theorem four_image_bound {G : Type*} [DecidableEq G] (eval : Four → G) :
    (Finset.univ.image eval).card ≤ 6566785 := by
  exact Finset.card_image_le.trans_eq ((Finset.card_univ).trans four_card)

end SignedCapacity

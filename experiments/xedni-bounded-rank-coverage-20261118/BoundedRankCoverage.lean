import Mathlib

/-!
Finite coefficient-box coverage for a fixed family of generators. The map from
coefficient tuples to the public group may have collisions; the theorem does
not assume independence or a particular elliptic-curve model.
-/

namespace XedniBoundedRankCoverage

open scoped BigOperators

variable {C : Type*} [Fintype C] [DecidableEq C]

abbrev coefficientBox (r H : ℕ) : Type := Fin r → Fin (2 * H + 1)

theorem coefficientBox_card (r H : ℕ) :
    Fintype.card (coefficientBox r H) = (2 * H + 1) ^ r := by
  classical
  simp [coefficientBox, Fintype.card_fun]

theorem image_card_le (r H : ℕ) (f : coefficientBox r H → C) :
    (Finset.univ.image f).card ≤ (2 * H + 1) ^ r := by
  classical
  simpa [coefficientBox_card] using (Finset.card_image_le (s := (Finset.univ : Finset (coefficientBox r H))) (f := f))

theorem exists_unreachable (r H : ℕ) (f : coefficientBox r H → C)
    (h : (2 * H + 1) ^ r < Fintype.card C) :
    ∃ c : C, c ∉ Finset.univ.image f := by
  classical
  by_contra hn
  push_neg at hn
  have heq : Finset.univ.image f = (Finset.univ : Finset C) :=
    Finset.eq_univ_iff_forall.mpr hn
  have hb := image_card_le r H f
  rw [heq, Finset.card_univ] at hb
  omega

theorem reachable_fraction_le [Nonempty C] (r H : ℕ) (f : coefficientBox r H → C) :
    ((Finset.univ.image f).card : ℚ) / Fintype.card C ≤
      ((2 * H + 1) ^ r : ℚ) / Fintype.card C := by
  classical
  have hpos : (0 : ℚ) < Fintype.card C := by exact_mod_cast Fintype.card_pos
  exact (div_le_div_iff_of_pos_right hpos).2 (by exact_mod_cast image_card_le r H f)

variable [AddCommGroup C]

def groupImage (r H : ℕ) (generators : Fin r → C) (a : coefficientBox r H) : C :=
  ∑ i : Fin r, (((a i).val : ℤ) - (H : ℤ)) • generators i

theorem group_reachable_card_le (r H : ℕ) (generators : Fin r → C) :
    (Finset.univ.image (groupImage r H generators)).card ≤ (2 * H + 1) ^ r :=
  image_card_le r H (groupImage r H generators)

theorem group_exists_unreachable (r H : ℕ) (generators : Fin r → C)
    (h : (2 * H + 1) ^ r < Fintype.card C) :
    ∃ c : C, c ∉ Finset.univ.image (groupImage r H generators) :=
  exists_unreachable r H (groupImage r H generators) h

#print axioms coefficientBox_card
#print axioms image_card_le
#print axioms exists_unreachable
#print axioms reachable_fraction_le
#print axioms group_reachable_card_le
#print axioms group_exists_unreachable

end XedniBoundedRankCoverage

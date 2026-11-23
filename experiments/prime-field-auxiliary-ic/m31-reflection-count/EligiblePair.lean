import M31FixtureObstruction

namespace M31EligiblePair

abbrev F := M31FixtureObstruction.F
local instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

theorem flip {y : F} (hy : y ≠ 0) : IsSquare (-y) ↔ ¬ IsSquare y := by
  have h : quadraticChar F (-1) = -1 := by
    apply quadraticChar_neg_one_iff_not_isSquare.mpr
    intro hs
    exact (by decide : ¬ (2147483647 % 4 ≠ 3)) (ZMod.exists_sq_eq_neg_one_iff.mp hs)
  rw [← quadraticChar_one_iff_isSquare (neg_ne_zero.mpr hy),
      ← quadraticChar_neg_one_iff_not_isSquare]
  rw [← neg_one_mul y, map_mul, h, neg_one_mul]
  omega

def original (x : F) := x^3 + 2*x + 14
def twist (x : F) := x^3 + 2*x - 14

theorem reflected_labels (x : F) :
    (IsSquare (original (-x)) ↔ ¬ IsSquare (twist x)) ∧
    (IsSquare (twist (-x)) ↔ ¬ IsSquare (original x)) := by
  have a (u : F) : original (-u) = -twist u := by unfold original twist; ring
  have b : twist (-x) = -original x := by unfold original twist; ring
  have nz : original (-x) ≠ 0 := M31FixtureObstruction.no_root _
  rw [a, neg_ne_zero] at nz
  rw [a, b]
  exact ⟨flip nz, flip (M31FixtureObstruction.no_root x)⟩

def eligible (x : F) : Prop := ¬ IsSquare x ∧ ¬ IsSquare (x^2+1)

theorem reflected_eligible {x : F} (hx : x ≠ 0) :
    eligible (-x) ↔ IsSquare x ∧ ¬ IsSquare (x^2+1) := by
  classical
  simp only [eligible, flip hx, not_not, neg_sq]

end M31EligiblePair

import PrimitiveMinor
import TranslatedMarginals

namespace M31.PairDeadline

abbrev F := ZMod 2147505293

set_option maxRecDepth 100000 in
private theorem group_prime : Nat.Prime 2147505293 := by norm_num

local instance : Fact (Nat.Prime 2147505293) := ⟨group_prime⟩

/-- Distinct canonical two-point rows cannot be the support of a dependency. -/
theorem two_independent {n : ℕ} (a b : Fin n → ℤ)
    (ha : ∑ j, |a j| = 2) (hb : ∑ j, |b j| = 2)
    (ca : M31.PrimitiveMinor.Canonical a) (cb : M31.PrimitiveMinor.Canonical b)
    (hne : a ≠ b) (u v : F)
    (zero : ∀ k, u*(a k : F) + v*(b k : F) = 0) : u = 0 ∧ v = 0 := by
  obtain ⟨i, j, h⟩ := M31.PrimitiveMinor.bounded_modular_minor a b
    (by decide) (by decide) ha hb ca cb hne
  constructor
  · apply (mul_eq_zero.mp (show u * ((a i : F)*b j - b i*a j) = 0 by
      linear_combination (b j : F) * zero i - (b i : F) * zero j)).resolve_right h
  · apply (mul_eq_zero.mp (show v * ((a i : F)*b j - b i*a j) = 0 by
      linear_combination (a i : F) * zero j - (a j : F) * zero i)).resolve_right h

/-- For any fixed path with a uniform additive shift, fewer than 0.74% of
starts can have three hits in 82,000 slots on the 578-endpoint support. -/
theorem three_hit_cap {Q : Type*} (slots : Finset Q) (path : Q → F)
    (hits : Finset F) (hc : hits.card = 578) (budget : slots.card ≤ 82000) :
    10000 * (Finset.univ.filter (fun h : F =>
      3 ≤ ∑ j ∈ slots, if h + path j ∈ hits then 1 else (0 : ℕ))).card <
      74 * 2147505293 := by
  classical
  let success (h : F) := decide (3 ≤ ∑ j ∈ slots, if h + path j ∈ hits then 1 else (0 : ℕ))
  have bound := M31TranslatedMarginals.success_bound slots path hits success 3
    (by simp [success])
  simp only [success, decide_eq_true_eq, hc] at bound
  omega

end M31.PairDeadline

import Mathlib.Tactic

namespace M31.PrefixMultiplicity

def bucket (x : ℕ) := x / 524288

theorem fits (x : ℕ) (hx : x < 2^31) : bucket x < 4096 := by
  unfold bucket
  omega

theorem contiguous (a b c : ℕ) (hab : a ≤ b) (hbc : b ≤ c)
    (h : bucket a = bucket c) : bucket b = bucket a := by
  unfold bucket at *
  omega

theorem count_in_bucket (xs : List ℕ) (k : ℕ) :
    (xs.filter (fun x => decide (bucket x = bucket k))).count k = xs.count k := by
  induction xs with
  | nil => rfl
  | cons a xs ih =>
    by_cases hk : a = k
    · subst a
      simp [ih]
    · by_cases hb : bucket a = bucket k <;> simp [hk, hb, ih]

end M31.PrefixMultiplicity

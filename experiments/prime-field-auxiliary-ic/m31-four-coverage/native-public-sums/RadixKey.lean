import Mathlib.Tactic

namespace M31.RadixKey

def lo (x : ℕ) := x % 2048
def mid (x : ℕ) := (x / 2048) % 2048
def hi (x : ℕ) := (x / 4194304) % 2048

theorem reconstruct (x : ℕ) (hx : x < 2^32) :
    x = hi x * 4194304 + mid x * 2048 + lo x := by
  unfold hi mid lo
  norm_num at hx
  omega

/-- Stable passes from low to high priority order by this lexicographic key. -/
theorem digit_order (x y : ℕ) (hx : x < 2^32) (hy : y < 2^32) :
    x < y ↔ hi x < hi y ∨ hi x = hi y ∧
      (mid x < mid y ∨ mid x = mid y ∧ lo x < lo y) := by
  have xrec := reconstruct x hx
  have yrec := reconstruct y hy
  have bounded (k : ℕ) : lo k < 2048 ∧ mid k < 2048 :=
    ⟨Nat.mod_lt _ (by decide), Nat.mod_lt _ (by decide)⟩
  obtain ⟨xl, xm⟩ := bounded x
  obtain ⟨yl, ym⟩ := bounded y
  omega

end M31.RadixKey

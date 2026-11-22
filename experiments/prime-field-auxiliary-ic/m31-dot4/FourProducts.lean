import Mathlib
def foldM31 (s : ℕ) := s % 2147483648 + s / 2147483648
theorem fold_mod (s : ℕ) : foldM31 s % 2147483647 = s % 2147483647 := by
  have h := Nat.mod_add_div s 2147483648
  unfold foldM31
  omega
theorem fold_twice (s : ℕ) (hs : s < 2^64) :
    let t := foldM31 (foldM31 s)
    (if 2147483647 ≤ t then t-2147483647 else t) = s % 2147483647 := by
  have h : foldM31 (foldM31 s) % 2147483647 = s % 2147483647 := (fold_mod _).trans (fold_mod s)
  dsimp
  unfold foldM31 at *
  split <;> omega
theorem four_products_fit (x y z w : ℕ) (hx : x ≤ 2147483646^2) (hy : y ≤ 2147483646^2)
    (hz : z ≤ 2147483646^2) (hw : w ≤ 2147483646^2) : x+y+z+w < 2^64 := by omega

/-- The two accumulation orders used by the benchmark agree for all products. -/
theorem defer_reductions (p a b c d : ℕ) :
    (a % p + b % p + c % p + d % p) % p = (a + b + c + d) % p := by
  exact (((Nat.mod_modEq a p).add (Nat.mod_modEq b p)).add
    (Nat.mod_modEq c p)).add (Nat.mod_modEq d p)

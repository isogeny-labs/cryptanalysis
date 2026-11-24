import Mathlib.Tactic

namespace M31DotBlocks

abbrev p : Nat := 2147483647
abbrev radix : Nat := 2147483648
def fold (s : Nat) := s % radix + s / radix

theorem block_bound (a b : Fin 4 → Nat) (ha : ∀ i, a i < p) (hb : ∀ i, b i < p) :
    (∑ i, a i * b i) ≤ 4*(p-1)^2 := by
  calc
    _ ≤ ∑ _ : Fin 4, (p-1)*(p-1) := Finset.sum_le_sum fun i _ =>
      Nat.mul_le_mul (by have := ha i; omega) (by have := hb i; omega)
    _ = _ := by simp [pow_two]

theorem block_fits : 4*(p-1)^2 < 2^64 := by decide

theorem fold_correct (s : Nat) : fold s % p = s % p := by unfold fold p radix; omega

theorem fold_bound (s : Nat) (h : s ≤ 4*(p-1)^2) : fold s < 5*radix := by
  unfold fold radix p at *
  omega

theorem sum_correct (blocks : List Nat) :
    (blocks.map fold).sum % p = blocks.sum % p := by
  induction blocks with
  | nil => rfl
  | cons s ss ih =>
    simp only [List.map_cons,List.sum_cons]
    rw [Nat.add_mod, fold_correct, ih, ← Nat.add_mod]

-- Counts both vector lanes, so the final horizontal add is covered as well.
theorem sum_fits (blocks : List Nat) (size : blocks.length ≤ 2^30)
    (safe : ∀ s ∈ blocks, s ≤ 4*(p-1)^2) : (blocks.map fold).sum < 2^64 := by
  have bound : (blocks.map fold).sum ≤ blocks.length * (5*radix) := by
    induction blocks with
    | nil => simp
    | cons s ss ih =>
      have hs := fold_bound s (safe s List.mem_cons_self)
      have h := ih (by simp at size; omega)
        (fun t ht => safe t (List.mem_cons_of_mem s ht))
      change fold s + (ss.map fold).sum ≤ (ss.length + 1) * (5*radix)
      rw [Nat.add_mul, Nat.one_mul]
      omega
  unfold radix at *
  omega

end M31DotBlocks

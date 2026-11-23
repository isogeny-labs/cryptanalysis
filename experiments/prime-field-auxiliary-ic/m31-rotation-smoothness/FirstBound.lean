import Mathlib

namespace M31FirstBound

/-- The three low bits encode the invariant character and one of four bands. -/
def packed (key sign band : ℕ) := 8 * key + 4 * sign + band

theorem decode {key sign band : ℕ} (hs : sign < 2) (hb : band < 4) :
    (packed key sign band / 8, packed key sign band / 4 % 2, packed key sign band % 4) =
      (key, sign, band) := by
  unfold packed
  apply Prod.ext
  · omega
  · apply Prod.ext <;> dsimp <;> omega

theorem sameOrbitOrder (key sign i j : ℕ) :
    packed key sign i ≤ packed key sign j ↔ i ≤ j := by
  unfold packed
  omega

/-- At cutoff c, summing contributions by earliest band counts exactly the
orbits with at least one representative at or below c. A weight can be one
orbit, its eligible-coordinate count, or its target-lift count. -/
theorem cumulative (keys : Finset ℕ) (bands : ℕ → Finset ℕ)
    (present : ∀ k, (bands k).Nonempty) (weight : ℕ → ℕ) (c : ℕ) :
    (∑ b ∈ Finset.range (c+1), ∑ k ∈ keys.filter (fun k => (bands k).min' (present k) = b),
      weight k) =
    ∑ k ∈ keys.filter (fun k => ∃ j ∈ bands k, j ≤ c), weight k := by
  rw [Finset.sum_fiberwise_eq_sum_filter]
  congr 1
  ext k
  simp only [Finset.mem_filter, Finset.mem_range]
  constructor
  · rintro ⟨hk, hm⟩
    exact ⟨hk, _, (bands k).min'_mem _, Nat.le_of_lt_succ hm⟩
  · rintro ⟨hk, j, hj, hc⟩
    exact ⟨hk, Nat.lt_succ_of_le (le_trans ((bands k).min'_le j hj) hc)⟩

end M31FirstBound

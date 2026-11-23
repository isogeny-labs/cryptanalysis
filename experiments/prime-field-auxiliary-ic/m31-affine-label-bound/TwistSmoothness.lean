import Mathlib

namespace M31TwistSmoothness

abbrev center : ℕ := 2^31

/-- Inclusive bound on the prime divisors of both candidate orders. -/
def bothSmooth (bound trace : ℕ) : Prop :=
  center - trace ∈ Nat.smoothNumbers (bound + 1) ∧
  center + trace ∈ Nat.smoothNumbers (bound + 1)

instance (b t : ℕ) : Decidable (bothSmooth b t) := by
  unfold bothSmooth
  infer_instance

private def traces (b : ℕ) := (List.range 92682).filter (fun t => decide (bothSmooth b t))

private theorem mem_traces (b t : ℕ) :
    t ∈ traces b ↔ t < 92682 ∧ bothSmooth b t := by simp [traces]

theorem hasseRange (t : ℕ) : t^2 ≤ 4*(center-1) ↔ t < 92682 := by
  constructor
  · intro h
    by_contra! hl
    exact (by decide : ¬ (92682 : ℕ)^2 ≤ 4*(center-1))
      (le_trans (Nat.pow_le_pow_left hl 2) h)
  · intro h
    have hh : t ≤ 92681 := by omega
    exact le_trans (Nat.pow_le_pow_left hh 2) (by decide)

private theorem screening : traces 109 = [0,8192] := by native_decide

theorem simultaneous109 {t : ℕ} (h : t^2 ≤ 4*(center-1)) :
    bothSmooth 109 t ↔ t = 0 ∨ t = 8192 := by
  have ht := (hasseRange t).mp h
  calc
    bothSmooth 109 t ↔ t ∈ traces 109 := by simp [mem_traces, ht]
    _ ↔ t = 0 ∨ t = 8192 := by rw [screening]; simp

theorem thresholdWitness :
    Nat.primeFactorsList (center - 8192) = [2,2,2,2,2,2,2,2,2,2,2,2,2,3,3,3,7,19,73] ∧
    109 ∈ Nat.primeFactorsList (center + 8192) := by native_decide

theorem belowThreshold {b t : ℕ} (hb : b < 109) (ht : t^2 ≤ 4*(center-1))
    (h : bothSmooth b t) : t = 0 := by
  have lift {n : ℕ} (hn : n ∈ Nat.smoothNumbers (b+1)) : n ∈ Nat.smoothNumbers 110 := by
    rw [Nat.mem_smoothNumbers] at hn ⊢
    exact ⟨hn.1, fun q hq => lt_of_lt_of_le (hn.2 q hq) (by omega)⟩
  rcases (simultaneous109 ht).mp ⟨lift h.1, lift h.2⟩ with hz | hz
  · exact hz
  · subst t
    have := (Nat.mem_smoothNumbers.mp h.2).2 109 thresholdWitness.2
    omega

/-- The two archived fixture traces have large prime divisors on both sides. -/
theorem fixtureFactors :
    Nat.primeFactorsList (center + 21645) = [2147505293] ∧
    Nat.primeFactorsList (center - 21645) = [53,40518151] ∧
    Nat.primeFactorsList (center + 22553) = [2147506201] ∧
    Nat.primeFactorsList (center - 22553) = [3,5,13,11012621] := by native_decide

end M31TwistSmoothness

import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace M31TraceSeparation

abbrev p : ℕ := 2147483647

/-- Power sums of the two roots of X² - tX + p. -/
def tr (t : ℤ) : ℕ → ℤ
  | 0 => 2
  | 1 => t
  | k+2 => t * tr t (k+1) - p * tr t k

def count (t : ℤ) (d : ℕ) : ℤ := (p : ℤ)^d + 1 - tr t d

theorem trace_mod (t : ℤ) (k : ℕ) :
    ((tr t (k+1) : ℤ) : ZMod p) = (t : ZMod p)^(k+1) := by
  induction k with
  | zero => simp [tr]
  | succ k ih =>
    simp only [tr, Int.cast_sub, Int.cast_mul, Int.cast_natCast, ZMod.natCast_self,
      zero_mul, sub_zero, ih]
    rw [pow_succ (t : ZMod p) (k+1), mul_comm]

/-- The trace-zero auxiliary count differs from every nonzero-trace-mod-p
count in each positive extension degree. -/
theorem distinct (t : ℤ) (ht : (t : ZMod p) ≠ 0) (k : ℕ) :
    count t (k+1) ≠ count 0 (k+1) := by
  letI : Fact (Nat.Prime p) := ⟨by native_decide⟩
  intro h
  have e : tr t (k+1) = tr 0 (k+1) := by simpa [count] using h
  have f := congrArg (fun z : ℤ => (z : ZMod p)) e
  change ((tr t (k+1) : ℤ) : ZMod p) = ((tr 0 (k+1) : ℤ) : ZMod p) at f
  rw [trace_mod, trace_mod] at f
  exact ht (by simpa using f)

theorem fixture_counts (k : ℕ) :
    count (-21645) (k+1) ≠ count 0 (k+1) ∧ count 21645 (k+1) ≠ count 0 (k+1) :=
  ⟨distinct _ (by decide) _, distinct _ (by decide) _⟩

end M31TraceSeparation

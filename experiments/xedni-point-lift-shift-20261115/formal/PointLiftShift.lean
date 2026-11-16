import Mathlib

namespace XedniPointLiftShift

/-- Bézout gives a vertical-coordinate shift making a rational chord slope integral. -/
theorem exists_shift_of_gcd_one (p d dy : ℤ) (hg : Int.gcd p d = 1) :
    ∃ k : ℤ, d ∣ dy + k * p := by
  have hb := Int.gcd_eq_gcd_ab p d
  rw [hg] at hb
  refine ⟨-dy * Int.gcdA p d, ⟨dy * Int.gcdB p d, ?_⟩⟩
  linear_combination dy * hb

/-- A nonzero coordinate difference smaller than a prime admits such a shift. -/
theorem exists_shift_of_prime (p d : ℕ) (dy : ℤ)
    (hp : Nat.Prime p) (hd : 0 < d) (hlt : d < p) :
    ∃ k : ℤ, (d : ℤ) ∣ dy + k * (p : ℤ) := by
  have hcop : Nat.Coprime p d := (hp.coprime_iff_not_dvd).mpr (by
    intro hdiv
    exact (not_le_of_gt hlt) (Nat.le_of_dvd hd hdiv))
  have hg : Int.gcd (p : ℤ) (d : ℤ) = 1 := by
    simpa [Int.gcd, Nat.Coprime] using hcop
  exact exists_shift_of_gcd_one (p : ℤ) (d : ℤ) dy hg

#print axioms exists_shift_of_gcd_one
#print axioms exists_shift_of_prime

end XedniPointLiftShift

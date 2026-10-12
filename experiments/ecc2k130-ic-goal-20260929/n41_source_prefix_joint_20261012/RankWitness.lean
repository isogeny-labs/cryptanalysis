/- The modular cancellation step for six exclusive pivot columns. -/
import Std

namespace RankWitness

def modulus : Nat := 549756390943

def pivotCoefficient : Fin 6 → Nat
  | 0 => 500675087208
  | 1 => 148692722092
  | 2 => 49081303735
  | 3 => 513703398366
  | 4 => 369491428954
  | 5 => 36052992577

private theorem all_pivot_coefficients_coprime :
    ∀ i : Fin 6, Nat.Coprime modulus (pivotCoefficient i) := by
  decide

theorem pivotCoefficient_coprime (i : Fin 6) :
    Nat.Coprime modulus (pivotCoefficient i) :=
  all_pivot_coefficients_coprime i

/-- If evaluating a six-row linear combination at six exclusive columns
    gives zero modulo the subgroup order, all six coefficients vanish. -/
theorem exclusive_pivots_force_zero
    (a : Fin 6 → Nat)
    (bounded : ∀ i, a i < modulus)
    (zero_at_pivots : ∀ i, modulus ∣ a i * pivotCoefficient i) :
    ∀ i, a i = 0 := by
  intro i
  have coprime := pivotCoefficient_coprime i
  have divisible := Nat.Coprime.dvd_of_dvd_mul_right coprime (zero_at_pivots i)
  exact Nat.eq_zero_of_dvd_of_lt divisible (bounded i)

#print axioms pivotCoefficient_coprime
#print axioms exclusive_pivots_force_zero

end RankWitness

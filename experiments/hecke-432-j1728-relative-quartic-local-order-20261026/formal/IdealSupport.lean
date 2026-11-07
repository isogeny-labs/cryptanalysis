import Mathlib.RingTheory.Ideal.Maps
import Mathlib.Tactic.NormNum

namespace J1728QuarticIdealSupport

variable {R : Type*} [CommRing R]

/-- A generator fixed by an automorphism remains in the transported ideal. -/
theorem fixed_generator_in_transport (σ : R ≃+* R) (D : Ideal R) (a : R)
    (ha : a ∈ D) (hfix : σ a = a) : a ∈ D.map σ.toRingHom := by
  rw [← hfix]
  exact Ideal.mem_map_of_mem σ.toRingHom ha

#print axioms fixed_generator_in_transport

/-- An ideal containing an element excluded by a prime cannot lie in that prime. -/
theorem fixed_generator_excludes_prime (σ : R ≃+* R) (D P : Ideal R) (a : R)
    (ha : a ∈ D) (hfix : σ a = a) (hnot : a ∉ P) :
    ¬ D.map σ.toRingHom ≤ P := by
  intro h
  exact hnot (h (fixed_generator_in_transport σ D a ha hfix))

#print axioms fixed_generator_excludes_prime

theorem selected_primes_do_not_divide_96 :
    ¬ (7 : ℕ) ∣ 96 ∧ ¬ (11 : ℕ) ∣ 96 ∧
      ¬ (23 : ℕ) ∣ 96 ∧ ¬ (31 : ℕ) ∣ 96 := by
  norm_num

#print axioms selected_primes_do_not_divide_96

end J1728QuarticIdealSupport

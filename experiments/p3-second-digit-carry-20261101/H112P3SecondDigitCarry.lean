import Mathlib.Algebra.Group.Hom.Basic
import Mathlib.Tactic

/-!
# H112: p³ second-digit halving-carry interfaces

The empirical premise that one of 144 frozen predicates is exact is not an
axiom here. These theorems cover the structural and conditional algorithmic
path only.
-/

namespace H112P3SecondDigitCarry

section Carry

variable {Q A : Type*}
variable [AddCommGroup Q] [AddCommGroup A]

def carry (liftSection : Q → A) (half target : Q) : A :=
  2 • liftSection half - liftSection target

theorem carry_mem_reduction_kernel
    (reduction : A →+ Q) (liftSection : Q → A) (half target : Q)
    (hsection : ∀ q, reduction (liftSection q) = q)
    (hhalf : 2 • half = target) :
    reduction (carry liftSection half target) = 0 := by
  simp [carry, hsection, hhalf]

theorem homomorphic_section_carry_zero
    (liftSection : Q →+ A) (half target : Q) (hhalf : 2 • half = target) :
    carry liftSection half target = 0 := by
  simp [carry, ← liftSection.map_nsmul, hhalf]

end Carry

section Digits

def lowDigit (p word : ℕ) : ℕ := word % p
def highDigit (p word : ℕ) : ℕ := word / p

theorem digit_recombination (p word : ℕ) :
    lowDigit p word + p * highDigit p word = word := by
  exact Nat.mod_add_div word p

theorem highDigit_lt
    (p word : ℕ) (hp : 0 < p) (hword : word < p * p) :
    highDigit p word < p := by
  exact (Nat.div_lt_iff_lt_mul hp).2 hword

end Digits

section Recovery

variable {Point Value : Type*}

theorem exact_predicate_supplies_parity
    (observable : Point → Value) (predicate : Value → ℕ) (scalar : Point → ℕ)
    (hexact : ∀ q, predicate (observable q) = scalar q % 2) (q : Point) :
    predicate (observable q) = scalar q % 2 := by
  exact hexact q

def reconstruct (oracle : ℕ → ℕ) : ℕ → ℕ
  | 0 => 0
  | k + 1 => oracle (k + 1) + 2 * reconstruct oracle ((k + 1) / 2)
termination_by k => k
decreasing_by omega

theorem reconstruct_eq (oracle : ℕ → ℕ) (hexact : ∀ k, oracle k = k % 2) :
    ∀ k, reconstruct oracle k = k := by
  intro k
  induction k using Nat.strong_induction_on with
  | h k ih =>
      cases k with
      | zero => simp [reconstruct]
      | succ n =>
          rw [reconstruct, hexact, ih ((n + 1) / 2) (by omega)]
          omega

theorem verified_scalar_unique
    {Scalar Point : Type*} (mul : Scalar → Point) (target : Point)
    (candidate trueScalar : Scalar) (hcandidate : mul candidate = target)
    (htrue : mul trueScalar = target) (hinjective : Function.Injective mul) :
    candidate = trueScalar := by
  apply hinjective
  rw [hcandidate, htrue]

end Recovery

section Cost

def totalCost
    (setup p3Lift carryQueries predicates halving verify controls checks : ℕ) : ℕ :=
  setup + p3Lift + carryQueries + predicates + halving + verify + controls + checks

theorem totalCost_bound
    (setup p3Lift carryQueries predicates halving verify controls checks budget : ℕ)
    (h : setup + p3Lift + carryQueries + predicates + halving + verify + controls + checks ≤ budget) :
    totalCost setup p3Lift carryQueries predicates halving verify controls checks ≤ budget := by
  exact h

end Cost

#print axioms carry_mem_reduction_kernel
#print axioms homomorphic_section_carry_zero
#print axioms digit_recombination
#print axioms highDigit_lt
#print axioms exact_predicate_supplies_parity
#print axioms reconstruct_eq
#print axioms verified_scalar_unique
#print axioms totalCost_bound

end H112P3SecondDigitCarry

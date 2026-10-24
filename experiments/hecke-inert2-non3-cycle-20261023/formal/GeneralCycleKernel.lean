module

public import Mathlib.Tactic.Linarith
public import Mathlib.Tactic.Ring
public import Mathlib.Algebra.Ring.Rat

/-! The rational three-term cycle kernel, with arbitrary positive cycle length. -/
namespace GeneralCycleKernel

public theorem period_three (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0) (i : ℤ) :
    x (i + 3) = x i := by
  have h0 := h i
  have h1 : x (i + 1) + x (i + 2) + x (i + 3) = 0 := by
    simpa [add_assoc] using h (i + 1)
  linarith

public theorem period_three_mul (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0)
    (n : ℕ) (i : ℤ) : x (i + 3 * (n : ℤ)) = x i := by
  induction n with
  | zero => simp
  | succ n ih =>
      calc
        x (i + 3 * ((n + 1 : ℕ) : ℤ)) = x ((i + 3 * (n : ℤ)) + 3) := by
          congr 1
          push_cast
          ring
        _ = x (i + 3 * (n : ℤ)) := period_three x h (i + 3 * (n : ℤ))
        _ = x i := ih

public theorem nonmultiple_trivial (x : ℤ → ℚ) (n : ℕ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0)
    (hn : ∀ i, x (i + (n : ℤ)) = x i)
    (hmod : n % 3 ≠ 0) (i : ℤ) : x i = 0 := by
  have hdiv : n = 3 * (n / 3) + n % 3 := by omega
  have hdivZ : (n : ℤ) = 3 * ((n / 3 : ℕ) : ℤ) + ((n % 3 : ℕ) : ℤ) := by
    exact_mod_cast hdiv
  have hrem (j : ℤ) : x (j + ((n % 3 : ℕ) : ℤ)) = x j := by
    have hp := hn j
    have hm := period_three_mul x h (n / 3) (j + ((n % 3 : ℕ) : ℤ))
    have heq : j + (n : ℤ) = (j + ((n % 3 : ℕ) : ℤ)) + 3 * ((n / 3 : ℕ) : ℤ) := by
      omega
    rw [heq] at hp
    exact hm.symm.trans hp
  have hlt : n % 3 < 3 := Nat.mod_lt _ (by decide)
  have hcase : n % 3 = 1 ∨ n % 3 = 2 := by omega
  have hstep (j : ℤ) : x (j + 1) = x j := by
    rcases hcase with h1 | h2
    · simpa [h1] using hrem j
    · have hstep2 (k : ℤ) : x (k + 2) = x k := by
        simpa [h2] using hrem k
      have hs := hstep2 (j + 1)
      have hp := period_three x h j
      have heq : (j + 1) + 2 = j + 3 := by ring
      rw [heq] at hs
      exact hs.symm.trans hp
  have hnext := hstep i
  have hnext2 := hstep (i + 1)
  have heq : (i + 1) + 1 = i + 2 := by ring
  rw [heq] at hnext2
  linarith [h i]

public def periodicPair (a b : ℚ) (i : ℤ) : ℚ :=
  if i % 3 = 0 then a else if i % 3 = 1 then b else -a-b

public theorem periodicPair_zero (a b : ℚ) : periodicPair a b 0 = a := by
  simp [periodicPair]

public theorem periodicPair_one (a b : ℚ) : periodicPair a b 1 = b := by
  simp [periodicPair]

public theorem periodicPair_recurrence (a b : ℚ) (i : ℤ) :
    periodicPair a b i + periodicPair a b (i + 1) + periodicPair a b (i + 2) = 0 := by
  have hrange : i % 3 = 0 ∨ i % 3 = 1 ∨ i % 3 = 2 := by omega
  rcases hrange with h0 | h1 | h2
  · have hnext : (i + 1) % 3 = 1 := by omega
    have hnext2 : (i + 2) % 3 = 2 := by omega
    simp [periodicPair, h0, hnext, hnext2]
  · have hnext : (i + 1) % 3 = 2 := by omega
    have hnext2 : (i + 2) % 3 = 0 := by omega
    simp [periodicPair, h1, hnext, hnext2]
  · have hnext : (i + 1) % 3 = 0 := by omega
    have hnext2 : (i + 2) % 3 = 1 := by omega
    simp [periodicPair, h2, hnext, hnext2]
    ring

public theorem periodicPair_cycle (a b : ℚ) (n : ℕ) (i : ℤ)
    (hmod : n % 3 = 0) :
    periodicPair a b (i + (n : ℤ)) = periodicPair a b i := by
  have hmodZ : (n : ℤ) % 3 = 0 := by exact_mod_cast hmod
  have heq : (i + (n : ℤ)) % 3 = i % 3 := by omega
  simp [periodicPair, heq]

public theorem recurrence_has_two_parameters (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0) (i : ℤ) :
    x i = periodicPair (x 0) (x 1) i := by
  let y := periodicPair (x 0) (x 1)
  have hy : ∀ j, y j + y (j + 1) + y (j + 2) = 0 := by
    intro j
    exact periodicPair_recurrence (x 0) (x 1) j
  have hz : x 0 = y 0 := by simp [y, periodicPair_zero]
  have ho : x 1 = y 1 := by simp [y, periodicPair_one]
  have ht : x 2 = y 2 := by
    have hx0 := h 0
    have hy0 := hy 0
    norm_num at hx0 hy0
    linarith
  have all (j : ℤ) : x j = y j ∧ x (j + 1) = y (j + 1) ∧
      x (j + 2) = y (j + 2) := by
    induction j using Int.induction_on with
    | zero =>
        simpa using And.intro hz (And.intro ho ht)
    | succ j ih =>
        rcases ih with ⟨hj, hj1, hj2⟩
        have hj3 : x (j + 3) = y (j + 3) := by
          rw [period_three x h j, period_three y hy j]
          exact hj
        simpa [add_assoc] using And.intro hj1 (And.intro hj2 hj3)
    | pred j ih =>
        rcases ih with ⟨hj, hj1, hj2⟩
        let k : ℤ := -(j : ℤ)
        have hm : x (k - 1) = y (k - 1) := by
          have hx := period_three x h (k - 1)
          have hy' := period_three y hy (k - 1)
          have heq : (k - 1) + 3 = k + 2 := by ring
          rw [heq] at hx hy'
          exact hx.symm.trans (hj2.trans hy')
        simpa [k, sub_eq_add_neg, add_assoc] using And.intro hm (And.intro hj hj1)
  exact (all i).1

public theorem periodicPair_injective (a b c d : ℚ)
    (heq : ∀ i : ℤ, periodicPair a b i = periodicPair c d i) :
    a = c ∧ b = d := by
  constructor
  · simpa [periodicPair_zero] using heq 0
  · simpa [periodicPair_one] using heq 1

public theorem multiple_periodic_solution (n : ℕ) (hmod : n % 3 = 0)
    (a b : ℚ) :
    (∀ i, periodicPair a b i + periodicPair a b (i + 1) +
      periodicPair a b (i + 2) = 0) ∧
    (∀ i, periodicPair a b (i + (n : ℤ)) = periodicPair a b i) := by
  constructor
  · exact periodicPair_recurrence a b
  · intro i
    exact periodicPair_cycle a b n i hmod

public theorem periodic_solution_unique_pair (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0) :
    ∃! pair : ℚ × ℚ, ∀ i, x i = periodicPair pair.1 pair.2 i := by
  refine ⟨(x 0, x 1), ?_, ?_⟩
  · intro i
    exact recurrence_has_two_parameters x h i
  · intro pair hp
    apply Prod.ext
    · have h0 := hp 0
      simpa [periodicPair_zero] using h0.symm
    · have h1 := hp 1
      simpa [periodicPair_one] using h1.symm

end GeneralCycleKernel

#print axioms GeneralCycleKernel.period_three
#print axioms GeneralCycleKernel.period_three_mul
#print axioms GeneralCycleKernel.nonmultiple_trivial
#print axioms GeneralCycleKernel.periodicPair_recurrence
#print axioms GeneralCycleKernel.periodicPair_cycle
#print axioms GeneralCycleKernel.recurrence_has_two_parameters
#print axioms GeneralCycleKernel.periodicPair_injective
#print axioms GeneralCycleKernel.multiple_periodic_solution
#print axioms GeneralCycleKernel.periodic_solution_unique_pair

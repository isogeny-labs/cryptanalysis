import Mathlib.Tactic

namespace M31PackedFiber

/-- Both siblings have the same image under the rational map evaluated by the fold. -/
theorem sibling_image {K : Type*} [Field K] (u v a b : K)
    (prod : u * v = b) (nonzero : b ≠ 0) :
    u + a + b/u = u + a + v ∧ v + a + b/v = u + a + v := by
  have hu : u ≠ 0 := fun h => nonzero (by simp [← prod, h])
  have hv : v ≠ 0 := fun h => nonzero (by simp [← prod, h])
  subst b
  constructor
  · field_simp
  · field_simp
    ring

/-- An address is extended by one sibling choice at each level. -/
def Address : Nat → Type
  | 0 => Unit
  | d+1 => Address d × Bool

theorem injective_levels {X : Type*} (nodes : (d : Nat) → Address d → X)
    (step : Nat → X → X) (depth : Nat)
    (fold : ∀ d < depth, ∀ i b, step d (nodes (d+1) (i,b)) = nodes d i)
    (distinct : ∀ d < depth, ∀ i, nodes (d+1) (i,false) ≠ nodes (d+1) (i,true)) :
    ∀ d ≤ depth, Function.Injective (nodes d) := by
  intro d
  induction d with
  | zero => intro _ a b _; cases a; cases b; rfl
  | succ d ih =>
    intro hd
    have lt : d < depth := hd
    rintro ⟨i,b⟩ ⟨j,c⟩ he
    have eq := ih (Nat.le_of_lt lt) ((fold d lt i b).symm.trans ((congrArg (step d) he).trans (fold d lt j c)))
    subst j
    cases b <;> cases c
    · rfl
    · exact (distinct d lt i he).elim
    · exact (distinct d lt i he.symm).elim
    · rfl

/-- The first k iterations of a half-buffer fold with stride n. -/
def foldPrefix {X : Type*} (n : Nat) (combine : X → X → X) (xs : Nat → X) :
    Nat → Nat → X
  | 0 => xs
  | k+1 =>
    let before := foldPrefix n combine xs k
    Function.update before k (combine (before k) (before (k+n)))

theorem foldPrefix_spec {X : Type*} (n : Nat) (combine : X → X → X) (xs : Nat → X)
    (k j : Nat) : foldPrefix n combine xs k j =
    if j < k then combine (xs j) (xs (j+n)) else xs j := by
  induction k generalizing j with
  | zero => simp [foldPrefix]
  | succ k ih =>
    by_cases h : j = k
    · subst j
      simp [foldPrefix, ih]
    · rw [foldPrefix, Function.update_of_ne h, ih]
      by_cases hj : j < k
      · simp [hj, Nat.lt_succ_of_lt hj]
      · have hj' : ¬ j < k+1 := by omega
        simp [hj, hj']

/-- Distinct half-buffer pairs and distinct folded values imply distinct input slots. -/
theorem slots_injective {X Y : Type*} (n : Nat) (x : Nat → X) (f : X → Y)
    (pair : ∀ i < n, f (x (i+n)) = f (x i))
    (different : ∀ i < n, x i ≠ x (i+n))
    (parents : ∀ i < n, ∀ j < n, f (x i) = f (x j) → i = j)
    (a b : Nat) (ha : a < n+n) (hb : b < n+n) (eq : x a = x b) : a = b := by
  have image := congrArg f eq
  by_cases h₁ : a < n <;> by_cases h₂ : b < n
  · exact parents a h₁ b h₂ image
  · obtain ⟨j, rfl⟩ : ∃ j, b = j+n := ⟨b-n, by omega⟩
    have hj : j < n := by omega
    have e := parents a h₁ j hj (image.trans (pair j hj))
    subst a
    exact False.elim (different j hj eq)
  · obtain ⟨i, rfl⟩ : ∃ i, a = i+n := ⟨a-n, by omega⟩
    have hi : i < n := by omega
    have e := parents i hi b h₂ ((pair i hi).symm.trans image)
    subst b
    exact False.elim (different i hi eq.symm)
  · obtain ⟨i, rfl⟩ : ∃ i, a = i+n := ⟨a-n, by omega⟩
    obtain ⟨j, rfl⟩ : ∃ j, b = j+n := ⟨b-n, by omega⟩
    have hi : i < n := by omega
    have hj : j < n := by omega
    exact congrArg (· + n) (parents i hi j hj ((pair i hi).symm.trans (image.trans (pair j hj))))

end M31PackedFiber

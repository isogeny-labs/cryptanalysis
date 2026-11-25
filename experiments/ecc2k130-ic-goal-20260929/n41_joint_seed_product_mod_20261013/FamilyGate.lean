import Std

/-! If reduction preserves evaluation at a fixed norm root, a modular product
preserves the zero test for every factor family. The concrete polynomial
remainder/evaluation bridge is checked computationally in this experiment. -/
namespace FamilyGate

variable {P K A : Type}

def product [One K] [Mul K] (xs : List A) (f : A → K) : K :=
  xs.foldr (fun x rest => f x * rest) 1

def modularFold [Mul P] (reduce : P → P) : List P → P → P
  | [], acc => acc
  | x :: xs, acc => modularFold reduce xs (reduce (acc * x))

theorem eval_modularFold [One K] [Mul K] [Mul P] (reduce : P → P)
    (evaluate : P → K) (xs : List P) (acc : P)
    (hreduce : ∀ x, evaluate (reduce x) = evaluate x)
    (hmul : ∀ x y, evaluate (x * y) = evaluate x * evaluate y)
    (hmul_one : ∀ x : K, x * 1 = x)
    (hassoc : ∀ x y z : K, (x * y) * z = x * (y * z)) :
    evaluate (modularFold reduce xs acc) =
      evaluate acc * product xs evaluate := by
  induction xs generalizing acc with
  | nil => simp [modularFold, product, hmul_one]
  | cons x rest ih =>
      simp only [modularFold, product]
      rw [ih, hreduce, hmul]
      exact hassoc (evaluate acc) (evaluate x) (product rest evaluate)

theorem product_zero_iff [One K] [Mul K] [Zero K] (xs : List A) (f : A → K)
    (one_ne_zero : (1 : K) ≠ 0)
    (mul_zero_iff : ∀ a b : K, a * b = 0 ↔ a = 0 ∨ b = 0) :
    product xs f = 0 ↔ ∃ x ∈ xs, f x = 0 := by
  induction xs with
  | nil => simp [product, one_ne_zero]
  | cons x rest ih =>
      change f x * product rest f = 0 ↔ ∃ y ∈ x :: rest, f y = 0
      rw [mul_zero_iff, ih]
      constructor
      · intro h
        rcases h with hx | ⟨y, hy, hfy⟩
        · exact ⟨x, by simp, hx⟩
        · exact ⟨y, by simp [hy], hfy⟩
      · rintro ⟨y, hy, hfy⟩
        rcases List.mem_cons.mp hy with rfl | htail
        · exact Or.inl hfy
        · exact Or.inr ⟨y, htail, hfy⟩

theorem modular_gate_exact [One K] [Mul K] [Zero K] [Mul P] [One P]
    (reduce : P → P) (evaluate : P → K) (xs : List P)
    (hone : evaluate (1 : P) = 1)
    (hreduce : ∀ x, evaluate (reduce x) = evaluate x)
    (hmul : ∀ x y, evaluate (x * y) = evaluate x * evaluate y)
    (hmul_one : ∀ x : K, x * 1 = x)
    (hone_mul : ∀ x : K, 1 * x = x)
    (hassoc : ∀ x y z : K, (x * y) * z = x * (y * z))
    (one_ne_zero : (1 : K) ≠ 0)
    (mul_zero_iff : ∀ a b : K, a * b = 0 ↔ a = 0 ∨ b = 0) :
    evaluate (modularFold reduce xs 1) = 0 ↔
      ∃ x ∈ xs, evaluate x = 0 := by
  rw [eval_modularFold reduce evaluate xs 1 hreduce hmul hmul_one hassoc,
      hone, hone_mul]
  exact product_zero_iff xs evaluate one_ne_zero mul_zero_iff

#print axioms FamilyGate.eval_modularFold
#print axioms FamilyGate.modular_gate_exact
end FamilyGate

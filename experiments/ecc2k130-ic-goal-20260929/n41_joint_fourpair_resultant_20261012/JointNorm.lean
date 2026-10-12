import Std

/- The finite-root zero criterion used by the two nested resultants.
   A field satisfies the two explicit algebraic hypotheses.  Connecting
   this product to Sage's polynomial resultant is a separate bridge. -/

namespace JointNorm

variable {K : Type} [Zero K] [One K] [Mul K]

def product {α : Type} (xs : List α) (f : α → K) : K :=
  xs.foldr (fun x rest => f x * rest) 1

theorem product_zero_iff {α : Type} (xs : List α) (f : α → K)
    (one_ne_zero : (1 : K) ≠ 0)
    (mul_zero_iff : ∀ a b : K, a * b = 0 ↔ a = 0 ∨ b = 0) :
    product xs f = 0 ↔ ∃ x ∈ xs, f x = 0 := by
  induction xs with
  | nil => simp [product, one_ne_zero]
  | cons x xs ih =>
      change f x * product xs f = 0 ↔ ∃ y ∈ x :: xs, f y = 0
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

def jointProduct {α β : Type} (left : List α) (right : List β)
    (upper : α → β → K) : K :=
  product left (fun u => product right (upper u))

theorem joint_zero_iff {α β : Type} (left : List α) (right : List β)
    (upper : α → β → K)
    (one_ne_zero : (1 : K) ≠ 0)
    (mul_zero_iff : ∀ a b : K, a * b = 0 ↔ a = 0 ∨ b = 0) :
    jointProduct left right upper = 0 ↔
      ∃ u ∈ left, ∃ v ∈ right, upper u v = 0 := by
  unfold jointProduct
  rw [product_zero_iff left (fun u => product right (upper u)) one_ne_zero mul_zero_iff]
  constructor
  · rintro ⟨u, hu, hproduct⟩
    exact ⟨u, hu, (product_zero_iff right (upper u) one_ne_zero mul_zero_iff).mp hproduct⟩
  · rintro ⟨u, hu, v, hv, hz⟩
    exact ⟨u, hu, (product_zero_iff right (upper u) one_ne_zero mul_zero_iff).mpr ⟨v, hv, hz⟩⟩

#print axioms JointNorm.product_zero_iff
#print axioms JointNorm.joint_zero_iff

end JointNorm

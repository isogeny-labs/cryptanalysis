/-! A characteristic-two linear functional has the same value on paired
roots whenever their difference belongs to a subspace it annihilates. -/
namespace DualRootSignature

structure BinaryAdd (F : Type) where
  add : F → F → F
  zero : F
  add_self : ∀ a, add a a = zero

structure Functional (F : Type) (A : BinaryAdd F) where
  eval : F → Bool
  map_add : ∀ a b, eval (A.add a b) = xor (eval a) (eval b)

variable {F : Type} (A : BinaryAdd F) (L : Functional F A)

theorem paired_roots_agree (U : F → Prop) (a₀ a₁ : F)
    (difference_in_U : U (A.add a₀ a₁))
    (annihilates_U : ∀ x, U x → L.eval x = false) :
    L.eval a₀ = L.eval a₁ := by
  have h : xor (L.eval a₀) (L.eval a₁) = false := by
    rw [← L.map_add]
    exact annihilates_U _ difference_in_U
  cases h₀ : L.eval a₀ <;> cases h₁ : L.eval a₁ <;>
    simp_all

theorem zero_functional_on_pair (U : F → Prop) (a₀ a₁ : F)
    (difference_in_U : U (A.add a₀ a₁))
    (annihilates_U : ∀ x, U x → L.eval x = false)
    (first_zero : L.eval a₀ = false) : L.eval a₁ = false := by
  rw [← paired_roots_agree A L U a₀ a₁ difference_in_U annihilates_U]
  exact first_zero

#print axioms DualRootSignature.paired_roots_agree
#print axioms DualRootSignature.zero_functional_on_pair

end DualRootSignature

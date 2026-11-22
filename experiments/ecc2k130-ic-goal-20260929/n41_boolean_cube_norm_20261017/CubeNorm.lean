import Std

/-! Exact one-bit norm expansion and zero detection for a recursive cube. -/
namespace CubeNorm

structure Domain (F : Type) where
  zero : F
  add : F → F → F
  mul : F → F → F
  mul_add : ∀ a b c, mul a (add b c) = add (mul a b) (mul a c)
  mul_eq_zero : ∀ a b, mul a b = zero ↔ a = zero ∨ b = zero

variable {F : Type} (D : Domain F)

def evalBit (a₀ a₁ : F) (bit : Bool) : F :=
  if bit then D.add a₀ a₁ else a₀

theorem one_bit_norm (a₀ a₁ : F) :
    D.mul (evalBit D a₀ a₁ false) (evalBit D a₀ a₁ true) =
      D.add (D.mul a₀ a₀) (D.mul a₀ a₁) := by
  simp only [evalBit, Bool.false_eq_true, ↓reduceIte, D.mul_add]

inductive Cube (F : Type) where
  | leaf : F → Cube F
  | split : Cube F → Cube F → Cube F

def norm : Cube F → F
  | .leaf value => value
  | .split left right => D.mul (norm left) (norm right)

def hasZero : Cube F → Prop
  | .leaf value => value = D.zero
  | .split left right => hasZero left ∨ hasZero right

theorem norm_zero_iff (cube : Cube F) :
    norm D cube = D.zero ↔ hasZero D cube := by
  induction cube with
  | leaf value => rfl
  | split left right left_ih right_ih =>
      simp only [norm, hasZero, D.mul_eq_zero, left_ih, right_ih]

#print axioms CubeNorm.one_bit_norm
#print axioms CubeNorm.norm_zero_iff

end CubeNorm

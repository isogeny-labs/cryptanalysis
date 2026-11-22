import Mathlib

/-- Once the product inverse is known, each child inverse follows from the sibling. -/
theorem splitProductInverse {F : Type*} [Field F] (a b : F) (ha : a ≠ 0) (hb : b ≠ 0) :
    (a*b)⁻¹*b = a⁻¹ ∧ (a*b)⁻¹*a = b⁻¹ := by
  constructor <;> field_simp

/-- The local replacement at zero and the final mask preserve totalized inversion. -/
theorem maskInverse {F : Type*} [Field F] [DecidableEq F] (x : F) :
    (if x=0 then 0 else (if x=0 then 1 else x)⁻¹) = x⁻¹ := by
  by_cases h : x=0 <;> simp [h]

namespace M31Inverse
inductive Tree (α : Type*) where
  | leaf (x : α)
  | branch (l r : Tree α)

variable {F : Type*} [Field F] [DecidableEq F]
def product : Tree F → F
  | .leaf x => if x=0 then 1 else x
  | .branch l r => product l * product r

theorem product_ne_zero (t : Tree F) : product t ≠ 0 := by
  induction t with
  | leaf x => by_cases h : x=0 <;> simp [product,h]
  | branch l r hl hr => exact mul_ne_zero hl hr

def descend : Tree F → F → Tree F
  | .leaf x, v => .leaf (if x=0 then 0 else v)
  | .branch l r, v => .branch (descend l (v*product r)) (descend r (v*product l))

def invertLeaves : Tree F → Tree F
  | .leaf x => .leaf x⁻¹
  | .branch l r => .branch (invertLeaves l) (invertLeaves r)

theorem allLeaves (t : Tree F) : descend t (product t)⁻¹ = invertLeaves t := by
  induction t with
  | leaf x => simp only [descend,product,invertLeaves]; rw [maskInverse]
  | branch l r hl hr =>
    obtain ⟨h₁,h₂⟩ := splitProductInverse _ _ (product_ne_zero l) (product_ne_zero r)
    simp only [descend,product,invertLeaves,h₁,h₂,hl,hr]
end M31Inverse

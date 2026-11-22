import Std

namespace SignedOrientation

/-- Orient a coefficient vector by its first nonzero entry. -/
def orientation : List Int → Int
  | [] => 0
  | x::xs => if x = 0 then orientation xs else x

theorem flip (v : List Int) :
    orientation (v.map Neg.neg) = -(orientation v) := by
  induction v with
  | nil => decide
  | cons x xs ih =>
    by_cases h : x = 0 <;> simp [orientation,h,ih]

theorem zero_iff (v : List Int) :
    orientation v = 0 ↔ ∀ a ∈ v, a = 0 := by
  induction v with
  | nil => simp [orientation]
  | cons x xs ih => by_cases h : x = 0 <;> simp [orientation,h,ih]

theorem unique_orientation (v : List Int) (nonzero : ∃ a ∈ v, a ≠ 0) :
    (0 < orientation v ↔ ¬ 0 < orientation (v.map Neg.neg)) ∧
    orientation v ≠ orientation (v.map Neg.neg) := by
  obtain ⟨a,ha,hn⟩ := nonzero
  have h : orientation v ≠ 0 := fun bad => hn ((zero_iff v).mp bad a ha)
  rw [flip]
  omega

/-- Backwards step for a block of nonzero affine denominators. -/
theorem undo_product {F : Type} [Lean.Grind.CommRing F] (partialProduct d inverse : F)
    (h : inverse * (partialProduct * d) = 1) :
    (inverse * partialProduct) * d = 1 ∧ (inverse * d) * partialProduct = 1 := by
  constructor <;> grind

#print axioms undo_product
#print axioms unique_orientation
end SignedOrientation

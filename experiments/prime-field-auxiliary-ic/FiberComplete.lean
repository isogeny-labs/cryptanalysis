import Std

namespace FiberComplete
open Lean.Grind

/-- Cleared-denominator equation for a finite preimage. A nonzero residue excludes the pole. -/
def mapsTo {F : Type} [Field F] (r A B x z : F) : Prop :=
  (x-r)*(z-(x-r)-A) = B

theorem mapsTo_affine {F : Type} [Field F] (r A B x z i : F)
    (unit : (x-r)*i = 1) : mapsTo r A B x z ↔ z = (x-r)+A+B*i := by
  unfold mapsTo
  constructor <;> intro h <;> grind

theorem sibling_fiber {F : Type} [Field F] (r A B l t : F)
    (pair : (l-r)*(t-r) = B) (x : F) :
    mapsTo r A B x ((l-r)+(t-r)+A) ↔ x = l ∨ x = t := by
  unfold mapsTo
  constructor
  · intro h
    have zero : (x-l)*(x-t) = 0 := by grind
    rcases Field.of_mul_eq_zero zero with h | h <;> grind
  · rintro (rfl | rfl) <;> grind

theorem pole_excluded {F : Type} [Field F] (r A B z : F) (hb : B ≠ 0) :
    ¬mapsTo r A B r z := by unfold mapsTo; grind

/-- Outer map first. A path only exists when each step is defined. -/
def Path {α : Type} : List (α → α → Prop) → α → α → Prop
| [], x, z => x = z
| f :: fs, x, z => ∃ y, Path fs x y ∧ f y z

inductive FullTree {α : Type} : List (α → α → Prop) → α → List α → Prop
| leaf (x) : FullTree [] x [x]
| branch {fs l r ls rs f z} : FullTree fs l ls → FullTree fs r rs →
    l ≠ r → (∀ y, f y z ↔ y = l ∨ y = r) → FullTree (f::fs) z (ls++rs)

theorem exact_fiber {α : Type} {fs z xs} (t : @FullTree α fs z xs) :
    ∀ x, x ∈ xs ↔ Path fs x z := by
  induction t with
  | leaf a => simp [Path]
  | branch tl tr _hf cover il ir =>
    intro x
    rw [List.mem_append, il, ir]
    constructor
    · rintro (h | h)
      · exact ⟨_,h,(cover _).mpr (Or.inl rfl)⟩
      · exact ⟨_,h,(cover _).mpr (Or.inr rfl)⟩
    · rintro ⟨y,path,last⟩
      rcases (cover y).mp last with rfl | rfl
      · exact Or.inl path
      · exact Or.inr path

/-- The concrete certificate needs a product check and distinct children at
each branch. The parent is fixed by their sum and the public map constants. -/
inductive Certified {F : Type} [Field F] :
    List (F → F → Prop) → F → List F → Prop
| leaf (x) : Certified [] x [x]
| branch {fs l t ls ts r A B} : Certified fs l ls → Certified fs t ts →
    B ≠ 0 → l ≠ t → (l-r)*(t-r) = B →
    Certified (mapsTo r A B :: fs) ((l-r)+(t-r)+A) (ls++ts)

theorem certified_exact {F : Type} [Field F] {fs z xs}
    (tree : @Certified F _ fs z xs) : ∀ x, x ∈ xs ↔ Path fs x z := by
  apply exact_fiber
  induction tree with
  | leaf x => exact .leaf x
  | branch tl tr _ nondup pair il ir =>
    exact .branch il ir nondup (sibling_fiber _ _ _ _ _ pair)

#print axioms certified_exact
#print axioms sibling_fiber
#print axioms pole_excluded
#print axioms exact_fiber
end FiberComplete

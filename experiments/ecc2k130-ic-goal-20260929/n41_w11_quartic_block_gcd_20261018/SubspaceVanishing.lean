import Std
import Init.Grind.Ring.Basic

namespace SubspaceVanishing
open Lean.Grind

/-- The same characteristic-two recurrence used to construct the vanishing
polynomial of an ordered binary basis. -/
def vanishingFn {F : Type} [CommRing F] : List F → F → F
  | [], x => x
  | b :: bs, x =>
      let g := vanishingFn bs
      g x * g x + g b * g x

/-- Binary subset sums of the ordered basis, including zero. -/
inductive binarySpan {F : Type} [Add F] [Zero F] : List F → F → Prop where
  | zero : binarySpan [] 0
  | keep {b bs x} : binarySpan bs x → binarySpan (b :: bs) x
  | take {b bs x} : binarySpan bs x → binarySpan (b :: bs) (x + b)

theorem vanishingFn_add {F : Type} [CommRing F]
    (charTwo : ∀ a : F, a + a = 0) (bs : List F) (x y : F) :
    vanishingFn bs (x + y) = vanishingFn bs x + vanishingFn bs y := by
  induction bs generalizing x y with
  | nil => simp [vanishingFn]
  | cons b bs ih =>
      simp only [vanishingFn]
      rw [ih x y]
      have hz := charTwo ((vanishingFn bs x) * (vanishingFn bs y))
      grind +ring

theorem vanishingFn_zero_on_binarySpan {F : Type} [CommRing F]
    (charTwo : ∀ a : F, a + a = 0) {bs : List F} {x : F}
    (hx : binarySpan bs x) : vanishingFn bs x = 0 := by
  induction hx with
  | zero => simp [vanishingFn]
  | keep h ih =>
      simp only [vanishingFn]
      rw [ih]
      grind +ring
  | take h ih =>
      rename_i b0 bs0 x0
      simp only [vanishingFn]
      rw [vanishingFn_add charTwo bs0 x0 b0, ih]
      have hz := charTwo (vanishingFn bs0 b0 * vanishingFn bs0 b0)
      grind +ring

#print axioms vanishingFn_add
#print axioms vanishingFn_zero_on_binarySpan

end SubspaceVanishing

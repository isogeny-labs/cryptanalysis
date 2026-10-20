import Std
import Init.Grind.Ring.Basic

namespace AffineNorm
open Lean.Grind

/-- Norm over every binary subset sum of an ordered basis. -/
def normFn {F : Type} [CommRing F] : List F → (F → F) → F → F
  | [], h, x => h x
  | b :: bs, h, x =>
      let g := normFn bs h
      g x * g (x + b)

/-- Each insertion doubles the family of factors. -/
theorem normFn_cons {F : Type} [CommRing F]
    (b : F) (bs : List F) (h : F → F) (x : F) :
    normFn (b :: bs) h x = normFn bs h x * normFn bs h (x + b) := rfl

/-- Translation by an inserted binary direction permutes the factors. -/
theorem normFn_translate_head {F : Type} [CommRing F]
    (charTwo : ∀ a : F, a + a = 0)
    (b : F) (bs : List F) (h : F → F) (x : F) :
    normFn (b :: bs) h (x + b) = normFn (b :: bs) h x := by
  simp only [normFn_cons]
  have hb := charTwo b
  have hh : (x + b) + b = x := by
    grind +ring
  rw [hh]
  grind +ring

/-- All finite binary subset sums of an ordered basis. -/
inductive binarySpan {F : Type} [Add F] [Zero F] : List F → F → Prop where
  | zero : binarySpan [] 0
  | keep {b bs x} : binarySpan bs x → binarySpan (b :: bs) x
  | take {b bs x} : binarySpan bs x → binarySpan (b :: bs) (x + b)

theorem normFn_translate_span {F : Type} [CommRing F]
    (charTwo : ∀ a : F, a + a = 0)
    {bs : List F} {y : F} (hy : binarySpan bs y)
    (h : F → F) (x : F) :
    normFn bs h (x + y) = normFn bs h x := by
  induction hy generalizing x with
  | zero =>
      have hz : x + 0 = x := by grind +ring
      rw [hz]
  | keep hy ih =>
      rename_i b bs y
      simp only [normFn_cons]
      rw [ih x]
      have hs : (x + y) + b = (x + b) + y := by grind +ring
      rw [hs, ih (x + b)]
  | take hy ih =>
      rename_i b bs y
      have ht : x + (y + b) = (x + y) + b := by grind +ring
      rw [ht, normFn_translate_head charTwo b bs h (x + y)]
      simp only [normFn_cons]
      rw [ih x]
      have hs : (x + y) + b = (x + b) + y := by grind +ring
      rw [hs, ih (x + b)]

#print axioms normFn_cons
#print axioms normFn_translate_head
#print axioms normFn_translate_span

end AffineNorm

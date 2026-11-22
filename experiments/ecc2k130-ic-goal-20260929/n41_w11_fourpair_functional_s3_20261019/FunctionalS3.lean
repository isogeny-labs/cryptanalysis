import Std
import Init.Grind.Ring.Basic

namespace FunctionalS3
open Lean.Grind

/-- The ordinary branch of the functional S3 quadratic is sound in a
characteristic-two field. The inverse witnesses are explicit hypotheses. -/
theorem quadratic_branch_sound
    {F : Type} [Field F]
    (charTwo : ∀ x : F, x + x = 0)
    (A B D invA invB h e : F)
    (ha : A * invA = 1) (hb : B * invB = 1)
    (hh : h * h + h = A * D * (invB * invB))
    (he : e = 0 ∨ e = 1) :
    let z := (B * invA) * (h + e)
    A * (z * z) + B * z + D = 0 := by
  rcases he with rfl | rfl
  · have hD := charTwo D
    have hzero := charTwo (0 : F)
    grind +ring
  · have hD := charTwo D
    have hone := charTwo (1 : F)
    have hhTwo := charTwo h
    grind +ring

/-- At the exceptional chart A=0, B nonzero, the linear root is exact. -/
theorem linear_branch_sound
    {F : Type} [Field F]
    (charTwo : ∀ x : F, x + x = 0)
    (B D invB : F) (hb : B * invB = 1) :
    B * (D * invB) + D = 0 := by
  have hD := charTwo D
  grind +ring

theorem linear_branch_complete
    {F : Type} [Field F]
    (charTwo : ∀ x : F, x + x = 0)
    (B D invB z : F) (hb : B * invB = 1)
    (hz : B * z + D = 0) :
    z = D * invB := by
  have hD := charTwo D
  grind +ring

/-- Every root of the ordinary quadratic is one of its two functional
branches. The characteristic-two and inverse assumptions are explicit. -/
theorem quadratic_branch_complete
    {F : Type} [Field F]
    (charTwo : ∀ x : F, x + x = 0)
    (A B D invA invB h z : F)
    (ha : A * invA = 1) (hb : B * invB = 1)
    (hh : h * h + h = A * D * (invB * invB))
    (hz : A * (z * z) + B * z + D = 0) :
    z = (B * invA) * h ∨ z = (B * invA) * (h + 1) := by
  let z0 := (B * invA) * h
  let z1 := (B * invA) * (h + 1)
  have hD := charTwo D
  have hB := charTwo B
  have hz0 := charTwo z0
  have hz1 := charTwo z1
  have hone := charTwo (1 : F)
  have hhTwo := charTwo h
  have hfactor : A * (z + z0) * (z + z1) = 0 := by
    dsimp [z0, z1]
    grind +ring
  have hA : A ≠ 0 := by
    intro heq
    have h01 : (0 : F) = 1 := by simpa only [heq, Semiring.zero_mul] using ha
    exact Field.zero_ne_one h01
  rcases Field.of_mul_eq_zero hfactor with hleft | hright
  · rcases Field.of_mul_eq_zero hleft with hzero | hzero
    · exact (hA hzero).elim
    · left
      dsimp [z0] at *
      grind +ring
  · right
    dsimp [z1] at *
    grind +ring

#print axioms FunctionalS3.quadratic_branch_sound
#print axioms FunctionalS3.linear_branch_sound
#print axioms FunctionalS3.linear_branch_complete
#print axioms FunctionalS3.quadratic_branch_complete

end FunctionalS3

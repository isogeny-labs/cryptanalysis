import Std
import Init.Grind.Ring.Basic

namespace FunctionalS3
open Lean.Grind

/-- A nonzero S3 linear coefficient admits a reciprocal witness. The
    Artin-Schreier root plus one branch bit covers every quadratic root,
    including the case where the quadratic coefficient is zero. -/
theorem functional_branch_exists {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (A B D z v h : F)
    (hB : B*v=1)
    (hs3 : A*z^2+B*z+D=0)
    (hh : h^2+h=A*D*v^2) :
    A*z=B*h ∨ A*z=B*(h+1) := by
  let u := A*z*v
  have hu : u^2+u=A*D*v^2 := by
    have hself := charTwo (A*D*v^2)
    dsimp [u]
    grind +ring
  have hdelta : (u+h)^2+(u+h)=0 := by
    have hcross := charTwo (u*h)
    have hq := charTwo (A*D*v^2)
    grind +ring
  have hfactor : (u+h)*((u+h)+1)=0 := by
    grind +ring
  have hsplit : u+h=0 ∨ u+h=1 := by
    rcases Field.of_mul_eq_zero hfactor with hzero | hone
    · exact Or.inl hzero
    · right
      have hself := charTwo 1
      grind +ring
  rcases hsplit with hzero | hone
  · left
    have hself := charTwo h
    dsimp [u] at hzero
    grind +ring
  · right
    have hself := charTwo (h+1)
    dsimp [u] at hone
    grind +ring

#print axioms functional_branch_exists

end FunctionalS3

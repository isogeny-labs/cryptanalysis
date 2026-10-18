import Std
import Init.Grind.Ring.Basic

namespace PairQuadratics
open Lean.Grind

/-- A shared root of the fixed-seed pair quadratic and the S3 quadratic
forces the source quartic eliminant to vanish. -/
theorem common_root_implies_eliminant_zero
    {F : Type} [Field F] (charTwo : ∀ x : F, x+x=0)
    (C p H A B D u : F) (hC : C ≠ 0)
    (hpair : C*u*u+p*u+H=0)
    (hlink : A*u*u+B*u+D=0) :
    A*D*p*p + B*(A*H+C*D)*p +
      (A*H+C*D)*(A*H+C*D) + C*H*B*B = 0 := by
  have htwo : (2 : F)=0 := by
    have hz:=charTwo 1
    grind +ring
  let M : F := A*H+C*D
  let L : F := A*p+B*C
  let g : F := A*D*p*p+B*M*p+M*M+C*H*B*B
  change g=0
  have hlin : L*u+M=0 := by
    have hidentity : L*u+M =
        A*(C*u*u+p*u+H)+C*(A*u*u+B*u+D) := by
      dsimp [L,M]
      grind +ring
    rw [hidentity,hpair,hlink]
    grind +ring
  have hM : M=L*u := by
    grind +ring
  have hcert : C*g=C*M*M+p*M*L+H*L*L := by
    dsimp [g,L,M]
    grind +ring
  have hzero : C*g=0 := by
    calc
      C*g = C*M*M+p*M*L+H*L*L := hcert
      _ = L*L*(C*u*u+p*u+H) := by rw [hM]; grind +ring
      _ = 0 := by rw [hpair]; grind +ring
  have hnonzero : C ≠ 0 := hC
  grind

/-- If the source-pair quadratic has a field root, zero of the eliminant
forces a common root with the S3 quadratic. The proof treats the singular
linear-elimination case `L = 0` separately. -/
theorem eliminant_zero_implies_common_root
    {F : Type} [Field F] (charTwo : ∀ x : F, x+x=0)
    (C p H A B D : F) (hC : C ≠ 0)
    (hsplit : ∃ u : F, C*u*u+p*u+H=0)
    (hg : A*D*p*p+B*(A*H+C*D)*p+
      (A*H+C*D)*(A*H+C*D)+C*H*B*B=0) :
    ∃ u : F, C*u*u+p*u+H=0 ∧ A*u*u+B*u+D=0 := by
  have htwo : (2 : F)=0 := by
    have hz:=charTwo 1
    grind +ring
  let M : F := A*H+C*D
  let L : F := A*p+B*C
  let g : F := A*D*p*p+B*M*p+M*M+C*H*B*B
  have hg' : g=0 := hg
  have hlin_identity (u : F) : L*u+M =
      A*(C*u*u+p*u+H)+C*(A*u*u+B*u+D) := by
    dsimp [L,M]
    grind +ring
  have hcert : C*g=C*M*M+p*M*L+H*L*L := by
    dsimp [g,L,M]
    grind +ring
  by_cases hL : L=0
  · have hM : M=0 := by
      have hz : C*M*M=0 := by
        have hgzero : C*g=0 := by rw [hg']; grind +ring
        rw [hcert,hL] at hgzero
        grind +ring
      grind
    obtain ⟨u,hpair⟩ := hsplit
    have hlin : L*u+M=0 := by rw [hL,hM]; grind +ring
    have hlink : A*u*u+B*u+D=0 := by
      have hi := hlin_identity u
      rw [hpair] at hi
      grind
    exact ⟨u,hpair,hlink⟩
  · let u : F := M/L
    have hLu : L*u=M := by
      dsimp [u]
      grind
    have hlin : L*u+M=0 := by rw [hLu]; exact charTwo M
    have hpair : C*u*u+p*u+H=0 := by
      have hfactor : C*g=L*L*(C*u*u+p*u+H) := by
        rw [hcert,← hLu]
        grind +ring
      have hz : L*L*(C*u*u+p*u+H)=0 := by
        rw [←hfactor,hg']
        grind +ring
      grind
    have hlink : A*u*u+B*u+D=0 := by
      have hi := hlin_identity u
      rw [hpair] at hi
      grind
    exact ⟨u,hpair,hlink⟩

#print axioms PairQuadratics.common_root_implies_eliminant_zero
#print axioms PairQuadratics.eliminant_zero_implies_common_root

end PairQuadratics

import Std.Tactic
import Init.Grind.Ring.Basic

/-! Faithful polynomial implications and exact native permutation data.
Actual plane-quartic geometry, theta-characteristic completeness and the
geometric Frobenius identification remain separate written/native bridges.
No custom axioms, holes or unverified native evaluation. -/
set_option autoImplicit false
set_option maxRecDepth 10000
set_option maxHeartbeats 2000000
namespace Bitangent223
open Lean.Grind

theorem denominator_factor {K : Type} [CommRing K] (a b d u : K) :
    let A := a+d*u+b*u^2
    let H := d+2*b*u
    4*b*A^2-A*H*(d+6*b*u)+u*H^3 =
      (4*a*b-d^2)*(a-b*u^2) := by
  dsimp
  grind

theorem constant_factor {K : Type} [CommRing K] (a b d e f u : K) :
    let A := a+d*u+b*u^2
    let H := d+2*b*u
    2*e*A^2-A*H*(f+e*u) =
      A*((2*e*a-d*f)+(d*e-2*b*f)*u) := by
  dsimp
  grind

theorem resultant_is_necessary {K : Type} [CommRing K]
    (A C D E L b c e v : K)
    (linear : C+L*v=0)
    (contact : 4*A^3*(c+e*v+b*v^2)-(D+E*v)^2=0) :
    4*A^3*(c*L^2-e*C*L+b*C^2)-(D*L-E*C)^2=0 := by
  have replaceC : C= -(L*v) := by grind
  rw [replaceC]
  have factor :
      4*A^3*(c*L^2-e*(-(L*v))*L+b*(-(L*v))^2)-
        (D*L-E*(-(L*v)))^2 =
      L^2*(4*A^3*(c+e*v+b*v^2)-(D+E*v)^2) := by grind
  rw [factor, contact]
  grind

def iterate {V : Type} (f : V → V) : Nat → V → V
  | 0, x => x
  | n+1, x => f (iterate f n x)

def actualPermutation (i : Fin 28) : Fin 28 :=
  match i.val with
  | 0 => ⟨4, by decide⟩
  | 1 => ⟨3, by decide⟩
  | 2 => ⟨5, by decide⟩
  | 3 => ⟨0, by decide⟩
  | 4 => ⟨2, by decide⟩
  | 5 => ⟨1, by decide⟩
  | 6 => ⟨8, by decide⟩
  | 7 => ⟨11, by decide⟩
  | 8 => ⟨7, by decide⟩
  | 9 => ⟨10, by decide⟩
  | 10 => ⟨6, by decide⟩
  | 11 => ⟨9, by decide⟩
  | 12 => ⟨16, by decide⟩
  | 13 => ⟨14, by decide⟩
  | 14 => ⟨12, by decide⟩
  | 15 => ⟨17, by decide⟩
  | 16 => ⟨15, by decide⟩
  | 17 => ⟨13, by decide⟩
  | 18 => ⟨19, by decide⟩
  | 19 => ⟨20, by decide⟩
  | 20 => ⟨18, by decide⟩
  | 21 => ⟨23, by decide⟩
  | 22 => ⟨26, by decide⟩
  | 23 => ⟨22, by decide⟩
  | 24 => ⟨25, by decide⟩
  | 25 => ⟨21, by decide⟩
  | 26 => ⟨24, by decide⟩
  | _ => ⟨27, by decide⟩

theorem actual_permutation_order_six :
    (∀ i : Fin 28, iterate actualPermutation 6 i = i) ∧
    ¬ (∀ i : Fin 28, iterate actualPermutation 2 i = i) ∧
    ¬ (∀ i : Fin 28, iterate actualPermutation 3 i = i) := by decide

end Bitangent223

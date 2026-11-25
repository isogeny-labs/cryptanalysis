import Mathlib.Tactic

namespace M31SetupCheck
variable {K : Type*} [Field K]

theorem pole (n d r : K) (hd : d ≠ 0) :
    n - r*d = 0 ↔ n/d = r := by
  rw [sub_eq_zero, div_eq_iff hd]

theorem step (n d r A B : K) (hd : d ≠ 0) (hu : n-r*d ≠ 0) :
    let u := n-r*d
    u*d ≠ 0 ∧ (u^2 + A*(u*d) + B*d^2)/(u*d) =
      (n/d-r) + A + B/(n/d-r) := by
  dsimp only
  refine ⟨mul_ne_zero hu hd, ?_⟩
  have hx : n/d-r = (n-r*d)/d := by field_simp
  rw [hx]
  field_simp

theorem terminal (n d c : K) (hd : d ≠ 0) :
    n-c*d = 0 ↔ n/d-c = 0 := by
  rw [sub_eq_zero (a:=n/d), pole n d c hd]

structure MapStep (K : Type*) where
  r : K
  A : K
  B : K

variable [DecidableEq K]

/-- A pole has no value. At the end report whether the terminal coordinate matches. -/
def affine (c x : K) : List (MapStep K) → Option Bool
  | [] => some (decide (x-c = 0))
  | m :: rest =>
    let u := x-m.r
    if u = 0 then none else affine c (u+m.A+m.B/u) rest

def projective (c n d : K) : List (MapStep K) → Option Bool
  | [] => some (decide (n-c*d = 0))
  | m :: rest =>
    let u := n-m.r*d
    if u = 0 then none else
      projective c (u^2 + m.A*(u*d) + m.B*d^2) (u*d) rest

theorem chain_correct (maps : List (MapStep K)) (c n d : K) (hd : d ≠ 0) :
    projective c n d maps = affine c (n/d) maps := by
  induction maps generalizing n d with
  | nil =>
    simp only [projective, affine, terminal n d c hd]
  | cons m rest ih =>
    have hp : n-m.r*d = 0 ↔ n/d-m.r = 0 := terminal n d m.r hd
    by_cases h : n-m.r*d = 0
    · simp [projective, affine, h, hp.mp h]
    · have ha := mt hp.mpr h
      obtain ⟨nonzero, ratio⟩ := step n d m.r m.A m.B hd h
      simp only [projective, affine, h, ha, if_false]
      rw [ih _ _ nonzero, ratio]

theorem from_input (maps : List (MapStep K)) (c x : K) :
    projective c x 1 maps = affine c x maps := by
  simpa using chain_correct maps c x 1 one_ne_zero

#print axioms from_input
end M31SetupCheck

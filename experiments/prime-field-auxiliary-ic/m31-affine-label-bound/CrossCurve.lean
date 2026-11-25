import Mathlib

set_option backward.isDefEq.respectTransparency false

namespace M31CrossCurve
abbrev p : ℕ := 2147483647

def u (t : ℤ) : ℕ → ℤ
  | 0 => 0
  | 1 => 1
  | d+2 => t*u t (d+1)-p*u t d

theorem u_step (t : ℤ) (d : ℕ) : u t (d+2) = t*u t (d+1)-p*u t d := rfl

def trace (t : ℤ) (d : ℕ) := 2*u t (d+1)-t*u t d

theorem initial (t : ℤ) : trace t 0 = 2 ∧ trace t 1 = t := by simp [trace,u]; ring

theorem recurrence (t : ℤ) (d : ℕ) :
    trace t (d+2) = t*trace t (d+1)-p*trace t d := by
  unfold trace
  rw [u_step t (d+1), u_step t d]
  ring

theorem norm (t : ℤ) (d : ℕ) :
    (u t (d+1))^2-t*u t d*u t (d+1)+p*(u t d)^2 = (p : ℤ)^d := by
  induction d with
  | zero => simp [u]
  | succ d ih =>
    rw [u_step t d, pow_succ (p : ℤ)]
    linear_combination (p : ℤ)*ih

theorem discriminant (t : ℤ) (d : ℕ) :
    (trace t d)^2-4*(p : ℤ)^d = (t^2-4*p)*(u t d)^2 := by
  unfold trace
  linear_combination 4*norm t d

private theorem nonzero (t : ℤ) (ht : (t : ZMod p) ≠ 0) (k : ℕ) : u t (k+1) ≠ 0 := by
  let : Fact (Nat.Prime p) := ⟨by native_decide⟩
  have residue (d : ℕ) : (u t (d+1) : ZMod p) = (t : ZMod p)^d := by
    induction d with
    | zero => simp [u]
    | succ d ih =>
      rw [u_step t d, Int.cast_sub, Int.cast_mul, Int.cast_mul, Int.cast_natCast,
        ZMod.natCast_self, zero_mul, sub_zero, ih, pow_succ, mul_comm]
  intro z
  have bad := residue k
  rw [z, Int.cast_zero] at bad
  exact pow_ne_zero k ht bad.symm

private theorem parity (a b : ℕ) : 0+2*a ≠ 1+2*b := by omega

private theorem differentClasses {x y : ℤ} (hx : x ≠ 0) (hy : y ≠ 0) :
    (-8121428563 : ℤ)*x^2 ≠ (-8081296779 : ℤ)*y^2 := by
  let : Fact (Nat.Prime 3) := ⟨by decide⟩
  intro eqn
  have h := congrArg Int.natAbs eqn
  simp only [Int.natAbs_mul, Int.natAbs_pow] at h
  change 8121428563 * x.natAbs^2 = 8081296779 * y.natAbs^2 at h
  have v := congrArg (padicValNat 3) h
  rw [padicValNat.mul (by decide : (8121428563 : ℕ) ≠ 0) (pow_ne_zero 2 (Int.natAbs_ne_zero.mpr hx)),
      padicValNat.mul (by decide : (8081296779 : ℕ) ≠ 0) (pow_ne_zero 2 (Int.natAbs_ne_zero.mpr hy)),
      padicValNat.pow, padicValNat.pow] at v
  have v1 : padicValNat 3 8121428563 = 0 := by native_decide
  have v2 : padicValNat 3 8081296779 = 1 := by native_decide
  rw [v1,v2] at v
  exact parity _ _ v

/-- Distinct even after squaring handles either choice of quadratic twist. -/
theorem distinctTraces (k : ℕ) :
    (trace (-21645) (k+1))^2 ≠ (trace (-22553) (k+1))^2 := by
  intro eqn
  have h := (discriminant (-21645) (k+1)).symm.trans
    ((congrArg (fun z : ℤ => z-4*(p : ℤ)^(k+1)) eqn).trans (discriminant (-22553) (k+1)))
  apply differentClasses (nonzero (-21645) (by decide) k) (nonzero (-22553) (by decide) k)
  have v1 : (-21645 : ℤ)^2-4*p = -8121428563 := by decide
  have v2 : (-22553 : ℤ)^2-4*p = -8081296779 := by decide
  simpa only [v1,v2] using h

end M31CrossCurve

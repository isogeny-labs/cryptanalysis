import Mathlib

/-!
The algebraic collision mechanism behind bounded-coefficient public relations.
The exact finite-grid component count is proved in the accompanying written
argument; the Lean bridge to that cardinality formula remains in progress.
-/

namespace XedniRelationCollisionCount

variable {C : Type*} [AddCommGroup C]

theorem relation_shift (U V : C) (a b u v : ℤ)
    (h : a • U + b • V = 0) :
    (u + a) • U + (v + b) • V = u • U + v • V := by
  rw [add_zsmul, add_zsmul]
  calc
    u • U + a • U + (v • V + b • V) =
        (u • U + v • V) + (a • U + b • V) := by abel
    _ = u • U + v • V := by rw [h, add_zero]

theorem relation_shift_multiple (U V : C) (a b u v t : ℤ)
    (h : a • U + b • V = 0) :
    (u + t * a) • U + (v + t * b) • V = u • U + v • V := by
  have ht : (t * a) • U + (t * b) • V = 0 := by
    rw [mul_zsmul, mul_zsmul, ← smul_add, h, smul_zero]
  rw [add_zsmul, add_zsmul]
  calc
    u • U + (t * a) • U + (v • V + (t * b) • V) =
        (u • U + v • V) + ((t * a) • U + (t * b) • V) := by abel
    _ = u • U + v • V := by rw [ht, add_zero]

theorem primitive_integer_collision (a b du dv : ℤ)
    (ha : a ≠ 0) (hab : Int.gcd a b = 1)
    (h : b * du = a * dv) :
    ∃ t : ℤ, du = a * t ∧ dv = b * t := by
  have hdiv : a ∣ du * b := by rw [mul_comm, h]; exact dvd_mul_right a dv
  have hadu : a ∣ du := Int.dvd_of_dvd_mul_left_of_gcd_one hdiv hab
  obtain ⟨t, ht⟩ := hadu
  refine ⟨t, ht, ?_⟩
  have hh : a * (b * t) = a * dv := by
    calc
      a * (b * t) = b * (a * t) := by ring
      _ = b * du := by rw [← ht]
      _ = a * dv := h
  exact (mul_left_cancel₀ ha hh).symm

theorem zmod_no_wrap (q : ℕ) (N z w : ℤ)
    (hN : 2 * N < q)
    (hzlo : -N ≤ z) (hzhi : z ≤ N)
    (hwlo : -N ≤ w) (hwhi : w ≤ N)
    (heq : (z : ZMod q) = (w : ZMod q)) : z = w := by
  have hd : (q : ℤ) ∣ w - z :=
    (ZMod.intCast_eq_intCast_iff_dvd_sub z w q).mp heq
  have hlt : -(q : ℤ) < w - z ∧ w - z < (q : ℤ) := by omega
  have habs : (w - z).natAbs < (q : ℤ).natAbs := by
    by_cases hp : 0 ≤ w - z
    · exact Int.natAbs_lt_natAbs_of_nonneg_of_lt hp hlt.2
    · have hn : 0 ≤ -(w - z) := by omega
      have hnlt : -(w - z) < (q : ℤ) := by omega
      simpa only [Int.natAbs_neg] using
        (Int.natAbs_lt_natAbs_of_nonneg_of_lt hn hnlt)
  have hzero : w - z = 0 := Int.eq_zero_of_dvd_of_natAbs_lt_natAbs hd habs
  omega

theorem zmod_collision_iff_relation_vector
    (q : ℕ) (N a b u v u' v' : ℤ)
    (ha : a ≠ 0) (hab : Int.gcd a b = 1)
    (hN : 2 * N < q)
    (hzlo : -N ≤ b * u - a * v) (hzhi : b * u - a * v ≤ N)
    (hwlo : -N ≤ b * u' - a * v') (hwhi : b * u' - a * v' ≤ N) :
    ((b * u - a * v : ℤ) : ZMod q) = ((b * u' - a * v' : ℤ) : ZMod q) ↔
      ∃ t : ℤ, u - u' = a * t ∧ v - v' = b * t := by
  constructor
  · intro heq
    have hval : b * u - a * v = b * u' - a * v' :=
      zmod_no_wrap q N _ _ hN hzlo hzhi hwlo hwhi heq
    have hmul : b * (u - u') = a * (v - v') := by nlinarith [hval]
    exact primitive_integer_collision a b (u - u') (v - v') ha hab hmul
  · rintro ⟨t, hdu, hdv⟩
    have hval : b * u - a * v = b * u' - a * v' := by
      linear_combination b * hdu - a * hdv
    exact congrArg (fun z : ℤ => (z : ZMod q)) hval

#print axioms relation_shift
#print axioms relation_shift_multiple
#print axioms primitive_integer_collision
#print axioms zmod_no_wrap
#print axioms zmod_collision_iff_relation_vector

end XedniRelationCollisionCount

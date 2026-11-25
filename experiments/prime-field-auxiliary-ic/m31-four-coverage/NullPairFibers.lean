import Mathlib.Tactic
import Mathlib.Data.ZMod.Basic

namespace M31.NullPairFibers

theorem small_minor_survives (z : ℤ) (hz : z ≠ 0) (lo : -128 ≤ z) (hi : z ≤ 128) :
    (z : ZMod 2147505293) ≠ 0 := by
  intro h
  obtain ⟨k, hk⟩ := (ZMod.intCast_zmod_eq_zero_iff_dvd z 2147505293).mp h
  norm_num at hk
  omega

theorem bounded_minor (a b c d : ℤ) (ha : |a| ≤ 8) (hb : |b| ≤ 8)
    (hc : |c| ≤ 8) (hd : |d| ≤ 8) : |a*d-b*c| ≤ 128 := by
  have product_bound (x y : ℤ) (hx : |x| ≤ 8) (hy : |y| ≤ 8) : |x*y| ≤ 64 := by
    rw [abs_mul]
    exact mul_le_mul hx hy (abs_nonneg _) (by decide)
  calc |a*d-b*c| = |a*d + -(b*c)| := by rw [sub_eq_add_neg]
       _ ≤ |a*d| + |-(b*c)| := abs_add_le ..
       _ ≤ 128 := by rw [abs_neg]; linarith [product_bound a d ha hd, product_bound b c hb hc]

variable {F : Type*} [Field F]

def affine (a b c d u v : F) (x : F × F) : F × F :=
  (a*x.1 + b*x.2 + u, c*x.1 + d*x.2 + v)

def affineEquiv (a b c d u v : F) (h : a*d - b*c ≠ 0) : (F × F) ≃ (F × F) where
  toFun := affine a b c d u v
  invFun t := ((d*(t.1-u) - b*(t.2-v))/(a*d-b*c), (a*(t.2-v)-c*(t.1-u))/(a*d-b*c))
  left_inv := by
    rintro ⟨x,y⟩
    have hi : (a*d-b*c) * (a*d-b*c)⁻¹ = 1 := mul_inv_cancel₀ h
    apply Prod.ext <;> dsimp [affine] <;> simp only [div_eq_mul_inv]
    · linear_combination x * hi
    · linear_combination y * hi
  right_inv := by
    rintro ⟨x,y⟩
    have hi : (a*d-b*c) * (a*d-b*c)⁻¹ = 1 := mul_inv_cancel₀ h
    apply Prod.ext <;> dsimp [affine] <;> simp only [div_eq_mul_inv]
    · linear_combination (x-u) * hi
    · linear_combination (y-v) * hi

variable {R : Type*}

def fiberEquiv (a b c d : F) (u v : R → F) (h : a*d-b*c ≠ 0) (t : F × F) :
    {p : R × (F × F) // affine a b c d (u p.1) (v p.1) p.2 = t} ≃ R where
  toFun p := p.val.1
  invFun r := ⟨(r, (affineEquiv a b c d (u r) (v r) h).symm t),
    (affineEquiv a b c d (u r) (v r) h).apply_symm_apply t⟩
  left_inv := by
    rintro ⟨⟨r,x⟩, hx⟩
    apply Subtype.ext
    apply Prod.ext
    · rfl
    · exact (affineEquiv a b c d (u r) (v r) h).symm_apply_eq.mpr hx.symm
  right_inv _ := rfl

theorem joint_count (a b c d : F) (u v : R → F) (h : a*d-b*c ≠ 0) (t : F × F) :
    Nat.card {p : R × (F × F) // affine a b c d (u p.1) (v p.1) p.2 = t} = Nat.card R :=
  Nat.card_congr (fiberEquiv a b c d u v h t)

theorem joint_fraction [Finite F] [Finite R] [Nonempty R]
    (a b c d : F) (u v : R → F) (h : a*d-b*c ≠ 0) (t : F × F) :
    (Nat.card {p : R × (F × F) // affine a b c d (u p.1) (v p.1) p.2 = t} : ℚ) /
      Nat.card (R × (F × F)) = 1 / (Nat.card F : ℚ)^2 := by
  rw [joint_count a b c d u v h t, Nat.card_prod, Nat.card_prod]
  push_cast
  have hr : (Nat.card R : ℚ) ≠ 0 := by exact_mod_cast Nat.card_pos.ne'
  have hf : (Nat.card F : ℚ) ≠ 0 := by exact_mod_cast Nat.card_pos.ne'
  field_simp

end M31.NullPairFibers

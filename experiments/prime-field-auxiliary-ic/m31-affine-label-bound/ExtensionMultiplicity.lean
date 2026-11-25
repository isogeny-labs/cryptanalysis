import Mathlib

set_option backward.isDefEq.respectTransparency false
namespace M31ExtensionMultiplicity

/-- Frobenius trace of the d-th power, with base trace p+1-n. -/
def tr (p n : ℤ) : ℕ → ℤ
  | 0 => 2
  | 1 => p+1-n
  | d+2 => (p+1-n)*tr p n (d+1)-p*tr p n d

def cofactor (p n : ℤ) : ℕ → ℤ
  | 0 => 0
  | 1 => 1
  | d+2 => (p+1-n)*cofactor p n (d+1)-p*cofactor p n d + p^(d+1)+1

theorem countFactor (p n : ℤ) (d : ℕ) : p^d+1-tr p n d = n*cofactor p n d := by
  induction d using Nat.twoStepInduction with
  | zero => simp [tr,cofactor]
  | one => simp [tr,cofactor]
  | more d h0 h1 =>
    rw [tr,cofactor,pow_succ p (d+1),pow_succ p d] at *
    linear_combination (p+1-n)*h1 - p*h0

def geom {R : Type*} [CommRing R] (a : R) : ℕ → R
  | 0 => 0
  | d+1 => geom a d + a^d

theorem geomSucc {R : Type*} [CommRing R] (a : R) (d : ℕ) :
    geom a (d+1) = geom a d + a^d := rfl

theorem telescope {R : Type*} [CommRing R] (a : R) (d : ℕ) :
    (a-1)*geom a d = a^d-1 := by
  induction d with
  | zero => simp [geom]
  | succ d ih => rw [geom,pow_succ]; linear_combination ih

theorem cofactorMod (p : ℤ) (n d : ℕ) :
    (cofactor p n d : ZMod n) = (d : ZMod n)*geom (p : ZMod n) d := by
  induction d using Nat.twoStepInduction with
  | zero => simp [cofactor,geom]
  | one => simp [cofactor,geom]
  | more d h0 h1 =>
    rw [cofactor]
    push_cast
    rw [ZMod.natCast_self, sub_zero, h0, h1, geomSucc _ (d+1), geomSucc _ d, pow_succ]
    push_cast
    linear_combination telescope (p : ZMod n) d

/-- For prime base group order n and p distinct from 1 modulo n, an
extension adds a second factor of n exactly at these two sets of degrees. -/
theorem squareFactor (p : ℤ) (n d : ℕ) [Fact n.Prime] (different : (p : ZMod n) ≠ 1) :
    (n : ℤ)^2 ∣ p^d+1-tr p n d ↔ n ∣ d ∨ orderOf (p : ZMod n) ∣ d := by
  have pos : (n : ℤ) ≠ 0 := by exact_mod_cast (Fact.out : Nat.Prime n).ne_zero
  have cancel : (n : ℤ)^2 ∣ (n : ℤ)*cofactor p n d ↔ (n : ℤ) ∣ cofactor p n d := by
    rw [pow_two, mul_dvd_mul_iff_left pos]
  have g : geom (p : ZMod n) d = 0 ↔ (p : ZMod n)^d = 1 := by
    have h := telescope (p : ZMod n) d
    constructor
    · intro z; rw [z, mul_zero] at h; exact sub_eq_zero.mp h.symm
    · intro z; rw [z, sub_self] at h
      exact (mul_eq_zero.mp h).resolve_left (sub_ne_zero.mpr different)
  rw [countFactor, cancel, ← ZMod.intCast_zmod_eq_zero_iff_dvd, cofactorMod, mul_eq_zero,
      ZMod.natCast_eq_zero_iff, g, orderOf_dvd_iff_pow_eq_one]

private theorem binaryPow {R : Type*} [Monoid R] (a : R) (d : ℕ) :
    npowBinRec d a = a^d := by
  induction d with
  | zero => simp [npowBinRec_zero]
  | succ d ih => rw [npowBinRec_succ, ih, pow_succ]

private theorem certifyOrder {n h : ℕ} (a : ZMod n) (hp : 0 < h)
    (full : npowBinRec h a = 1)
    (checks : ∀ q ∈ h.primeFactors, npowBinRec (h/q) a ≠ 1) : orderOf a = h := by
  apply orderOf_eq_of_pow_and_pow_div_prime hp (by simpa [binaryPow] using full)
  intro q prime divides
  simpa [binaryPow] using checks q (Nat.mem_primeFactors.mpr ⟨prime,divides,hp.ne'⟩)

theorem firstOrder : orderOf (2147483647 : ZMod 2147505293) = 1073752646 := by
  apply certifyOrder <;> native_decide

theorem secondOrder : orderOf (2147483647 : ZMod 2147506201) = 2147506200 := by
  apply certifyOrder <;> native_decide

theorem firstDegrees (d : ℕ) :
    (2147505293 : ℤ)^2 ∣ 2147483647^d+1-tr 2147483647 2147505293 d ↔
    2147505293 ∣ d ∨ 1073752646 ∣ d := by
  let : Fact (Nat.Prime 2147505293) := ⟨by native_decide⟩
  simpa only [Nat.cast_ofNat, Int.cast_ofNat, firstOrder] using
    squareFactor 2147483647 2147505293 d (by decide)

theorem secondDegrees (d : ℕ) :
    (2147506201 : ℤ)^2 ∣ 2147483647^d+1-tr 2147483647 2147506201 d ↔
    2147506201 ∣ d ∨ 2147506200 ∣ d := by
  let : Fact (Nat.Prime 2147506201) := ⟨by native_decide⟩
  simpa only [Nat.cast_ofNat, Int.cast_ofNat, secondOrder] using
    squareFactor 2147483647 2147506201 d (by decide)

end M31ExtensionMultiplicity

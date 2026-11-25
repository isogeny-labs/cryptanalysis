import Mathlib

namespace M31QuadraticCopy

/-- Over the quadratic extension the short models with constants b and -b
are related by (x,y) ↦ (-x,iy), where i² = -1. The identity also covers y=0. -/
theorem twistCoordinates {K : Type*} [Field K] (i a b x y : K) (hi : i^2 = -1) :
    (i*y)^2 = (-x)^3 + a*(-x) - b ↔ y^2 = x^3 + a*x + b := by
  rw [mul_pow, hi]
  constructor <;> intro h <;> linear_combination -h

/-- For either sign of t, the degree-two Frobenius count factors as the
two base-field counts. -/
theorem quadraticCount (p t : ℤ) :
    p^2 + 1 - (t^2-2*p) = (p+1-t)*(p+1+t) := by ring

/-- If the embedded subgroup has order n and index coprime to n, it
contains precisely the elements annihilated by a power of n. -/
theorem primaryCopy {G : Type*} [AddCommGroup G] (H : AddSubgroup G)
    {n c : ℕ} (hn : 0 < n) (size : Nat.card H = n)
    (ambient : Nat.card G = n*c) (cop : n.Coprime c) (x : G) :
    (∃ k : ℕ, n^k • x = 0) ↔ x ∈ H := by
  have idx : Nat.card (G ⧸ H) = c := by
    apply Nat.eq_of_mul_eq_mul_right hn
    rw [← size, ← H.card_eq_card_quotient_mul_card_addSubgroup, ambient, size, Nat.mul_comm]
  constructor
  · rintro ⟨k,hk⟩
    let q := QuotientAddGroup.mk' H x
    have annih : n^k • q = 0 := by
      change n^k • (QuotientAddGroup.mk' H) x = 0
      rw [← map_nsmul, hk, map_zero]
    have dc : addOrderOf q ∣ c := idx ▸ addOrderOf_dvd_natCard q
    have dn := addOrderOf_dvd_iff_nsmul_eq_zero.mpr annih
    have one : addOrderOf q = 1 := Nat.dvd_one.mp
      ((cop.pow_left k) ▸ Nat.dvd_gcd dn dc)
    exact (QuotientAddGroup.eq_zero_iff x).mp (AddMonoid.addOrderOf_eq_one_iff.mp one)
  · intro hx
    refine ⟨1, ?_⟩
    let y : H := ⟨x,hx⟩
    have ann := addOrderOf_dvd_iff_nsmul_eq_zero.mp (addOrderOf_dvd_natCard y)
    simpa [size, y] using congrArg H.subtype ann

/-- A sum of cofactor-torsion points can equal a target-primary point only
at zero. This applies to arbitrarily many points and includes signed sums
by choosing the signed points as inputs. -/
theorem cofactorSum {G I : Type*} [AddCommGroup G] (s : Finset I) (f : I → G)
    {n c k : ℕ} (cop : n.Coprime c) (hc : ∀ i ∈ s, c • f i = 0)
    (x : G) (hn : n^k • x = 0) (row : x = ∑ i ∈ s, f i) : x = 0 := by
  have annih : c • x = 0 := by
    rw [row, Finset.smul_sum]
    exact Finset.sum_eq_zero hc
  apply AddMonoid.addOrderOf_eq_one_iff.mp
  apply Nat.dvd_one.mp
  exact (cop.pow_left k) ▸ Nat.dvd_gcd (addOrderOf_dvd_iff_nsmul_eq_zero.mpr hn)
    (addOrderOf_dvd_iff_nsmul_eq_zero.mpr annih)

theorem fixtureOrders :
    2147505293 * 2147462003 = 4611686017958881879 ∧
    Nat.Coprime 2147505293 2147462003 ∧
    2147506201 * 2147461095 = 4611686017918750095 ∧
    Nat.Coprime 2147506201 2147461095 := by decide

end M31QuadraticCopy

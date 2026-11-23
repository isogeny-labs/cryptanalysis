import Mathlib

namespace MersenneTwist

variable {F : Type*} [Field F] [Fintype F] [DecidableEq F]

/-- Affine fibers plus the single rational point at infinity for a smooth cubic model. -/
noncomputable def modelCount (f : F → F) : ℕ :=
  1 + ∑ x : F, ({y : F | y^2 = f x} : Set F).toFinset.card

/-- A nonsquare twist interchanges square and nonsquare fibers. The formula
also handles a zero of f, which contributes one point to each affine model. -/
theorem countPair (f : F → F) (d : F) (hd : quadraticChar F d = -1)
    (hF : ringChar F ≠ 2) :
    modelCount f + modelCount (fun x => d*f x) = 2*(Fintype.card F+1) := by
  have fiber (u : F) :
      ({y : F | y^2 = u} : Set F).toFinset.card +
      ({y : F | y^2 = d*u} : Set F).toFinset.card = 2 := by
    have h := quadraticChar_card_sqrts hF u
    have ht := quadraticChar_card_sqrts hF (d*u)
    rw [map_mul, hd, neg_one_mul] at ht
    omega
  unfold modelCount
  generalize_proofs
  rw [show ∀ a b : ℕ, 1+a+(1+b) = 2+(a+b) by intros; omega]
  rw [← Finset.sum_add_distrib]
  simp_rw [fiber]
  simp
  omega

/-- Even when the target order is even, every common divisor of the two
rational group orders divides a power of two. -/
theorem commonDivisor {p k n t c : ℕ} (mersenne : p+1 = 2^k)
    (pair : n+t = 2*(p+1)) (hn : c ∣ n) (ht : c ∣ t) : c ∣ 2^(k+1) := by
  simpa [pair, mersenne, pow_succ, Nat.mul_comm] using Nat.dvd_add hn ht

/-- A homomorphism kills the odd-order part, even on a group of mixed order. -/
theorem killsOdd {G H : Type*} [AddGroup G] [AddGroup H] (φ : G →+ H)
    (p k : ℕ) (mersenne : p+1 = 2^k) (pair : Nat.card G + Nat.card H = 2*(p+1))
    (x : G) (odd : Odd (addOrderOf x)) : φ x = 0 := by
  let c := addOrderOf (φ x)
  have src : c ∣ addOrderOf x := addOrderOf_map_dvd φ x
  have pow : c ∣ 2^(k+1) := commonDivisor mersenne pair
    (dvd_trans src (addOrderOf_dvd_natCard x)) (addOrderOf_dvd_natCard (φ x))
  have cop := odd.coprime_two_right.pow_right (k+1)
  exact AddMonoid.addOrderOf_eq_one_iff.mp
    (Nat.dvd_one.mp (cop ▸ Nat.dvd_gcd src pow))

/-- Apply both arguments to the rational groups with their model counts. -/
theorem twistHomZero {G H : Type*} [AddGroup G] [AddGroup H] (φ : G →+ H)
    (f : F → F) (d : F) (hd : quadraticChar F d = -1) (hF : ringChar F ≠ 2)
    (k : ℕ) (mersenne : Fintype.card F + 1 = 2^k)
    (source : Nat.card G = modelCount f)
    (dest : Nat.card H = modelCount (fun x => d*f x))
    (odd : Odd (Nat.card G)) : φ = 0 := by
  ext x
  apply killsOdd φ (Fintype.card F) k mersenne
  · rw [source, dest, countPair f d hd hF]
  · exact odd.of_dvd_nat (addOrderOf_dvd_natCard x)

example : 2147505293 + 2147462003 = 2*(2147483647+1) ∧
    2147506201 + 2147461095 = 2*(2147483647+1) := by decide

end MersenneTwist

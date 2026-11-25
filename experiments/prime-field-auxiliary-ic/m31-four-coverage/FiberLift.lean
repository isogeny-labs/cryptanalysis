import Mathlib.FieldTheory.Finite.Basic
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.Tactic

namespace M31FiberLift

private instance : Fact (Nat.Prime 2147483647) := ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def squares {K : Type*} [Monoid K] {ι : Type*} (v : ι → K) : ℕ → ι → K
  | 0 => v
  | n+1 => fun i => (squares v n i)^2

theorem lane_power {K : Type*} [Monoid K] {ι : Type*} (v : ι → K) (n : ℕ) (i : ι) :
    squares v n i = (v i)^(2^n) := by
  induction n with
  | zero => simp [squares]
  | succ n ih =>
    change (squares v n i)^2 = _
    rw [ih, ← pow_mul, pow_succ]

/-- The post-squaring equality test accepts precisely the quadratic residues,
including zero, for any lane index and any width. -/
theorem lift_exact {ι : Type*} (v : ι → ZMod 2147483647) (i : ι) :
    (squares v 29 i)^2 = v i ↔ ∃ z, z^2 = v i := by
  constructor
  · exact fun h => ⟨_,h⟩
  · rintro ⟨z,hz⟩
    rw [lane_power, ← hz]
    calc
      ((z^2)^(2^29 : ℕ))^2 = z^((2*(2^29 : ℕ))*2) := by rw [pow_mul, pow_mul]
      _ = z^(2147483647+1 : ℕ) := by norm_num
      _ = z^2 := by rw [pow_succ, ZMod.pow_card, pow_two]

/-- A single candidate gives a root for the base or the negative twist.
Both square tests succeed simultaneously precisely for zero. -/
theorem twist_split (a : ZMod 2147483647) :
    let t := (a^(2^29 : ℕ))^2
    (t = a ∨ t = -a) ∧ ((t = a ∧ t = -a) ↔ a = 0) := by
  dsimp only
  have h : ((a^(2^29 : ℕ))^2)^2 = a^2 := by
    calc
      _ = a^((2^29 : ℕ)*2*2) := by rw [pow_mul, pow_mul]
      _ = a^(2147483647+1 : ℕ) := by norm_num
      _ = a^2 := by rw [pow_succ, ZMod.pow_card, pow_two]
  refine ⟨sq_eq_sq_iff_eq_or_eq_neg.mp h, ?_⟩
  constructor
  · rintro ⟨h₁,h₂⟩
    have hz : 2*a = 0 := by linear_combination h₂ - h₁
    exact (mul_eq_zero.mp hz).resolve_left (by decide)
  · rintro rfl
    norm_num

theorem twist_rhs {K : Type*} [CommRing K] (x a b : K) :
    (-x)^3 + a*(-x) - b = -(x^3 + a*x + b) := by ring

theorem minus_one_nonsquare : ¬ IsSquare (-1 : ZMod 2147483647) := by
  rw [FiniteField.isSquare_neg_one_iff, ZMod.card]
  decide

theorem twist_lift_exact (a : ZMod 2147483647) :
    (a^(2^29 : ℕ))^2 = -a ↔ ∃ z, z^2 = -a := by
  have h := lift_exact (fun _ : Unit => -a) ()
  rw [lane_power] at h
  have he : Even (2^29 : ℕ) := ⟨2^28, by norm_num⟩
  simpa only [he.neg_pow] using h

abbrev F31 := ZMod 2147483647

noncomputable def rootCount (a : F31) : ℤ :=
  (({y : F31 | y^2 = a}.toFinset.card : ℕ) : ℤ)

theorem complementary_counts (a : F31) : rootCount a + rootCount (-a) = 2 := by
  have hc : ringChar F31 ≠ 2 := by rw [ZMod.ringChar_zmod_n]; decide
  have hn := quadraticChar_neg_one_iff_not_isSquare.mpr minus_one_nonsquare
  unfold rootCount
  rw [quadraticChar_card_sqrts hc, quadraticChar_card_sqrts hc,
    ← neg_one_mul a, map_mul, hn]
  ring

/-- Each curve has one point at infinity. The twist term is reindexed by −x. -/
theorem complementary_totals (rhs : F31 → F31) :
    (1 + ∑ x, rootCount (rhs x)) + (1 + ∑ x, rootCount (-rhs (-x))) = 4294967296 := by
  have he := Equiv.sum_comp (Equiv.neg F31) (fun x => rootCount (-rhs x))
  change (∑ x, rootCount (-rhs (-x))) = ∑ x, rootCount (-rhs x) at he
  rw [he]
  have hs : (∑ x, rootCount (rhs x)) + (∑ x, rootCount (-rhs x)) = 4294967294 := by
    rw [← Finset.sum_add_distrib]
    simp [complementary_counts, ZMod.card, F31]
  linarith

/-- A homomorphism between finite groups of coprime sizes has trivial image. -/
theorem coprime_transfer {A B : Type*} [AddGroup A] [AddGroup B] [Fintype A] [Fintype B]
    (h : (Fintype.card A).Coprime (Fintype.card B)) (f : A →+ B) (x : A) : f x = 0 := by
  have ha : Fintype.card A • f x = 0 := by
    rw [← map_nsmul, card_nsmul_eq_zero, map_zero]
  have d := Nat.dvd_gcd (addOrderOf_dvd_iff_nsmul_eq_zero.mpr ha)
    (show addOrderOf (f x) ∣ Fintype.card B from addOrderOf_dvd_card)
  rw [h.gcd_eq_one] at d
  exact AddMonoid.addOrderOf_eq_one_iff.mp (Nat.eq_one_of_dvd_one d)

/-- A mixed additive decomposition in a common ambient group has zero
net twist contribution whenever the two source cardinalities are coprime. -/
theorem mixed_sum {A T V : Type*} [AddCommGroup A] [AddCommGroup T] [AddCommGroup V]
    [Fintype A] [Fintype T] (i : A →+ V) (j : T →+ V)
    (hc : (Fintype.card A).Coprime (Fintype.card T)) (target base : A) (twist : T)
    (balance : i target = i base + j twist) : j twist = 0 ∧ i target = i base := by
  have same : i (target-base) = j twist := by rw [map_sub, balance]; abel
  have ha : Fintype.card A • j twist = 0 := by rw [← same, ← map_nsmul, card_nsmul_eq_zero, map_zero]
  have ht : Fintype.card T • j twist = 0 := by rw [← map_nsmul, card_nsmul_eq_zero, map_zero]
  have d := Nat.dvd_gcd (addOrderOf_dvd_iff_nsmul_eq_zero.mpr ha)
    (addOrderOf_dvd_iff_nsmul_eq_zero.mpr ht)
  rw [hc.gcd_eq_one] at d
  have zero := AddMonoid.addOrderOf_eq_one_iff.mp (Nat.eq_one_of_dvd_one d)
  exact ⟨zero, by simpa [zero] using balance⟩

theorem archived_orders_coprime : Nat.Coprime 2147505293 2147462003 := by decide

end M31FiberLift

import Mathlib

namespace M31TraceScreen

abbrev r := 2147505293
abbrev R := ZMod r
instance : Fact (Nat.Prime r) := ⟨by native_decide⟩
abbrev p : R := 2147483647
abbrev g : R := 396466032
abbrev traceAt (k : ℕ) : R := g^k + p / g^k
abbrev inHasse (t : R) := t.val ≤ 92681 ∨ r - 92681 ≤ t.val

theorem hasseCut : (92681:ℕ)^2 ≤ 4*2147483647 ∧ 4*2147483647 < 92682^2 := by decide

theorem generatorOrder : orderOf g = 3244 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by native_decide)
  intro q hq hd
  change q ∣ 2 * 2 * 811 at hd
  have eqPrime {n : ℕ} (hn : Nat.Prime n) (h : q ∣ n) : q = n :=
    ((Nat.dvd_prime hn).mp h).resolve_left hq.ne_one
  rcases hq.dvd_mul.mp hd with hd | hd
  · rcases hq.dvd_mul.mp hd with h | h <;> obtain rfl := eqPrime (by decide) h <;> native_decide
  · obtain rfl := eqPrime (by native_decide) hd
    native_decide

theorem table : ∀ k : Fin 3244, inHasse (traceAt k.val) →
    traceAt k.val = -21645 ∨ traceAt k.val = 21645 := by native_decide

private theorem smallOrder {K : Type*} [Field K] {x : K} {d : ℕ}
    (hd : 0 < d) (hlt : d < 661993) (hx : x^d = 1) (hs : x^(r-1) = 1) :
    orderOf x ∣ 3244 := by
  have ho := orderOf_dvd_of_pow_eq_one hx
  have hp := Nat.pos_of_dvd_of_pos ho hd
  have hle := Nat.le_of_dvd hd ho
  have hc := (by native_decide : Nat.Prime 661993).coprime_iff_not_dvd.mpr
    (fun h => by have := Nat.le_of_dvd hp h; omega)
  have hsmall : orderOf x ∣ 3244 :=
    hc.symm.dvd_of_dvd_mul_right (show orderOf x ∣ 3244*661993 from orderOf_dvd_of_pow_eq_one hs)
  exact hsmall

/-- A modular eigenvalue fixed in degree d, whose order also divides r-1. -/
theorem splitScreen {K : Type*} [Field K] [Algebra R K] {x : K} {d : ℕ}
    (hd : 0 < d) (hlt : d < 661993) (hx : x^d = 1) (hs : x^(r-1) = 1)
    {t : R} (ht : inHasse t) (he : algebraMap R K t = x + algebraMap R K p / x) :
    t = -21645 ∨ t = 21645 := by
  have hsmall := smallOrder hd hlt hx hs
  have hgen : IsPrimitiveRoot g 3244 := generatorOrder ▸
    (show IsPrimitiveRoot g (orderOf g) from ⟨pow_orderOf_eq_one _, fun _ h => orderOf_dvd_of_pow_eq_one h⟩)
  obtain ⟨k,hk,hxk⟩ := (hgen.map_of_injective (algebraMap R K).injective).eq_pow_of_pow_eq_one
    (orderOf_dvd_iff_pow_eq_one.mp hsmall)
  have htrace : t = traceAt k := (algebraMap R K).injective (by simpa [traceAt, hxk] using he)
  subst t
  exact table ⟨k,hk⟩ ht

/-- Quadratic Frobenius data in a splitting field. Either root may be named x. -/
theorem traceScreen {K : Type*} [Field K] [Algebra R K] [CharP K r]
    {x y : K} {d : ℕ} {t : R} (hd : 0 < d) (hlt : d < 661993)
    (ht : inHasse t) (hs : x + y = algebraMap R K t)
    (hm : x*y = algebraMap R K p) (hx : x^d = 1) :
    t = -21645 ∨ t = 21645 := by
  have fixed (a : R) : (algebraMap R K a)^r = algebraMap R K a := by
    rw [← map_pow, ZMod.pow_card]
  have hsum : x^r + y^r = x+y := by
    rw [← add_pow_char, hs, fixed]
  have hprod : x^r * y^r = x*y := by rw [← mul_pow, hm, fixed]
  have roots : (x^r-x)*(x^r-y) = 0 := by
    linear_combination (x^r)*hsum - hprod
  have hn : x ≠ 0 := by
    intro h
    simp [h, zero_pow (Nat.ne_of_gt hd)] at hx
  rcases mul_eq_zero.mp roots with h | h
  · have hpow : x^(r-1) = 1 := by
      apply mul_right_cancel₀ hn
      simpa [← pow_succ] using sub_eq_zero.mp h
    apply splitScreen hd hlt hx hpow ht
    rw [← hs, ← hm, mul_div_cancel_left₀ _ hn]
  · have hy : y^d = 1 := by
      rw [← sub_eq_zero.mp h, ← pow_mul, Nat.mul_comm, pow_mul, hx, one_pow]
    have hpd : p^d = 1 := (algebraMap R K).injective (by
      rw [map_pow, ← hm, mul_pow, hx, hy, map_one, one_mul])
    have hdv := smallOrder hd hlt hpd (ZMod.pow_card_sub_one_eq_one (by native_decide : p ≠ 0))
    exact (by native_decide : p^3244 ≠ 1) (orderOf_dvd_iff_pow_eq_one.mp hdv) |>.elim

/-- Modular point-count form, with both Frobenius roots treated symmetrically. -/
theorem pointCountScreen {K : Type*} [Field K] [Algebra R K] [CharP K r]
    {x y : K} {d : ℕ} {t : R} (hd : 0 < d) (hlt : d < 661993)
    (ht : inHasse t) (hs : x + y = algebraMap R K t) (hm : x*y = algebraMap R K p)
    (count : (1-x^d)*(1-y^d) = 0) : t = -21645 ∨ t = 21645 := by
  rcases mul_eq_zero.mp count with h | h
  · exact traceScreen hd hlt ht hs hm (sub_eq_zero.mp h).symm
  · exact traceScreen hd hlt ht (add_comm x y ▸ hs) (mul_comm x y ▸ hm) (sub_eq_zero.mp h).symm

/-- The point-count expression is unchanged by choosing another ordering of
the roots of the same quadratic. -/
private theorem sameCount {K : Type*} [Field K] {x y a b : K} (d : ℕ)
    (hs : x+y = a+b) (hm : x*y = a*b) :
    (1-x^d)*(1-y^d) = (1-a^d)*(1-b^d) := by
  have h : (x-a)*(x-b) = 0 := by linear_combination x*hs - hm
  rcases mul_eq_zero.mp h with h | h
  · obtain rfl := sub_eq_zero.mp h
    obtain rfl := add_left_cancel hs
    rfl
  · obtain rfl := sub_eq_zero.mp h
    rw [add_comm a x] at hs
    obtain rfl := add_left_cancel hs
    ring

theorem exactScreen {K : Type*} [Field K] [Algebra R K] [CharP K r]
    {x y : K} {d : ℕ} {t : R} (hd : 0 < d) (hlt : d < 661993)
    (ht : inHasse t) (hs : x+y = algebraMap R K t) (hm : x*y = algebraMap R K p) :
    (1-x^d)*(1-y^d) = 0 ↔ t = -21645 ∨ (t = 21645 ∧ Even d) := by
  let f := algebraMap R K
  have posSum : (21645:R) = -1 + (-p) := by native_decide
  have negSum : (-21645:R) = 1+p := by native_decide
  have negPass (h : t = -21645) : (1-x^d)*(1-y^d) = 0 := by
    have s : x+y = (1:K)+f p := by simpa [f, h, negSum] using hs
    rw [sameCount d s (by simpa [f] using hm), one_pow, sub_self, zero_mul]
  have posTest (h : t = 21645) : (1-x^d)*(1-y^d) = 0 ↔ Even d := by
    have h1 : f (-1:R) = -1 := (map_neg f (1:R)).trans (congrArg Neg.neg f.map_one)
    have s : x+y = (-1:K)+f (-p) := hs.trans (by
      change f t = _
      rw [h,posSum,map_add,h1])
    have m : x*y = (-1:K)*f (-p) := calc
      x*y = f p := hm
      _ = f ((-1:R)*(-p)) := congrArg f (by native_decide)
      _ = f (-1:R)*f (-p) := f.map_mul _ _
      _ = _ := congrArg (fun z => z*f (-p)) h1
    rw [sameCount d s m]
    constructor
    · intro hz
      rcases mul_eq_zero.mp hz with hl | hr
      · have he : (-1:R)^d = 1 := f.injective (by simpa only [map_pow, h1, map_one] using (sub_eq_zero.mp hl).symm)
        have ho : orderOf (-1:R) = 2 := (CharP.orderOf_eq_two_iff r (by decide)).mpr rfl
        exact even_iff_two_dvd.mpr (ho ▸ orderOf_dvd_of_pow_eq_one he)
      · have he : (-p)^d = 1 := f.injective (by simpa only [map_one,map_pow] using (sub_eq_zero.mp hr).symm)
        have hv := smallOrder hd hlt he (ZMod.pow_card_sub_one_eq_one (by native_decide : -p ≠ 0))
        exact ((by native_decide : (-p)^3244 ≠ 1) (orderOf_dvd_iff_pow_eq_one.mp hv)).elim
    · rintro ⟨k,rfl⟩
      simp [← two_mul, pow_mul]
  constructor
  · intro h
    rcases pointCountScreen hd hlt ht hs hm h with hn | hp
    · exact Or.inl hn
    · exact Or.inr ⟨hp,(posTest hp).mp h⟩
  · rintro (hn | ⟨hp,he⟩)
    · exact negPass hn
    · exact (posTest hp).mpr he

/-- At the endpoint another Hasse trace has a root of exact order 661993. -/
theorem endpoint : inHasse (-74434) ∧
    (371347778:R) + p / 371347778 = -74434 ∧ orderOf (371347778:R) = 661993 := by
  refine ⟨by native_decide, by native_decide, ?_⟩
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by native_decide)
  intro q hq hd
  obtain rfl := ((Nat.dvd_prime (by native_decide : Nat.Prime 661993)).mp hd).resolve_left hq.ne_one
  native_decide

end M31TraceScreen

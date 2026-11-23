import M31FixtureObstruction
import Mathlib

namespace M31AffinePair
open Polynomial
abbrev F := M31FixtureObstruction.F
def f (x : F) := x^3 + 2*x + 14

/-- The monic form of f(aX+b), for nonzero a. -/
def pull (a b : F) : Cubic F :=
  ⟨1, 3*b/a, (3*b^2+2)/a^2, f b/a^3⟩

theorem pullEval (a b x : F) (ha : a ≠ 0) :
    a^3 * ((pull a b).toPoly.eval x) = f (a*x+b) := by
  simp [Cubic.toPoly, pull, f]
  field_simp
  ring

theorem irreduciblePull (a b : F) (ha : a ≠ 0) : Irreducible (pull a b).toPoly := by
  apply Polynomial.irreducible_of_degree_le_three_of_not_isRoot
  · rw [Cubic.natDegree_of_a_ne_zero (show (pull a b).a ≠ 0 from one_ne_zero)]
    decide
  · intro x hx
    exact M31FixtureObstruction.no_root (a*x+b) (by
      change f (a*x+b) = 0
      rw [← pullEval a b x ha, hx.eq_zero, mul_zero])

theorem distinctPull (a b : F) (ha : a ≠ 0) (h : (pull a b).toPoly = (pull 1 0).toPoly) :
    a = 1 ∧ b = 0 := by
  have h2 := Cubic.b_of_eq h
  have h1 := Cubic.c_of_eq h
  have h0 := Cubic.d_of_eq h
  change 3*b/a = 3*0/1 at h2
  have hb : b = 0 := by
    have hz : 3*b = 0 := (div_eq_zero_iff.mp (by simpa using h2 : 3*b/a=0)).resolve_right ha
    exact (mul_eq_zero.mp hz).resolve_left (by native_decide)
  subst b
  norm_num [pull, f] at h1 h0
  field_simp at h1 h0
  have hs : a^2 = 1 := by
    apply mul_left_cancel₀ (by native_decide : (2:F) ≠ 0)
    linear_combination -h1
  have ht : a^3 = 1 := by
    apply mul_left_cancel₀ (by native_decide : (14:F) ≠ 0)
    linear_combination -h0
  exact ⟨by rwa [pow_succ, hs, one_mul] at ht, rfl⟩

theorem genusTwoInput (a b : F) (ha : a ≠ 0) (nonid : ¬(a = 1 ∧ b = 0)) :
    let sextic := (pull a b).toPoly * (pull 1 0).toPoly
    sextic.Separable ∧ sextic.natDegree = 6 := by
  have h := irreduciblePull a b ha
  have h' := irreduciblePull 1 0 one_ne_zero
  have cop := (h.isCoprime_or_dvd (pull 1 0).toPoly).resolve_right (fun hd =>
    nonid (distinctPull a b ha (eq_of_monic_of_associated
      (Cubic.monic_of_a_eq_one rfl) (Cubic.monic_of_a_eq_one rfl) (h.associated_of_dvd h' hd))))
  refine ⟨(PerfectField.separable_of_irreducible h).mul
    (PerfectField.separable_of_irreducible h') cop, ?_⟩
  rw [natDegree_mul h.ne_zero h'.ne_zero,
    Cubic.natDegree_of_a_ne_zero (show (pull a b).a ≠ 0 from one_ne_zero),
    Cubic.natDegree_of_a_ne_zero (show (pull 1 0).a ≠ 0 from one_ne_zero)]

/-- The affine fibers and the fiber at infinity of the even-degree model.
In the infinity chart v=y/x³ the limiting equation is v²=a³. -/
abbrev Fibers (a b : F) :=
  (Σ x : F, {y : F // y^2 = f x * f (a*x+b)}) ⊕ {v : F // v^2 = a^3}

theorem pointCount (a b : F) :
    (Nat.card (Fibers a b) : ℤ) - (2147483647+1) =
    (∑ x : F, quadraticChar F (f x) * quadraticChar F (f (a*x+b))) +
      quadraticChar F (a^3) := by
  classical
  have counts (u : F) : (Fintype.card {y : F // y^2 = u} : ℤ) = quadraticChar F u + 1 := by
    have z := quadraticChar_card_sqrts ((ZMod.ringChar_zmod_n _).trans_ne (by decide : 2147483647 ≠ 2)) u
    rw [Set.toFinset_card] at z
    convert z using 2
    exact Fintype.card_congr (Equiv.refl _)
  rw [Nat.card_eq_fintype_card, Fintype.card_sum, Fintype.card_sigma, Nat.cast_add, Nat.cast_sum]
  simp_rw [counts, map_mul]
  rw [Finset.sum_add_distrib]
  simp [F, M31FixtureObstruction.F, ZMod.card]
  ring

/-- Hasse-Weil on the genus-two double cover, with the infinity correction
(the character of the leading coefficient). -/
theorem accuracy (s infinitySign hits : ℤ)
    (inf : infinitySign = 1 ∨ infinitySign = -1)
    (hw : (s+infinitySign)^2 ≤ 16*2147483647)
    (rule : 2*hits - 2147483647 = s ∨ 2*hits - 2147483647 = -s ∨
            2*hits - 2147483647 = 21645 ∨ 2*hits - 2147483647 = -21645) :
    10000000*hits < 5000432*2147483647 := by
  have ht : |s+infinitySign| ≤ 185363 := by
    by_contra! hn
    have hsq := mul_self_le_mul_self (by decide : (0:ℤ) ≤ 185364) (show 185364 ≤ |s+infinitySign| by omega)
    rw [← sq |s+infinitySign|, sq_abs] at hsq
    nlinarith
  obtain ⟨hlo,hhi⟩ := abs_le.mp ht
  rcases inf with h | h <;> rcases rule with h' | h' | h' | h' <;> omega

/-- Every deterministic Boolean function is accounted for by its two
outputs. Constants use the destination marginal; copy and complement use
the character correlation. -/
theorem scoreBound (nn nl ln ll inf : ℤ) (r0 r1 : Bool)
    (total : nn+nl+ln+ll = 2147483647) (balance : nl+ll-nn-ln = 21645)
    (hinf : inf = 1 ∨ inf = -1)
    (hw : ((nn+ll-nl-ln)+inf)^2 ≤ 16*2147483647) :
    10000000*((if r0 then nl else nn)+(if r1 then ll else ln)) < 5000432*2147483647 := by
  apply accuracy _ _ _ hinf hw
  cases r0 <;> cases r1 <;> simp only [Bool.false_eq_true, ite_false, ite_true] <;> omega

/-- The standard genus-two bound on the fiber count directly controls
copying or complementing the source sign, for the actual field sum. -/
theorem affineCorrelation (a b : F) (ha : a ≠ 0)
    (hw : ((Nat.card (Fibers a b) : ℤ) - (2147483647+1))^2 ≤ 16*2147483647) :
    |∑ x : F, quadraticChar F (f x) * quadraticChar F (f (a*x+b))| ≤ 185364 := by
  rw [pointCount] at hw
  set s := ∑ x : F, quadraticChar F (f x) * quadraticChar F (f (a*x+b))
  have ht : |s+quadraticChar F (a^3)| ≤ 185363 := by
    by_contra! hn
    have hsq := mul_self_le_mul_self (by decide : (0:ℤ) ≤ 185364)
      (show 185364 ≤ |s+quadraticChar F (a^3)| by omega)
    rw [← sq |s+quadraticChar F (a^3)|, sq_abs] at hsq
    nlinarith
  obtain ⟨lo,hi⟩ := abs_le.mp ht
  rcases quadraticChar_dichotomy (F := F) (pow_ne_zero 3 ha) with h | h <;>
    exact abs_le.mpr (by constructor <;> omega)

/-- Source and destination have the same marginal since the affine map is
a permutation. Thus each source label has both possible successors. -/
theorem cellFloor (nn nl ln ll : ℤ) (total : nn+nl+ln+ll = 2147483647)
    (balance : nl+ll-nn-ln = 21645) (same : nl = ln)
    (corr : |nn+ll-nl-ln| ≤ 185364) :
    536813749 ≤ nn ∧ 536813749 ≤ nl ∧ 536813749 ≤ ln ∧ 536813749 ≤ ll := by
  obtain ⟨lo,hi⟩ := abs_le.mp corr
  omega

end M31AffinePair

namespace M31AffinePair

theorem translatedCoprime (t u : F) (hne : t ≠ u) :
    IsCoprime (pull 1 t).toPoly (pull 1 u).toPoly := by
  have ht := irreduciblePull 1 t one_ne_zero
  have hu := irreduciblePull 1 u one_ne_zero
  apply (ht.isCoprime_or_dvd _).resolve_right
  intro hd
  have h := Cubic.b_of_eq (Polynomial.eq_of_monic_of_associated
    (Cubic.monic_of_a_eq_one (show (pull 1 t).a = 1 from rfl))
    (Cubic.monic_of_a_eq_one (show (pull 1 u).a = 1 from rfl)) (ht.associated_of_dvd hu hd))
  apply hne
  apply mul_left_cancel₀ (by native_decide : (3:F) ≠ 0)
  simpa [pull] using h

abbrev nonemptySubsets := (Finset.univ : Finset (Fin 11)).powerset.erase ∅

/-- Signs have already been multiplied by the chosen pattern. The only
analytic input is the lower bound on each nonempty signed character sum. -/
theorem patternFloor {X : Type*} [Fintype X] (size : Fintype.card X = 2147483647)
    (g : Fin 11 → X → ℤ) (sign : ∀ i x, g i x = 1 ∨ g i x = -1)
    (bound : ∀ s ∈ nonemptySubsets,
      -((3*s.card-1)*46341 : ℕ) ≤ (∑ x, ∏ i ∈ s, g i x : ℤ)) :
    330268 ≤ (Finset.univ.filter (fun x => ∀ i, g i x = 1)).card := by
  classical
  let W (s : Finset (Fin 11)) : ℤ := ∑ x, ∏ i ∈ s, g i x
  have hw : W ∅ = 2147483647 := by simp [W, size]
  have split := Finset.sum_erase_add ((Finset.univ : Finset (Fin 11)).powerset) W
    (Finset.empty_mem_powerset _)
  have budget : (∑ s ∈ nonemptySubsets, (-(((3*s.card-1)*46341 : ℕ) : ℤ))) = -1471095045 := by
    native_decide
  have low := Finset.sum_le_sum bound
  rw [budget] at low
  have term (x : X) : (∏ i, (1+g i x)) = if ∀ i, g i x = 1 then 2048 else 0 := by
    split_ifs with h
    · simp [h]
    · push Not at h
      obtain ⟨i, hi⟩ := h
      exact Finset.prod_eq_zero (Finset.mem_univ i) (by rw [(sign i x).resolve_left hi]; decide)
  have expansion : (∑ s ∈ (Finset.univ : Finset (Fin 11)).powerset, W s) =
      ((Finset.univ.filter fun x => ∀ i, g i x = 1).card : ℤ)*2048 := by
    unfold W
    rw [Finset.sum_comm]
    simp_rw [← Finset.prod_one_add, term]
    rw [← Finset.sum_filter]
    simp
  change -1471095045 ≤ ∑ s ∈ nonemptySubsets, W s at low
  change (∑ s ∈ nonemptySubsets, W s) + W ∅ = _ at split
  rw [hw, expansion] at split
  omega

end M31AffinePair

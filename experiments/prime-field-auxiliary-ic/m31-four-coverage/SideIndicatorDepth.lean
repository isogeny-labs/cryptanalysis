import FiberLift
import SquareRootDepth

open Polynomial
namespace M31SideIndicatorDepth

theorem degree_bound {p : ℕ} [Fact p.Prime] (s : Finset (ZMod p))
    (hs : 0 < s.card) (proper : s.card < p) (f : (ZMod p)[X])
    (exactLabel : ∀ x, f.eval x = if x ∈ s then 1 else 0) :
    p-1 ≤ f.natDegree := by
  classical
  by_contra! low
  have zeroSum : ∑ x : ZMod p, f.eval x = 0 := by
    simp_rw [Polynomial.eval_eq_sum_range]
    rw [Finset.sum_comm]
    apply Finset.sum_eq_zero
    intro i hi
    rw [← Finset.mul_sum]
    have hi' : i < Fintype.card (ZMod p) - 1 := by
      rw [ZMod.card]
      have := Finset.mem_range.mp hi
      omega
    rw [FiniteField.sum_pow_lt_card_sub_one _ i hi', mul_zero]
  simp_rw [exactLabel] at zeroSum
  have hcard : (s.card : ZMod p) = 0 := by simpa using zeroSum
  exact (Nat.not_dvd_of_pos_of_lt hs proper) ((ZMod.natCast_eq_zero_iff _ _).mp hcard)

abbrev F := ZMod 2147483647
private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def admits (x : F) := ∃ y : F, y^2 = x^3 + 2*x + 14

theorem both_labels : admits 1 ∧ ¬ admits 0 := by
  constructor
  · exact ⟨814455902, by decide +kernel⟩
  · rintro ⟨y,hy⟩
    have hr : (1653535937 : F)^2 = -14 := by decide +kernel
    apply M31FiberLift.minus_one_nonsquare
    refine ⟨y / 1653535937, ?_⟩
    rw [← pow_two, div_pow, hr]
    simp at hy
    rw [hy]
    decide +kernel

theorem curve_depth {d : Nat} {f : F[X]} (hc : M31SquareRootDepth.Circuit d f)
    (exactLabel : ∀ x, (admits x ∧ f.eval x = 1) ∨ (¬ admits x ∧ f.eval x = 0)) :
    31 ≤ d := by
  classical
  let s := Finset.univ.filter admits
  have inside : (1:F) ∈ s := Finset.mem_filter.mpr ⟨Finset.mem_univ _,both_labels.1⟩
  have outside : (0:F) ∉ s := fun h => both_labels.2 (Finset.mem_filter.mp h).2
  have strict : s ⊂ Finset.univ := Finset.ssubset_iff_of_subset (Finset.subset_univ s) |>.mpr
    ⟨0,Finset.mem_univ _,outside⟩
  have proper := Finset.card_lt_card strict
  rw [Finset.card_univ,ZMod.card] at proper
  have lo := degree_bound s (Finset.card_pos.mpr ⟨_,inside⟩) proper f (by
    intro x
    rcases exactLabel x with ⟨yes,h⟩ | ⟨no,h⟩ <;> simp_all [s])
  have hi := M31SquareRootDepth.circuit_degree hc
  by_contra! small
  have := Nat.pow_le_pow_right (by decide : 0 < 2) (show d ≤ 30 by omega)
  omega

open M31SquareRootDepth in
private theorem powers {b : F[X]} (hb : Circuit 0 b) (d k : Nat) (hk : k ≤ 2^d) :
    Circuit d (b^k) := by
  induction d generalizing k with
  | zero =>
    have : k ≤ 1 := hk
    interval_cases k
    · simpa using Circuit.constant (1:F)
    · simpa using hb
  | succ d ih =>
    let m := min k (2^d)
    have hm : m ≤ k := min_le_left _ _
    have hrem : k-m ≤ 2^d := by dsimp [m]; rw [pow_succ] at hk; omega
    have h := Circuit.mul (ih m (min_le_right _ _)) (ih (k-m) hrem)
    rw [← pow_add, Nat.add_sub_of_le hm] at h
    simpa using h

open M31SquareRootDepth in
private theorem sumCircuit (k d : Nat) (hk : k ≤ 2^d) (s : Finset F) :
    Circuit d (∑ a ∈ s, (1 - (X - C a)^k)) := by
  have one : Circuit 0 (1 : F[X]) := by simpa using Circuit.constant (1:F)
  have single (a : F) : Circuit d (1 - (X - C a)^k) := by
    have base : Circuit 0 (X - C a) := Circuit.sub Circuit.input (Circuit.constant a)
    simpa only [Nat.zero_max] using Circuit.sub one (powers base d k hk)
  induction s using Finset.induction_on with
  | empty => simpa using Circuit.scale (0:F) (single 0)
  | insert a t ha ih =>
    rw [Finset.sum_insert ha]
    simpa only [max_self] using Circuit.add (single a) ih

open M31SquareRootDepth in
theorem indicator_upper (s : Finset F) : ∃ f, Circuit 31 f ∧
    ∀ x, f.eval x = if x ∈ s then 1 else 0 := by
  let delta := fun a : F => 1 - (X - C a)^(2147483646 : Nat)
  refine ⟨_, sumCircuit 2147483646 31 (by decide) s, ?_⟩
  change ∀ x, (∑ a ∈ s, delta a).eval x = _
  intro x
  have label (a : F) : (delta a).eval x = if a = x then 1 else 0 := by
    by_cases h : a = x
    · simp [delta,h]
    · have powOne := ZMod.pow_card_sub_one_eq_one (p := 2147483647) (sub_ne_zero.mpr (Ne.symm h))
      simpa [delta,h] using congrArg (fun y : F => 1-y) powOne
  simp [Polynomial.eval_finsetSum, label]

end M31SideIndicatorDepth

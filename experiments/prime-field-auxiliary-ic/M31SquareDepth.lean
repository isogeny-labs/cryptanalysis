import Mathlib.Algebra.Polynomial.Expand
import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.NumberTheory.LucasLehmer

namespace M31SquareDepth
open Polynomial

abbrev K := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

inductive Circuit where
  | input
  | const (c : K)
  | add (a b : Circuit)
  | sub (a b : Circuit)
  | mul (a b : Circuit)
  | sq (a : Circuit)

noncomputable def poly : Circuit → K[X]
  | .input => X
  | .const c => C c
  | .add a b => poly a + poly b
  | .sub a b => poly a - poly b
  | .mul a b => poly a * poly b
  | .sq a => poly a * poly a

def depth : Circuit → Nat
  | .input | .const _ => 0
  | .add a b | .sub a b => max (depth a) (depth b)
  | .mul a b => max (depth a) (depth b) + 1
  | .sq a => depth a + 1

theorem degree_bound (a : Circuit) : (poly a).natDegree ≤ 2 ^ depth a := by
  induction a with
  | input => simp [poly, depth]
  | const c => simp [poly, depth]
  | add a b ha hb | sub a b ha hb | mul a b ha hb =>
    have l := ha.trans (Nat.pow_le_pow_right (by decide : 0 < 2) (le_max_left (depth a) (depth b)))
    have r := hb.trans (Nat.pow_le_pow_right (by decide : 0 < 2) (le_max_right (depth a) (depth b)))
    first
    | exact (natDegree_add_le ..).trans (max_le l r)
    | exact (natDegree_sub_le ..).trans (max_le l r)
    | exact (natDegree_mul_le ..).trans (by change _ ≤ 2^(max (depth a) (depth b)+1); rw [pow_succ]; omega)
  | sq a ha =>
    apply (natDegree_mul_le ..).trans
    change _ ≤ 2^(depth a+1)
    rw [pow_succ]
    omega

def recognizes (a b : Circuit) := ∀ x : K, x ≠ 0 →
  ((poly a).eval x = (poly b).eval x ↔ IsSquare x)

theorem lower (a b : Circuit) (h : recognizes a b) : 30 ≤ max (depth a) (depth b) := by
  classical
  let f := poly a - poly b
  have hn : ¬ IsSquare (-1 : K) := by
    rw [FiniteField.isSquare_neg_one_iff, ZMod.card]
    decide
  have hf : f ≠ 0 := by
    intro e
    apply hn
    apply (h (-1) (by simp)).mp
    rw [sub_eq_zero.mp e]
  let s : Finset K := Finset.univ.erase 0
  have roots : s.val ⊆ (expand K 2 f).roots := by
    intro x hx
    have nz : x ≠ 0 := (Finset.mem_erase.mp (show x ∈ s from hx)).1
    have he := (h (x^2) (pow_ne_zero _ nz)).mpr (by exact ⟨x, pow_two x⟩)
    apply (mem_roots ((expand_ne_zero (by decide : 0 < 2)).mpr hf)).2
    simpa [Polynomial.IsRoot, expand_eq_comp_X_pow, eval_comp, f] using sub_eq_zero.mpr he
  have card : s.card = 2147483646 := by simp [s, ZMod.card]
  have bound := card_le_degree_of_subset_roots roots
  rw [card, expand_eq_comp_X_pow, natDegree_comp] at bound
  simp only [natDegree_X_pow] at bound
  have deg := (natDegree_sub_le (poly a) (poly b)).trans
    (max_le ( (degree_bound a).trans (Nat.pow_le_pow_right (by decide) (le_max_left _ (depth b))))
            ( (degree_bound b).trans (Nat.pow_le_pow_right (by decide) (le_max_right (depth a) _))))
  change f.natDegree ≤ _ at deg
  by_contra! small
  have lim := Nat.pow_le_pow_right (by decide : 0 < 2) (show max (depth a) (depth b) ≤ 29 by omega)
  omega

def chain : Nat → Circuit
  | 0 => .input
  | n+1 => .sq (chain n)

theorem chain_depth (n : Nat) : depth (chain n) = n := by
  induction n <;> simp_all [chain, depth]

theorem chain_eval (n : Nat) (x : K) : (poly (chain n)).eval x = x^(2^n) := by
  induction n <;> simp_all [chain, poly, pow_succ, pow_mul]

theorem upper : max (depth (chain 30)) (depth .input) = 30 ∧ recognizes (chain 30) .input := by
  constructor
  · simp [chain_depth, depth]
  intro x hx
  have hchar : ringChar K ≠ 2 := by rw [ZMod.ringChar_zmod_n]; decide
  rw [chain_eval, FiniteField.isSquare_iff hchar hx, ZMod.card]
  simp only [poly, eval_X]
  rw [show (2:Nat)^30 = 1073741823+1 by decide, show (2147483647:Nat)/2 = 1073741823 by decide]
  rw [pow_succ]
  conv_lhs => rhs; rw [← one_mul x]
  exact mul_left_inj' hx

end M31SquareDepth

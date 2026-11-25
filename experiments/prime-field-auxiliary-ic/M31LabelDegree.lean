import Mathlib.Algebra.Polynomial.Expand
import Mathlib.Algebra.Polynomial.BigOperators
import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.NumberTheory.LucasLehmer

namespace M31LabelDegree
open Polynomial
abbrev K := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

theorem capacity (P : K[X]) (A : Finset K)
    (correct : ∀ x : K, x ≠ 0 → (P.eval x ∈ A ↔ IsSquare x)) :
    1073741823 ≤ A.card * P.natDegree := by
  classical
  let F : K[X] := ∏ a ∈ A, (P - C a)
  have zeros (x : K) : F.eval x = 0 ↔ P.eval x ∈ A := by
    simp [F, eval_prod, Finset.prod_eq_zero_iff, sub_eq_zero]
  have hn : ¬ IsSquare (-1 : K) := by
    rw [FiniteField.isSquare_neg_one_iff, ZMod.card]
    decide
  have hf : F ≠ 0 := by
    intro e
    exact hn ((correct _ (by simp)).mp ((zeros _).mp (by rw [e]; simp)))
  let S : Finset K := Finset.univ.erase 0
  have roots : S.val ⊆ (expand K 2 F).roots := by
    intro x hx
    have nz := (Finset.mem_erase.mp (show x ∈ S from hx)).1
    have hz := (zeros (x^2)).mpr ((correct _ (pow_ne_zero _ nz)).mpr ⟨x, pow_two x⟩)
    apply (mem_roots ((expand_ne_zero (by decide : 0 < 2)).mpr hf)).2
    simpa [IsRoot, expand_eq_comp_X_pow, eval_comp] using hz
  have bound := card_le_degree_of_subset_roots roots
  have card : S.card = 2147483646 := by simp [S, ZMod.card]
  rw [card, expand_eq_comp_X_pow, natDegree_comp, natDegree_X_pow] at bound
  have d : F.natDegree ≤ A.card * P.natDegree := calc
    _ ≤ ∑ a ∈ A, (P-C a).natDegree := natDegree_prod_le _ _
    _ ≤ ∑ _a ∈ A, P.natDegree := Finset.sum_le_sum fun a _ =>
      (natDegree_sub_le P (C a)).trans (by simp)
    _ = _ := by simp
  omega

theorem minimum_degree (P : K[X]) (A : Finset K) (size : A.card ≤ 32767)
    (correct : ∀ x : K, x ≠ 0 → (P.eval x ∈ A ↔ IsSquare x)) :
    32769 ≤ P.natDegree := by
  have h := (capacity P A correct).trans (Nat.mul_le_mul_right P.natDegree size)
  omega
end M31LabelDegree

import Mathlib.Algebra.Polynomial.Roots
import Mathlib.FieldTheory.Finite.Basic
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.Tactic

namespace M31SquareRootDepth
open Polynomial
abbrev F := ZMod 2147483647
private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

/-- A polynomial selecting either ordinate on every nonzero square. -/
def SelectsRoot (f : F[X]) := ∀ z : F, z ≠ 0 → (f.eval (z^2))^2 = z^2

theorem degree_bound (f : F[X]) (h : SelectsRoot f) : 2^29 ≤ f.natDegree := by
  classical
  let g := f.comp (X^2)
  let q := g^2 - X^2
  have dg : g.natDegree = f.natDegree * 2 := by simp [g, natDegree_comp]
  have nz : q ≠ 0 := by
    intro eq
    have he : g^2 = X^2 := sub_eq_zero.mp eq
    rcases sq_eq_sq_iff_eq_or_eq_neg.mp he with pos | neg
    · rw [pos, natDegree_X] at dg; omega
    · rw [neg, natDegree_neg, natDegree_X] at dg; omega
  have roots : (Finset.univ.erase (0 : F)).val ⊆ q.roots := by
    intro x hx
    have hx' := (Finset.mem_erase.mp (show x ∈ Finset.univ.erase (0 : F) from hx)).1
    apply (mem_roots nz).mpr
    simpa [IsRoot, q, g, eval_comp] using sub_eq_zero.mpr (h x hx')
  have card := card_le_degree_of_subset_roots roots
  have domain : (Finset.univ.erase (0 : F)).card = 2147483646 := by
    simp [Finset.card_erase_of_mem, ZMod.card, F]
  rw [domain] at card
  have upper := natDegree_sub_le (g^2) ((X : F[X])^2)
  change 2147483646 ≤ (g^2 - X^2).natDegree at card
  simp [natDegree_pow, dg] at upper
  norm_num
  omega

/-- A shared arithmetic circuit can be unfolded to this expression without
changing the maximum multiplication depth along an input-to-output path. -/
inductive Circuit : Nat → F[X] → Prop
  | input : Circuit 0 X
  | constant (a : F) : Circuit 0 (C a)
  | add : Circuit d f → Circuit e g → Circuit (max d e) (f+g)
  | sub : Circuit d f → Circuit e g → Circuit (max d e) (f-g)
  | scale (a : F) : Circuit d f → Circuit d (C a*f)
  | mul : Circuit d f → Circuit e g → Circuit (max d e + 1) (f*g)

theorem circuit_degree (hc : Circuit d f) : f.natDegree ≤ 2^d := by
  induction hc with
  | input => simp
  | constant => simp
  | add a b ha hb =>
    apply (natDegree_add_le _ _).trans
    exact max_le (ha.trans (Nat.pow_le_pow_right (by decide) (le_max_left _ _)))
      (hb.trans (Nat.pow_le_pow_right (by decide) (le_max_right _ _)))
  | sub a b ha hb =>
    apply (natDegree_sub_le _ _).trans
    exact max_le (ha.trans (Nat.pow_le_pow_right (by decide) (le_max_left _ _)))
      (hb.trans (Nat.pow_le_pow_right (by decide) (le_max_right _ _)))
  | scale a h ih => exact (natDegree_mul_le.trans (by simpa using ih))
  | @mul d f e g a b ha hb =>
    have u := ha.trans (Nat.pow_le_pow_right (by decide : 0 < 2) (le_max_left d e))
    have v := hb.trans (Nat.pow_le_pow_right (by decide : 0 < 2) (le_max_right d e))
    rw [pow_succ]; exact natDegree_mul_le.trans (by omega)

theorem depth_bound (hc : Circuit d f) (h : SelectsRoot f) : 29 ≤ d := by
  exact (Nat.pow_le_pow_iff_right (by decide : 1 < 2)).mp ((degree_bound f h).trans (circuit_degree hc))

theorem attained : ∃ f, Circuit 29 f ∧ SelectsRoot f := by
  have chain (n : Nat) : Circuit n ((X : F[X])^(2^n : Nat)) := by
    induction n with
    | zero => simpa using Circuit.input
    | succ n ih => simpa [pow_succ, pow_add, Nat.mul_two] using Circuit.mul ih ih
  refine ⟨_, chain 29, ?_⟩
  intro z _
  simp only [eval_pow, eval_X]
  rw [← pow_mul, ← pow_mul]
  change z^(2147483647+1 : Nat) = z^2
  rw [pow_succ, ZMod.pow_card, pow_two]

end M31SquareRootDepth

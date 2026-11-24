import FixedWeights

namespace M31FixedOrbitExact

open M31FixedWeights M31FiberRecurrence M31PanelInitializer

private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def seedOK (a b : M) := a^2 + b^2 + fixed^2 - a*b*fixed - 4 = 0

private def weights : Nat → M × M
  | 0 => (0,1)
  | n+1 => let pair := weights n; (pair.2, fixed*pair.2-pair.1)

private theorem weight_values (n : Nat) :
    weights n = (generated fixed 0 1 n, generated fixed 0 1 (n+1)) := by
  induction n with
  | zero => rfl
  | succ n ih => rw [weights, ih]; rfl

private def den (u q : M) := u^2 + q^2 - fixed*u*q
private def num (u : M) := u^2*(4-fixed^2)
private def exceptional (x : M) := x = 2 ∨ x = -2
private instance (x : M) : Decidable (exceptional x) := by unfold exceptional; infer_instance

-- Gap n+1 relates the two coordinates of a seed through u*b = q*a.
set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
private theorem gap_table : ∀ n : Fin 127,
    let v := (weights n.val).1
    let u := (weights n.val).2
    den u (1+v) ≠ 0 ∧ exceptional (forward^[6] (num u / den u (1+v) - 2)) := by
  decide +kernel

private theorem repeat_exceptional (a b : M) (valid : seedOK a b) (n : Fin 127)
    (repeatSlot : generated fixed a b (n.val+1) = a) : exceptional (forward^[7] a) := by
  let u := (weights n.val).2
  let q := 1 + (weights n.val).1
  have linear : u*b-q*a = 0 := by
    dsimp [u,q]
    rw [weight_values]
    rw [weighted] at repeatSlot
    linear_combination repeatSlot
  obtain ⟨nonzero, cert⟩ := gap_table n
  have relation : den u q * a^2 = num u := by
    unfold den num
    unfold seedOK at valid
    linear_combination u^2*valid - (u*b+q*a-fixed*u*a)*linear
  have sqr : a^2 = num u / den u q :=
    (eq_div_iff nonzero).mpr (by rw [mul_comm]; exact relation)
  change exceptional (forward^[6] (forward a))
  rw [show forward a = num u / den u q - 2 by unfold forward; rw [← sq, sqr]]
  exact cert

private theorem shifted (a b : M) (i n : Nat) :
    generated fixed (generated fixed a b i) (generated fixed a b (i+1)) n =
    generated fixed a b (i+n) := by
  induction n using Nat.twoStepInduction with
  | zero => rfl
  | one => rfl
  | more n h j =>
    rw [generated, h, j]
    rfl

private theorem edge_valid (a b : M) (h : seedOK a b) (i : Nat) :
    seedOK (generated fixed a b i) (generated fixed a b (i+1)) := by
  induction i with
  | zero => exact h
  | succ i ih =>
    change seedOK _ (fixed*generated fixed a b (i+1)-generated fixed a b i)
    unfold seedOK at *
    linear_combination ih

theorem injective_slots (a b : M) (h : seedOK a b)
    (good : forward^[7] a ≠ 2 ∧ forward^[7] a ≠ -2) :
    Function.Injective (fun i : Fin 128 => generated fixed a b i.val) := by
  intro i j eq
  wlog hij : i.val ≤ j.val generalizing i j
  · exact (this eq.symm (by omega)).symm
  by_contra ne
  have gap : i.val < j.val := by by_contra z; exact ne (Fin.ext (by omega))
  let n : Fin 127 := ⟨j.val-i.val-1, by omega⟩
  have idx : i.val+(n.val+1) = j.val := by dsimp [n]; omega
  have ex := repeat_exceptional _ _ (edge_valid a b h i.val) n (by rw [shifted, idx]; exact eq.symm)
  rw [fixed_terminal _ _ h] at ex
  exact ex.elim good.1 good.2

private theorem degree (n : Nat) : (doublingPoly M n).natDegree = 2^n := by
  induction n with
  | zero => simp [doublingPoly]
  | succ n ih => rw [doublingPoly, Polynomial.natDegree_sub_C, Polynomial.natDegree_pow, ih,
      pow_succ, Nat.mul_comm]

private theorem eval_iter (x : M) (n : Nat) : (doublingPoly M n).eval x = forward^[n] x := by
  induction n with
  | zero => simp [doublingPoly]
  | succ n ih =>
    rw [doublingPoly, Polynomial.eval_sub, Polynomial.eval_pow, Polynomial.eval_C, ih,
      Function.iterate_succ_apply', forward, sq]

theorem exhausts (a b : M) (valid : seedOK a b) (good : forward^[7] a ≠ 2 ∧ forward^[7] a ≠ -2)
    (x : M) : forward^[7] x = forward^[7] a ↔
      ∃ i : Fin 128, generated fixed a b i.val = x := by
  classical
  let poly := doublingPoly M 7 - Polynomial.C (forward^[7] a)
  have deg : poly.natDegree = 128 := by simp [poly, Polynomial.natDegree_sub_C, degree]
  have nz : poly ≠ 0 := by intro e; simp [e] at deg
  have mem (y : M) : y ∈ poly.roots.toFinset ↔ forward^[7] y = forward^[7] a := by
    rw [Multiset.mem_toFinset, Polynomial.mem_roots nz]
    change (doublingPoly M 7 - Polynomial.C (forward^[7] a)).eval y = 0 ↔ _
    rw [Polynomial.eval_sub, Polynomial.eval_C, eval_iter, sub_eq_zero]
  let f := fun i : Fin 128 => generated fixed a b i.val
  let vals := Finset.univ.image f
  have size : vals.card = 128 := by
    simp [vals,f,Finset.card_image_of_injective _ (injective_slots a b valid good)]
  have sub : vals ⊆ poly.roots.toFinset := by
    intro y hy
    obtain ⟨i, _, rfl⟩ := Finset.mem_image.mp hy
    exact (mem _).mpr (fixed_terminal a b valid i.val)
  have bound := (Multiset.toFinset_card_le _).trans (Polynomial.card_roots' poly)
  have allRoots := Finset.eq_of_subset_of_card_le sub (by omega)
  rw [← mem, ← allRoots]
  simp [vals,f]

end M31FixedOrbitExact

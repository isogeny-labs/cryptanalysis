import FiberRecurrence
import TorusOrder
import Mathlib.RingTheory.RootsOfUnity.PrimitiveRoots
import Mathlib.Algebra.Polynomial.Roots

namespace M31FiberRecurrence

private theorem trace_collision {K : Type*} [Field K] {a b : K} (ha : a ≠ 0) (hb : b ≠ 0)
    (h : tr a = tr b) : a = b ∨ a*b = 1 := by
  unfold tr at h
  field_simp at h
  have h' : (a-b)*(a*b-1) = 0 := by linear_combination h
  simpa only [mul_eq_zero, sub_eq_zero] using h'

/-- Trace after n applications of the doubling polynomial. -/
noncomputable def doublingPoly (K : Type*) [Field K] : Nat → Polynomial K
  | 0 => Polynomial.X
  | n+1 => doublingPoly K n ^ 2 - Polynomial.C 2

private theorem doubling_degree (K : Type*) [Field K] (n : Nat) :
    (doublingPoly K n).natDegree = 2^n := by
  induction n with
  | zero => simp [doublingPoly]
  | succ n ih => rw [doublingPoly, Polynomial.natDegree_sub_C, Polynomial.natDegree_pow, ih,
      pow_succ, Nat.mul_comm]

private theorem doubling_eval {K : Type*} [Field K] {a : K} (ha : a ≠ 0) (n : Nat) :
    (doublingPoly K n).eval (tr a) = tr (a^(2^n)) := by
  induction n with
  | zero => simp [doublingPoly]
  | succ n ih =>
    simp only [doublingPoly, Polynomial.eval_sub, Polynomial.eval_pow, Polynomial.eval_C, ih,
      pow_succ 2 n, pow_mul]
    have hn := pow_ne_zero (2^n) ha
    unfold tr
    field_simp
    ring

def orbitTrace {K : Type*} [Field K] (z : K) (i : Fin 128) := tr (z^(1 + 16777216*i.val))

theorem orbitTrace_injective {K : Type*} [Field K] {z : K} (hz : z ≠ 0)
    (ho : orderOf z = 2147483648) : Function.Injective (orbitTrace z) := by
  have prim := IsPrimitiveRoot.iff_orderOf.mpr ho
  intro i j eq
  rcases trace_collision (pow_ne_zero _ hz) (pow_ne_zero _ hz) eq with same | opposite
  · have h := prim.pow_inj (by omega) (by omega) same
    apply Fin.ext
    omega
  · rw [← pow_add] at opposite
    have h := prim.dvd_of_pow_eq_one _ opposite
    omega

/-- Exactly the 128 field roots, even if the ambient field is infinite. -/
theorem orbitTrace_exhausts {K : Type*} [Field K] {z : K} (hz : z ≠ 0)
    (ho : orderOf z = 2147483648) (x : K) :
    (doublingPoly K 7).eval x = tr (z^128) ↔ ∃ i : Fin 128, orbitTrace z i = x := by
  classical
  let p := doublingPoly K 7 - Polynomial.C (tr (z^128))
  have deg : p.natDegree = 128 := by simp [p, Polynomial.natDegree_sub_C, doubling_degree]
  have nz : p ≠ 0 := by intro h; simp [h] at deg
  have mem (v : K) : v ∈ p.roots.toFinset ↔ (doublingPoly K 7).eval v = tr (z^128) := by
    simp [Polynomial.mem_roots nz, Polynomial.IsRoot, p, sub_eq_zero]
  let s := Finset.univ.image (orbitTrace z)
  have sz : s.card = 128 := by simp [s, Finset.card_image_of_injective _ (orbitTrace_injective hz ho)]
  have root : z ^ 2147483648 = 1 := ho ▸ pow_orderOf_eq_one z
  have sub : s ⊆ p.roots.toFinset := by
    intro v hv
    obtain ⟨i, _, rfl⟩ := Finset.mem_image.mp hv
    apply (mem _).2
    unfold orbitTrace
    rw [doubling_eval (pow_ne_zero _ hz), ← pow_mul]
    have e : (1 + 16777216*i.val)*2^7 = 128 + 2147483648*i.val := by omega
    rw [e, pow_add, pow_mul, root, one_pow, mul_one]
  have card := (Multiset.toFinset_card_le _).trans (Polynomial.card_roots' p)
  have allRoots := Finset.eq_of_subset_of_card_le sub (by omega)
  rw [← mem, ← allRoots]
  simp [s]

/-- Either square root used by the initializer selects a valid neighboring trace. -/
theorem neighbor_of_discriminant {K : Type*} [Field K] [NeZero (2 : K)]
    {z w d y : K} (hz : z ≠ 0) (hw : w ≠ 0)
    (hd : d^2 = ((tr z)^2 - 4)*((tr w)^2 - 4))
    (hy : 2*y = tr z * tr w + d) :
    y = tr (z*w) ∨ y = tr (z/w) := by
  have sum : tr (z*w) + tr (z/w) = tr z * tr w := by
    unfold tr
    field_simp
    ring
  have disc : (tr (z*w) - tr (z/w))^2 = ((tr z)^2-4)*((tr w)^2-4) := by
    unfold tr
    field_simp
    ring
  have diff : d^2 = (tr (z*w) - tr (z/w))^2 := hd.trans disc.symm
  rcases sq_eq_sq_iff_eq_or_eq_neg.mp diff with pos | neg
  · left
    apply mul_left_cancel₀ (NeZero.ne (2 : K))
    rw [hy, ← sum, pos]
    ring
  · right
    apply mul_left_cancel₀ (NeZero.ne (2 : K))
    rw [hy, ← sum, neg]
    ring

def generated {K : Type*} [Field K] (step first second : K) : Nat → K
  | 0 => first
  | 1 => second
  | n+2 => step * generated step first second (n+1) - generated step first second n

theorem generated_trace {K : Type*} [Field K] {z w : K} (hz : z ≠ 0) (hw : w ≠ 0)
    (n : Nat) : generated (tr w) (tr z) (tr (z*w)) n = tr (z*w^n) := by
  induction n using Nat.twoStepInduction with
  | zero => simp [generated]
  | one => simp [generated]
  | more n ih jh =>
    rw [generated, jh, ih]
    convert next_trace (mul_ne_zero hz (pow_ne_zero n hw)) hw using 1 <;>
      simp [pow_succ, mul_assoc]

/-- Reversing a primitive-step walk permutes its slots by negation modulo 128. -/
private theorem reverse_slots {K : Type*} [Field K] {w : K} (period : w^128 = 1)
    (i : Fin 128) : ∃ j : Fin 128, (w⁻¹)^j.val = w^i.val := by
  by_cases h : i.val = 0
  · exact ⟨0, by simp [h]⟩
  · refine ⟨⟨128-i.val, by omega⟩, ?_⟩
    rw [inv_pow]
    apply inv_eq_of_mul_eq_one_right
    rw [← pow_add, show 128-i.val+i.val = 128 by omega, period]

theorem every_root_generated {K : Type*} [Field K] [NeZero (2 : K)] {z d y : K}
    (hz : z ≠ 0) (ho : orderOf z = 2147483648)
    (hd : d^2 = ((tr z)^2 - 4)*((tr (z^16777216))^2 - 4))
    (hy : 2*y = tr z * tr (z^16777216) + d)
    (x : K) (hx : (doublingPoly K 7).eval x = tr (z^128)) :
    ∃ j : Fin 128, generated (tr (z^16777216)) (tr z) y j.val = x := by
  obtain ⟨i, rfl⟩ := (orbitTrace_exhausts hz ho x).mp hx
  let w := z^16777216
  have hw : w ≠ 0 := pow_ne_zero _ hz
  have period : w^128 = 1 := by
    change (z^16777216)^128 = 1
    rw [← pow_mul]
    change z^2147483648 = 1
    rw [← ho, pow_orderOf_eq_one]
  have repr : orbitTrace z i = tr (z*w^i.val) := by
    unfold orbitTrace w
    rw [pow_add, pow_one, pow_mul]
  rw [repr]
  rcases neighbor_of_discriminant hz hw hd hy with pos | neg
  · exact ⟨i, pos ▸ generated_trace hz hw _⟩
  · obtain ⟨j, hj⟩ := reverse_slots period i
    refine ⟨j, ?_⟩
    change generated (tr w) (tr z) y j.val = _
    rw [neg, div_eq_mul_inv]
    have ht : tr w = tr w⁻¹ := by simp [tr, add_comm]
    rw [ht, generated_trace hz (inv_ne_zero hw), hj]

theorem generated_exact {K : Type*} [Field K] [NeZero (2 : K)] {z d y : K}
    (hz : z ≠ 0) (ho : orderOf z = 2147483648)
    (hd : d^2 = ((tr z)^2 - 4)*((tr (z^16777216))^2 - 4))
    (hy : 2*y = tr z * tr (z^16777216) + d) :
    let f := fun j : Fin 128 => generated (tr (z^16777216)) (tr z) y j.val
    Function.Injective f ∧
      ∀ x, (doublingPoly K 7).eval x = tr (z^128) ↔ ∃ j, f j = x := by
  classical
  intro f
  let src := Finset.univ.image (orbitTrace z)
  let dst := Finset.univ.image f
  have sub : src ⊆ dst := by
    intro x hx
    obtain ⟨i, _, rfl⟩ := Finset.mem_image.mp hx
    obtain ⟨j, hj⟩ := every_root_generated hz ho hd hy _ ((orbitTrace_exhausts hz ho _).2 ⟨i, rfl⟩)
    exact Finset.mem_image.mpr ⟨j, Finset.mem_univ _, hj⟩
  have size : src.card = 128 := by
    simp [src, Finset.card_image_of_injective _ (orbitTrace_injective hz ho)]
  have bound : dst.card ≤ 128 := (Finset.card_image_le).trans_eq (by simp)
  have eqs := Finset.eq_of_subset_of_card_le sub (by omega)
  constructor
  · have full : (Finset.univ.image f).card = (Finset.univ : Finset (Fin 128)).card := by
      change dst.card = _
      rw [← eqs, size]
      simp
    simpa using Finset.injOn_of_card_image_eq full
  · intro x
    rw [orbitTrace_exhausts hz ho]
    have h := Finset.ext_iff.mp eqs x
    simpa [src, dst] using h

/-- In the archived fiber the terminal supplies the order hypothesis. -/
theorem archived_generated_exact {K : Type*} [Field K] [NeZero (2 : K)]
    (ι : ZMod 2147483647 →+* K) {z d y : K} (hz : z ≠ 0)
    (fiber : M31TorusOrder.step^[7] (tr z) = ι 340921998)
    (hd : d^2 = ((tr z)^2 - 4)*((tr (z^16777216))^2 - 4))
    (hy : 2*y = tr z * tr (z^16777216) + d) :
    let f := fun j : Fin 128 => generated (tr (z^16777216)) (tr z) y j.val
    Function.Injective f ∧
      ∀ x, (doublingPoly K 7).eval x = ι 340921998 ↔ ∃ j, f j = x := by
  have terminal : tr (z^128) = ι 340921998 := (M31TorusOrder.trace_iter hz 7).symm.trans fiber
  rw [← terminal]
  exact generated_exact hz (M31TorusOrder.archived_fiber_order ι hz fiber) hd hy

end M31FiberRecurrence

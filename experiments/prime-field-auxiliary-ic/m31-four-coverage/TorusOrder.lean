import Mathlib.GroupTheory.OrderOfElement
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.Tactic

namespace M31TorusOrder

def traceValue {K : Type*} [Field K] (z : K) := z + z⁻¹
def step {K : Type*} [Field K] (x : K) := x^2-2

theorem trace_square {K : Type*} [Field K] {z : K} (hz : z ≠ 0) :
    step (traceValue z) = traceValue (z^2) := by
  unfold step traceValue
  field_simp
  ring

theorem trace_iter {K : Type*} [Field K] {z : K} (hz : z ≠ 0) (n : ℕ) :
    step^[n] (traceValue z) = traceValue (z^(2^n)) := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Function.iterate_succ_apply', ih, trace_square (pow_ne_zero _ hz), ← pow_mul, pow_succ]

theorem order_from_trace {K : Type*} [Field K] [NeZero (2 : K)] {z : K} (hz : z ≠ 0)
    (n : ℕ) (h : step^[n] (traceValue z) = -2) : orderOf z = 2^(n+1) := by
  rw [trace_iter hz] at h
  let w := z^(2^n)
  have hw : w ≠ 0 := pow_ne_zero _ hz
  change w + w⁻¹ = -2 at h
  field_simp at h
  have hsq : (w+1)^2 = 0 := by linear_combination h
  have hm : w = -1 := eq_neg_of_add_eq_zero_left (sq_eq_zero_iff.mp hsq)
  apply orderOf_eq_prime_pow
  · change w ≠ 1
    rw [hm]
    intro bad
    exact (NeZero.ne (2:K)) (by linear_combination -bad)
  · rw [pow_succ 2 n, pow_mul]
    change w^2 = 1
    rw [hm]
    norm_num

private instance : Fact (Nat.Prime 2147483647) := ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

private theorem terminal : step^[23] (340921998 : ZMod 2147483647) = -2 := by decide +kernel

theorem archived_fiber_order {K : Type*} [Field K] [NeZero (2 : K)]
    (ι : ZMod 2147483647 →+* K) {z : K} (hz : z ≠ 0)
    (fiber : step^[7] (traceValue z) = ι 340921998) : orderOf z = 2^31 := by
  have two : ι 2 = 2 := by change ι (2 : ℕ) = (2 : ℕ); exact map_natCast ι 2
  have commute : Function.Semiconj ι step step := fun x => by simp [step,two]
  apply order_from_trace hz 30
  change step^[23+7] (traceValue z) = -2
  rw [Function.iterate_add_apply, fiber, ← (commute.iterate_right 23).eq, terminal]
  simp [two]

end M31TorusOrder

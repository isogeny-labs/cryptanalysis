/- Structural bridge for linear tests on a sampled characteristic-two hyperplane.
   The concrete field, receipt rows, and rank certificate remain outside Lean. -/

namespace ResidualSpan

def xorSum : List Nat → Nat
  | [] => 0
  | x :: xs => Nat.xor x (xorSum xs)

theorem linear_test_zero_on_xor_sum
    (test : Nat → Bool)
    (zero : test 0 = false)
    (linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (samples : List Nat)
    (sample_zero : ∀ x, x ∈ samples → test x = false) :
    test (xorSum samples) = false := by
  induction samples with
  | nil => simpa [xorSum] using zero
  | cons x xs ih =>
      have hx : test x = false := sample_zero x (by simp)
      have hxs : ∀ y, y ∈ xs → test y = false := by
        intro y hy
        exact sample_zero y (by simp [hy])
      change test (Nat.xor x (xorSum xs)) = false
      rw [linear x (xorSum xs), hx, ih hxs]
      decide

theorem no_additional_linear_test
    (trace test : Nat → Bool)
    (samples : List Nat)
    (test_zero : test 0 = false)
    (test_linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (test_zero_on_samples : ∀ x, x ∈ samples → test x = false)
    (span_trace_kernel : ∀ v, trace v = false →
      ∃ selected : List Nat,
        (∀ x, x ∈ selected → x ∈ samples) ∧ xorSum selected = v) :
    ∀ v, trace v = false → test v = false := by
  intro v hv
  obtain ⟨selected, members, sum_eq⟩ := span_trace_kernel v hv
  rw [← sum_eq]
  apply linear_test_zero_on_xor_sum test test_zero test_linear selected
  intro x hx
  exact test_zero_on_samples x (members x hx)

#print axioms ResidualSpan.linear_test_zero_on_xor_sum
#print axioms ResidualSpan.no_additional_linear_test

end ResidualSpan

/- A full binary feature span makes every linear predicate that vanishes
on the sample vanish on the whole feature space. The 862-row certificate
and the concrete coordinate encoding are audited outside Lean. -/
namespace FullFeatureRank

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

theorem full_span_forces_zero_test
    (width : Nat) (test : Nat → Bool) (samples : List Nat)
    (test_zero : test 0 = false)
    (test_linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (test_zero_on_samples : ∀ x, x ∈ samples → test x = false)
    (span_within : ∀ v, v < 2 ^ width → ∃ selected : List Nat,
      (∀ x, x ∈ selected → x ∈ samples) ∧ xorSum selected = v) :
    ∀ v, v < 2 ^ width → test v = false := by
  intro v hv
  obtain ⟨selected, members, sum_eq⟩ := span_within v hv
  rw [← sum_eq]
  apply linear_test_zero_on_xor_sum test test_zero test_linear selected
  intro x hx
  exact test_zero_on_samples x (members x hx)

#print axioms FullFeatureRank.linear_test_zero_on_xor_sum
#print axioms FullFeatureRank.full_span_forces_zero_test

end FullFeatureRank

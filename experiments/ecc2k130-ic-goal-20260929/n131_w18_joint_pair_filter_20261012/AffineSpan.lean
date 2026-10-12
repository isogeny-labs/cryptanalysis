/- A structural bridge from a finite affine-rank certificate to parity gates.
   The concrete N41 curve, witness file, and elimination are checked separately. -/
namespace AffineSpan

def xorSum : List Nat → Nat
  | [] => 0
  | x :: xs => Nat.xor x (xorSum xs)

def fromAnchor (anchor : Nat) (selected : List Nat) : Nat :=
  Nat.xor anchor (xorSum (selected.map (Nat.xor anchor)))

theorem xorSum_zero_of_zero_on_members
    (test : Nat → Bool)
    (zero : test 0 = false)
    (linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (xs : List Nat)
    (all_zero : ∀ x, x ∈ xs → test x = false) :
    test (xorSum xs) = false := by
  induction xs with
  | nil => simpa [xorSum] using zero
  | cons x rest ih =>
      have hx : test x = false := all_zero x (by simp)
      have hr : ∀ y, y ∈ rest → test y = false := by
        intro y hy
        exact all_zero y (by simp [hy])
      change test (Nat.xor x (xorSum rest)) = false
      rw [linear x (xorSum rest), hx, ih hr]
      decide

theorem affine_test_constant_on_affine_span
    (test : Nat → Bool)
    (zero : test 0 = false)
    (linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (anchor : Nat) (selected : List Nat)
    (same : ∀ x, x ∈ selected → test x = test anchor) :
    test (fromAnchor anchor selected) = test anchor := by
  unfold fromAnchor
  rw [linear]
  have hz : test (xorSum (selected.map (Nat.xor anchor))) = false := by
    apply xorSum_zero_of_zero_on_members test zero linear
    intro y hy
    obtain ⟨x, hx, rfl⟩ := List.mem_map.mp hy
    rw [linear, same x hx]
    cases test anchor <;> rfl
  rw [hz]
  cases test anchor <;> rfl

theorem no_additional_affine_parity
    (trace test : Nat → Bool) (anchor : Nat) (samples : List Nat)
    (test_zero : test 0 = false)
    (test_linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (constant_on_samples : ∀ x, x ∈ samples → test x = test anchor)
    (affine_span_trace_kernel : ∀ v, trace v = false →
      ∃ selected : List Nat,
        (∀ x, x ∈ selected → x ∈ samples) ∧ fromAnchor anchor selected = v) :
    ∀ v, trace v = false → test v = test anchor := by
  intro v hv
  obtain ⟨selected, members, hspan⟩ := affine_span_trace_kernel v hv
  rw [← hspan]
  apply affine_test_constant_on_affine_span test test_zero test_linear anchor selected
  intro x hx
  exact constant_on_samples x (members x hx)

#print axioms AffineSpan.affine_test_constant_on_affine_span
#print axioms AffineSpan.no_additional_affine_parity
end AffineSpan

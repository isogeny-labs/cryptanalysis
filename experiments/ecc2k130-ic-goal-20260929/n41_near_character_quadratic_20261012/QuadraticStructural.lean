import Std

namespace QuadraticStructural

def xorSum : List Nat → Nat
  | [] => 0
  | value :: rest => Nat.xor value (xorSum rest)

theorem linear_zero_on_xorSum (test : Nat → Bool)
    (zero : test 0 = false)
    (linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (values : List Nat)
    (vanishes : ∀ value ∈ values, test value = false) :
    test (xorSum values) = false := by
  induction values with
  | nil => simpa [xorSum] using zero
  | cons value rest ih =>
      have hv : test value = false := vanishes value (by simp)
      have hrest : ∀ item ∈ rest, test item = false := by
        intro item hm
        exact vanishes item (by simp [hm])
      change test (Nat.xor value (xorSum rest)) = false
      rw [linear value (xorSum rest), hv, ih hrest]
      rfl

theorem sampled_basis_forces_linear_zero
    (samples : List Nat) (witnesses : Fin 821 → List Nat)
    (cert : ∀ bit : Fin 821, xorSum (witnesses bit) = 2 ^ bit.val)
    (members : ∀ bit : Fin 821, ∀ value ∈ witnesses bit, value ∈ samples)
    (test : Nat → Bool)
    (zero : test 0 = false)
    (linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (sample_zero : ∀ value ∈ samples, test value = false) :
    ∀ bit : Fin 821, test (2 ^ bit.val) = false := by
  intro bit
  rw [← cert bit]
  apply linear_zero_on_xorSum test zero linear (witnesses bit)
  intro value hv
  exact sample_zero value (members bit value hv)

#print axioms QuadraticStructural.sampled_basis_forces_linear_zero

end QuadraticStructural

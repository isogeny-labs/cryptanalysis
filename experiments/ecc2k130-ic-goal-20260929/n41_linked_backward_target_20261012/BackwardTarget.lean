import Std

/-! The target-backward terminal chain is equivalent to the forward sum
    under the group laws. The concrete curve/chart bridge is recorded
    separately in PROOF_MAP.md. -/

theorem backward_target_equiv {Point : Type}
    (add : Point → Point → Point) (neg : Point → Point) (zero : Point)
    (assoc : ∀ a b c, add (add a b) c = add a (add b c))
    (right_zero : ∀ a, add a zero = a)
    (left_neg : ∀ a, add (neg a) a = zero)
    (right_neg : ∀ a, add a (neg a) = zero)
    (target prefix8 final8 final9 : Point) :
    add (add target (neg final9)) (neg final8) = prefix8 ↔
      target = add (add prefix8 final8) final9 := by
  have cancel_left (a b : Point) : add (add a (neg b)) b = a := by
    rw [assoc, left_neg, right_zero]
  have cancel_right (a b : Point) : add (add a b) (neg b) = a := by
    rw [assoc, right_neg, right_zero]
  constructor
  · intro h
    have h8 := congrArg (fun z => add z final8) h
    rw [cancel_left] at h8
    have h9 := congrArg (fun z => add z final9) h8
    rw [cancel_left] at h9
    exact h9
  · intro h
    rw [h]
    rw [cancel_right, cancel_right]

#print axioms backward_target_equiv

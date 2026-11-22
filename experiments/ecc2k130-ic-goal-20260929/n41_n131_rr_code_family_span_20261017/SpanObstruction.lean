import Std

namespace SpanObstruction

/-- A Boolean-linear trace that kills every coefficient also kills every
XOR combination of those coefficients. -/
theorem fold_annihilated {V : Type} (add : V → V → V) (L : V → Bool)
    (linear : ∀ a b, L (add a b) = Bool.xor (L a) (L b))
    (xs : List V) (acc : V) (hacc : L acc = false)
    (hxs : ∀ x ∈ xs, L x = false) :
    L (xs.foldl add acc) = false := by
  induction xs generalizing acc with
  | nil => exact hacc
  | cons x rest ih =>
      simp only [List.foldl_cons]
      apply ih (add acc x)
      · rw [linear, hacc, hxs x (by simp)]
        rfl
      · intro y hy
        exact hxs y (by simp [hy])

/-- A constant coefficient in the XOR span of the sign-dependent
coefficients cannot be separated from them by one Boolean-linear trace. -/
theorem constant_in_span_not_separable {V : Type}
    (add : V → V → V) (zero constant : V)
    (coefficients representation : List V)
    (representation_subset : ∀ x ∈ representation, x ∈ coefficients)
    (representation_eq : representation.foldl add zero = constant)
    (L : V → Bool)
    (linear : ∀ a b, L (add a b) = Bool.xor (L a) (L b))
    (zero_trace : L zero = false)
    (kills_coefficients : ∀ x ∈ coefficients, L x = false) :
    L constant = false := by
  rw [← representation_eq]
  exact fold_annihilated add L linear representation zero zero_trace
    (fun x hx => kills_coefficients x (representation_subset x hx))

#print axioms fold_annihilated
#print axioms constant_in_span_not_separable

end SpanObstruction

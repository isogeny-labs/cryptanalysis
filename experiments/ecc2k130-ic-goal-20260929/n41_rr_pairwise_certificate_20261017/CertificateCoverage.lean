import Std

namespace CertificateCoverage

/-- An additive Boolean trace kills an XOR fold when it kills every term. -/
private theorem fold_zero {V : Type} (add : V → V → V) (L : V → Bool)
    (linear : ∀ a b, L (add a b) = Bool.xor (L a) (L b))
    (xs : List V) (acc : V) (hacc : L acc = false)
    (hxs : ∀ x ∈ xs, L x = false) :
    L (xs.foldl add acc) = false := by
  induction xs generalizing acc with
  | nil => exact hacc
  | cons x tail ih =>
      simp only [List.foldl_cons]
      apply ih (add acc x)
      · rw [linear, hacc, hxs x (by simp)]
        rfl
      · intro y hy
        exact hxs y (by simp [hy])

/-- If a constant coefficient belongs to the XOR span of the
nonconstant coefficients of two charts, one linear trace cannot
annihilate both charts while selecting that constant. -/
theorem pair_span_obstructs_shared_trace {V : Type}
    (add : V → V → V) (zero constant : V)
    (left right representation : List V)
    (representation_subset : ∀ x ∈ representation, x ∈ left ∨ x ∈ right)
    (representation_eq : representation.foldl add zero = constant)
    (L : V → Bool)
    (linear : ∀ a b, L (add a b) = Bool.xor (L a) (L b))
    (zero_trace : L zero = false)
    (kills_left : ∀ x ∈ left, L x = false)
    (kills_right : ∀ x ∈ right, L x = false) :
    L constant = false := by
  rw [← representation_eq]
  exact fold_zero add L linear representation zero zero_trace (by
    intro x hx
    rcases representation_subset x hx with h | h
    · exact kills_left x h
    · exact kills_right x h)

#print axioms pair_span_obstructs_shared_trace

end CertificateCoverage

import Std

/-! A signature that distinguishes the two roots of a complete
point-addition equation selects the intended linked subtotal. -/

universe u v

theorem signature_selects_plus {Point : Type u} {Signature : Type v}
    (signature : Point → Signature) (plus minus candidate : Point)
    (separated : signature plus ≠ signature minus)
    (complete_roots : candidate = plus ∨ candidate = minus)
    (matches_plus : signature candidate = signature plus) :
    candidate = plus := by
  cases complete_roots with
  | inl isPlus => exact isPlus
  | inr isMinus =>
      subst candidate
      exact False.elim (separated matches_plus.symm)

#print axioms signature_selects_plus

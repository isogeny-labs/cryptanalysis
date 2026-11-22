import Std

namespace QuadraticCertificate

/-- A diagonal term has the Boolean-linear value `x i`; off-diagonal terms
have the Boolean-quadratic value `x i && x j`. The term list may contain
either kind and has no constant term. -/
def score {n : Nat} (terms : List (Fin n × Fin n))
    (weight : Fin n × Fin n → Bool) (x : Fin n → Bool) : Bool :=
  (terms.map fun ij => weight ij && x ij.1 && x ij.2).foldl Bool.xor false

theorem score_zero {n : Nat} (terms : List (Fin n × Fin n))
    (weight : Fin n × Fin n → Bool) :
    score terms weight (fun _ => false) = false := by
  induction terms with
  | nil => simp [score]
  | cons ij rest ih =>
      have hrest : List.foldl Bool.xor false
          (rest.map fun _ => false) = false := by simpa [score] using ih
      simpa [score] using hrest

/-- If an exact quadratic score is one on every value in a finite family,
that family cannot contain the zero field-coordinate vector. -/
theorem certificate_excludes_zero {n : Nat} (terms : List (Fin n × Fin n))
    (weight : Fin n × Fin n → Bool) (values : List (Fin n → Bool))
    (hcert : ∀ x ∈ values, score terms weight x = true) :
    (fun _ => false) ∉ values := by
  intro hz
  have h := hcert (fun _ => false) hz
  simp [score_zero] at h

#print axioms QuadraticCertificate.score_zero
#print axioms QuadraticCertificate.certificate_excludes_zero

end QuadraticCertificate

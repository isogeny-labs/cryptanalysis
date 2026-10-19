import Std

namespace GlobalMacaulayDual

/-- A Boolean linear functional that vanishes on each generator also
vanishes on every finite XOR of generators. -/
theorem annihilates_fold {V : Type}
    (xor : V → V → V) (zero : V) (phi : V → Bool)
    (hadd : ∀ x y, phi (xor x y) = Bool.xor (phi x) (phi y))
    (hzero : phi zero = false)
    (rows : List V) (hrows : ∀ row ∈ rows, phi row = false) :
    phi (rows.foldl xor zero) = false := by
  have aux : ∀ (xs : List V) (acc : V),
      phi acc = false →
      (∀ row ∈ xs, phi row = false) →
      phi (xs.foldl xor acc) = false := by
    intro xs
    induction xs with
    | nil =>
      intro acc hacc _
      simpa using hacc
    | cons x tail ih =>
      intro acc hacc hs
      have hx : phi x = false := hs x (by simp)
      have ht : ∀ row ∈ tail, phi row = false := by
        intro row hmem
        exact hs row (by simp [hmem])
      simp only [List.foldl_cons]
      apply ih (xor acc x)
      · rw [hadd, hacc, hx]
        decide
      · exact ht
  exact aux rows zero hzero hrows

/-- A dual functional separating the constant row from all Macaulay
rows excludes a constant-one row-span certificate. -/
theorem no_constant_certificate {V : Type}
    (xor : V → V → V) (zero one : V) (phi : V → Bool)
    (hadd : ∀ x y, phi (xor x y) = Bool.xor (phi x) (phi y))
    (hzero : phi zero = false) (hone : phi one = true)
    (rows : List V) (hrows : ∀ row ∈ rows, phi row = false) :
    rows.foldl xor zero ≠ one := by
  intro heq
  have hfold := annihilates_fold xor zero phi hadd hzero rows hrows
  rw [heq, hone] at hfold
  cases hfold

#print axioms annihilates_fold
#print axioms no_constant_certificate
end GlobalMacaulayDual

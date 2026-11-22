import Std

namespace FamilyResultant

/-- Product of characteristic-two differences from one root to a family. -/
def pairProduct (mul : Nat → Nat → Nat) (a : Nat) : List Nat → Nat
  | [] => 1
  | b :: bs => mul (a ^^^ b) (pairProduct mul a bs)

/-- Product of all pairwise characteristic-two differences. -/
def familyProduct (mul : Nat → Nat → Nat) (bs : List Nat) : List Nat → Nat
  | [] => 1
  | a :: as => mul (pairProduct mul a bs) (familyProduct mul bs as)

private theorem xor_zero_iff_eq (a b : Nat) : (a ^^^ b = 0) ↔ a = b := by
  constructor
  · intro h
    have h' := congrArg (fun x : Nat => x ^^^ b) h
    simpa [Nat.xor_assoc, Nat.xor_self] using h'
  · intro h
    rw [h, Nat.xor_self]

/-- A pair product vanishes exactly when its fixed root appears in the family. -/
theorem pairProduct_zero_iff (mul : Nat → Nat → Nat)
    (hzero : ∀ x y, mul x y = 0 ↔ x = 0 ∨ y = 0)
    (a : Nat) (bs : List Nat) :
    pairProduct mul a bs = 0 ↔ a ∈ bs := by
  induction bs with
  | nil => simp [pairProduct]
  | cons b rest ih =>
      simp [pairProduct, hzero, xor_zero_iff_eq, ih, List.mem_cons]

/-- Under the field's no-zero-divisors law, the resultant vanishes exactly
    when the two finite root families share a root. -/
theorem familyProduct_zero_iff_common (mul : Nat → Nat → Nat)
    (hzero : ∀ x y, mul x y = 0 ↔ x = 0 ∨ y = 0)
    (as bs : List Nat) :
    familyProduct mul bs as = 0 ↔ ∃ a, a ∈ as ∧ a ∈ bs := by
  induction as with
  | nil => simp [familyProduct]
  | cons a rest ih =>
      simp [familyProduct, hzero, pairProduct_zero_iff mul hzero, ih,
        List.mem_cons]

#print axioms FamilyResultant.pairProduct_zero_iff
#print axioms FamilyResultant.familyProduct_zero_iff_common

end FamilyResultant

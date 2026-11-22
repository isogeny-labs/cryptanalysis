import Std

namespace ThreeFamilyProduct

/-- Product of determinant values over a third family. -/
def thirdProduct (mul : Nat → Nat → Nat) (det : Nat → Nat → Nat → Nat)
    (a b : Nat) : List Nat → Nat
  | [] => 1
  | c :: cs => mul (det a b c) (thirdProduct mul det a b cs)

/-- Product over the second and third families. -/
def secondProduct (mul : Nat → Nat → Nat) (det : Nat → Nat → Nat → Nat)
    (a : Nat) (bs cs : List Nat) : Nat :=
  bs.foldr (fun b rest => mul (thirdProduct mul det a b cs) rest) 1

/-- Exact finite eliminant for three code families. -/
def familyProduct (mul : Nat → Nat → Nat) (det : Nat → Nat → Nat → Nat)
    (as bs cs : List Nat) : Nat :=
  as.foldr (fun a rest => mul (secondProduct mul det a bs cs) rest) 1

private theorem exists_cons_iff {P : Nat → Prop} (a : Nat) (xs : List Nat) :
    (P a ∨ ∃ x ∈ xs, P x) ↔ ∃ x ∈ a :: xs, P x := by
  constructor
  · intro h
    rcases h with h | ⟨x, hx, hp⟩
    · exact ⟨a, List.mem_cons_self, h⟩
    · exact ⟨x, List.mem_cons_of_mem a hx, hp⟩
  · rintro ⟨x, hx, hp⟩
    rcases List.mem_cons.mp hx with rfl | hx
    · exact Or.inl hp
    · exact Or.inr ⟨x, hx, hp⟩

theorem thirdProduct_zero_iff (mul : Nat → Nat → Nat)
    (hzero : ∀ x y, mul x y = 0 ↔ x = 0 ∨ y = 0)
    (det : Nat → Nat → Nat → Nat) (a b : Nat) (cs : List Nat) :
    thirdProduct mul det a b cs = 0 ↔ ∃ c ∈ cs, det a b c = 0 := by
  induction cs with
  | nil => simp [thirdProduct]
  | cons c rest ih =>
      change mul (det a b c) (thirdProduct mul det a b rest) = 0 ↔
        ∃ x ∈ c :: rest, det a b x = 0
      rw [hzero, ih]
      exact exists_cons_iff (P := fun x => det a b x = 0) c rest

theorem secondProduct_zero_iff (mul : Nat → Nat → Nat)
    (hzero : ∀ x y, mul x y = 0 ↔ x = 0 ∨ y = 0)
    (det : Nat → Nat → Nat → Nat) (a : Nat) (bs cs : List Nat) :
    secondProduct mul det a bs cs = 0 ↔
      ∃ b ∈ bs, ∃ c ∈ cs, det a b c = 0 := by
  induction bs with
  | nil => simp [secondProduct]
  | cons b rest ih =>
      change mul (thirdProduct mul det a b cs)
        (secondProduct mul det a rest cs) = 0 ↔
          ∃ x ∈ b :: rest, ∃ c ∈ cs, det a x c = 0
      rw [hzero, thirdProduct_zero_iff mul hzero, ih]
      exact exists_cons_iff (P := fun x => ∃ c ∈ cs, det a x c = 0) b rest

theorem familyProduct_zero_iff (mul : Nat → Nat → Nat)
    (hzero : ∀ x y, mul x y = 0 ↔ x = 0 ∨ y = 0)
    (det : Nat → Nat → Nat → Nat) (as bs cs : List Nat) :
    familyProduct mul det as bs cs = 0 ↔
      ∃ a ∈ as, ∃ b ∈ bs, ∃ c ∈ cs, det a b c = 0 := by
  induction as with
  | nil => simp [familyProduct]
  | cons a rest ih =>
      change mul (secondProduct mul det a bs cs)
        (familyProduct mul det rest bs cs) = 0 ↔
          ∃ x ∈ a :: rest, ∃ b ∈ bs, ∃ c ∈ cs, det x b c = 0
      rw [hzero, secondProduct_zero_iff mul hzero, ih]
      exact exists_cons_iff (P := fun x => ∃ b ∈ bs, ∃ c ∈ cs, det x b c = 0) a rest

#print axioms ThreeFamilyProduct.thirdProduct_zero_iff
#print axioms ThreeFamilyProduct.secondProduct_zero_iff
#print axioms ThreeFamilyProduct.familyProduct_zero_iff

end ThreeFamilyProduct

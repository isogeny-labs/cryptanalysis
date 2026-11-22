import Std

/-! A homomorphic class map sends inverse points to inverse classes. -/
namespace ClassBound

structure GroupModel (G : Type) where
  add : G → G → G
  neg : G → G
  zero : G
  add_assoc : ∀ x y z, add (add x y) z = add x (add y z)
  zero_add : ∀ x, add zero x = x
  add_zero : ∀ x, add x zero = x
  add_neg : ∀ x, add x (neg x) = zero
  neg_unique : ∀ x y, add x y = zero → y = neg x

structure Hom {G H : Type} (A : GroupModel G) (B : GroupModel H) where
  map : G → H
  map_add : ∀ x y, map (A.add x y) = B.add (map x) (map y)
  map_zero : map A.zero = B.zero

variable {G H : Type} (A : GroupModel G) (B : GroupModel H)

theorem class_neg (φ : Hom A B) (p : G) :
    φ.map (A.neg p) = B.neg (φ.map p) := by
  have h : B.add (φ.map p) (φ.map (A.neg p)) = B.zero := by
    calc
      B.add (φ.map p) (φ.map (A.neg p)) =
          φ.map (A.add p (A.neg p)) := (φ.map_add p (A.neg p)).symm
      _ = φ.map A.zero := by rw [A.add_neg]
      _ = B.zero := φ.map_zero
  exact B.neg_unique (φ.map p) (φ.map (A.neg p)) h

theorem signed_x_fiber_has_at_most_two_classes
    (φ : Hom A B) (p q : G) (hq : q = p ∨ q = A.neg p) :
    φ.map q = φ.map p ∨ φ.map q = B.neg (φ.map p) := by
  rcases hq with rfl | rfl
  · exact Or.inl rfl
  · exact Or.inr (class_neg A B φ p)

def publicRawLabel (i : Fin 4) : Fin 4 :=
  match i.val with
  | 0 => 0
  | 1 => 2
  | 2 => 1
  | _ => 3

theorem public_raw_labels_bijective :
    (∀ i j : Fin 4, publicRawLabel i = publicRawLabel j → i = j) ∧
    (∀ c : Fin 4, ∃ i : Fin 4, publicRawLabel i = c) := by
  decide

#print axioms ClassBound.class_neg
#print axioms ClassBound.signed_x_fiber_has_at_most_two_classes
#print axioms ClassBound.public_raw_labels_bijective

end ClassBound

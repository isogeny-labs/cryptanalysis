module

public import Init

namespace NullCompletion

universe u

/-- The group laws needed for the cancellation-count uniqueness step. -/
public structure AddGroupData (G : Type u) where
  add : G → G → G
  zero : G
  neg : G → G
  add_assoc : ∀ a b c : G, add (add a b) c = add a (add b c)
  zero_add : ∀ a : G, add zero a = a
  add_zero : ∀ a : G, add a zero = a
  neg_add : ∀ a : G, add (neg a) a = zero
  add_neg : ∀ a : G, add a (neg a) = zero

public theorem pair_completion_exists {G : Type u} (H : AddGroupData G) (a : G) :
    H.add a (H.neg a) = H.zero := H.add_neg a

public theorem pair_completion_unique {G : Type u} (H : AddGroupData G)
    (a b : G) (h : H.add a b = H.zero) : b = H.neg a := by
  calc
    b = H.add H.zero b := (H.zero_add b).symm
    _ = H.add (H.add (H.neg a) a) b := by rw [H.neg_add a]
    _ = H.add (H.neg a) (H.add a b) := H.add_assoc (H.neg a) a b
    _ = H.add (H.neg a) H.zero := by rw [h]
    _ = H.neg a := H.add_zero (H.neg a)

public theorem triple_completion_exists {G : Type u} (H : AddGroupData G)
    (a b : G) : H.add (H.add a b) (H.neg (H.add a b)) = H.zero :=
  H.add_neg (H.add a b)

public theorem triple_completion_unique {G : Type u} (H : AddGroupData G)
    (a b c : G) (h : H.add (H.add a b) c = H.zero) :
    c = H.neg (H.add a b) :=
  pair_completion_unique H (H.add a b) c h

public theorem nonzero_sum_has_nonzero_completion {G : Type u} (H : AddGroupData G)
    (a b : G) (h : H.add a b ≠ H.zero) :
    H.neg (H.add a b) ≠ H.zero := by
  intro hz
  have hs : H.add a b = H.zero := by
    calc
      H.add a b = H.add H.zero (H.add a b) := (H.zero_add (H.add a b)).symm
      _ = H.add (H.neg (H.add a b)) (H.add a b) := by rw [hz]
      _ = H.zero := H.neg_add (H.add a b)
  exact h hs

#print axioms pair_completion_exists
#print axioms pair_completion_unique
#print axioms triple_completion_exists
#print axioms triple_completion_unique
#print axioms nonzero_sum_has_nonzero_completion

end NullCompletion

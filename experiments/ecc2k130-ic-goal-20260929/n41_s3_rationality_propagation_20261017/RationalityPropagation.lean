import Std

namespace RationalityPropagation

/-- The group identities used by the Frobenius argument. These hold in every
    elliptic-curve point group; the concrete curve bridge is separate. -/
structure GroupLaws (α : Type) where
  add : α → α → α
  neg : α → α
  zero : α
  add_left_cancel : ∀ a b c, add a b = add a c → b = c
  add_right_cancel : ∀ a b c, add a c = add b c → a = b
  neg_add_cancel : ∀ a, add (neg a) a = zero
  neg_add : ∀ a b, add (neg a) (neg b) = neg (add a b)

/-- A point whose field-fixed x-coordinate has two distinct lifts is sent by
    Frobenius either to itself or to its group inverse. -/
theorem rational_children_of_rational_sum
    {α : Type} (G : GroupLaws α) (frobenius : α → α)
    (P Q : α)
    (map_add : ∀ a b, frobenius (G.add a b) =
                         G.add (frobenius a) (frobenius b))
    (sum_fixed : frobenius (G.add P Q) = G.add P Q)
    (P_fiber : frobenius P = P ∨ frobenius P = G.neg P)
    (Q_fiber : frobenius Q = Q ∨ frobenius Q = G.neg Q)
    (P_not_two_torsion : G.add P P ≠ G.zero)
    (Q_not_two_torsion : G.add Q Q ≠ G.zero)
    (sum_not_two_torsion : G.add (G.add P Q) (G.add P Q) ≠ G.zero) :
    frobenius P = P ∧ frobenius Q = Q := by
  rcases P_fiber with hP | hP
  · rcases Q_fiber with hQ | hQ
    · exact ⟨hP, hQ⟩
    · have h : G.add P (G.neg Q) = G.add P Q := by
        calc
          G.add P (G.neg Q) = G.add (frobenius P) (frobenius Q) := by rw [hP, hQ]
          _ = frobenius (G.add P Q) := (map_add P Q).symm
          _ = G.add P Q := sum_fixed
      have hn : G.neg Q = Q := G.add_left_cancel P (G.neg Q) Q h
      have ht : G.add Q Q = G.zero := by
        calc
          G.add Q Q = G.add (G.neg Q) Q := by rw [hn]
          _ = G.zero := G.neg_add_cancel Q
      exact False.elim (Q_not_two_torsion ht)
  · rcases Q_fiber with hQ | hQ
    · have h : G.add (G.neg P) Q = G.add P Q := by
        calc
          G.add (G.neg P) Q = G.add (frobenius P) (frobenius Q) := by rw [hP, hQ]
          _ = frobenius (G.add P Q) := (map_add P Q).symm
          _ = G.add P Q := sum_fixed
      have hn : G.neg P = P := G.add_right_cancel (G.neg P) P Q h
      have ht : G.add P P = G.zero := by
        calc
          G.add P P = G.add (G.neg P) P := by rw [hn]
          _ = G.zero := G.neg_add_cancel P
      exact False.elim (P_not_two_torsion ht)
    · have h : G.neg (G.add P Q) = G.add P Q := by
        calc
          G.neg (G.add P Q) = G.add (G.neg P) (G.neg Q) := (G.neg_add P Q).symm
          _ = G.add (frobenius P) (frobenius Q) := by rw [hP, hQ]
          _ = frobenius (G.add P Q) := (map_add P Q).symm
          _ = G.add P Q := sum_fixed
      have ht : G.add (G.add P Q) (G.add P Q) = G.zero := by
        calc
          G.add (G.add P Q) (G.add P Q) =
              G.add (G.neg (G.add P Q)) (G.add P Q) := by rw [h]
          _ = G.zero := G.neg_add_cancel (G.add P Q)
      exact False.elim (sum_not_two_torsion ht)

#print axioms RationalityPropagation.rational_children_of_rational_sum

end RationalityPropagation

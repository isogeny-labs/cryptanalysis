import Mathlib.Algebra.Group.Basic

namespace CommonTranslation

theorem same_translation_preserves_difference
    {G : Type*} [AddCommGroup G] (a b t : G) :
    (a + t) - (b + t) = a - b := by
  simp [sub_eq_add_neg, add_comm, add_left_comm, add_assoc]

#print axioms same_translation_preserves_difference

end CommonTranslation

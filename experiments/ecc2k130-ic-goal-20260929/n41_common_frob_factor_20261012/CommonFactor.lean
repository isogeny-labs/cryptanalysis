import Std

/-! A shared additive endomorphism factors out of five summands.
    The concrete Frobenius and subgroup bridges are recorded separately. -/

theorem common_factor_two {Point : Type}
    (add : Point → Point → Point) (f : Point → Point)
    (assoc : ∀ a b c, add (add a b) c = add a (add b c))
    (comm : ∀ a b, add a b = add b a)
    (f_add : ∀ a b, f (add a b) = add (f a) (f b))
    (a b : Point) :
    add (add a (f a)) (add b (f b)) = add (add a b) (f (add a b)) := by
  rw [f_add]
  calc
    add (add a (f a)) (add b (f b)) =
        add a (add (f a) (add b (f b))) := assoc a (f a) (add b (f b))
    _ = add a (add b (add (f a) (f b))) := by
      rw [← assoc (f a) b (f b), comm (f a) b, assoc b (f a) (f b)]
    _ = add (add a b) (add (f a) (f b)) := (assoc a b (add (f a) (f b))).symm

theorem common_factor_five {Point : Type}
    (add : Point → Point → Point) (f : Point → Point)
    (assoc : ∀ a b c, add (add a b) c = add a (add b c))
    (comm : ∀ a b, add a b = add b a)
    (f_add : ∀ a b, f (add a b) = add (f a) (f b))
    (a b c d e : Point) :
    add (add (add (add (add a (f a)) (add b (f b)))
      (add c (f c))) (add d (f d))) (add e (f e)) =
    add (add (add (add (add a b) c) d) e)
      (f (add (add (add (add a b) c) d) e)) := by
  rw [common_factor_two add f assoc comm f_add a b]
  rw [common_factor_two add f assoc comm f_add (add a b) c]
  rw [common_factor_two add f assoc comm f_add (add (add a b) c) d]
  rw [common_factor_two add f assoc comm f_add (add (add (add a b) c) d) e]

#print axioms common_factor_two
#print axioms common_factor_five

import Std

namespace JointResidual

/-- The group laws needed for exact target subtraction. The source curve
supplies these laws through its ordinary point group. -/
structure GroupLaws (G : Type) where
  zero : G
  add : G → G → G
  neg : G → G
  assoc : ∀ a b c, add (add a b) c = add a (add b c)
  right_neg : ∀ a, add a (neg a) = zero
  right_zero : ∀ a, add a zero = a

def subtract {G : Type} (g : GroupLaws G) (a b : G) : G :=
  g.add a (g.neg b)

theorem cancel_right {G : Type} (g : GroupLaws G) (a b : G) :
    g.add (g.add a b) (g.neg b) = a := by
  calc
    g.add (g.add a b) (g.neg b) =
        g.add a (g.add b (g.neg b)) := g.assoc a b (g.neg b)
    _ = g.add a g.zero := by rw [g.right_neg b]
    _ = a := g.right_zero a

/-- Any five-block target relation places the first-three-block sum at
the target residual after subtracting the last two blocks. -/
theorem first_three_is_target_residual {G : Type} (g : GroupLaws G)
    (z e₃ e₄ target : G)
    (relation : g.add (g.add z e₃) e₄ = target) :
    z = subtract g (subtract g target e₄) e₃ := by
  have first_four : g.add z e₃ = subtract g target e₄ := by
    calc
      g.add z e₃ = g.add (g.add (g.add z e₃) e₄) (g.neg e₄) :=
        (cancel_right g (g.add z e₃) e₄).symm
      _ = subtract g target e₄ := by rw [relation]; rfl
  calc
    z = g.add (g.add z e₃) (g.neg e₃) :=
      (cancel_right g z e₃).symm
    _ = subtract g (subtract g target e₄) e₃ := by rw [first_four]; rfl

/-- Any coordinate map and prefix map preserve that necessary target
residual equality. -/
theorem prefix_is_necessary {G Coord Prefix : Type} (g : GroupLaws G)
    (coordinate : G → Coord) (prefixCoordinate : Coord → Prefix)
    (z e₃ e₄ target : G)
    (relation : g.add (g.add z e₃) e₄ = target) :
    prefixCoordinate (coordinate z) =
      prefixCoordinate (coordinate (subtract g (subtract g target e₄) e₃)) := by
  rw [first_three_is_target_residual g z e₃ e₄ target relation]

#print axioms JointResidual.cancel_right
#print axioms JointResidual.first_three_is_target_residual
#print axioms JointResidual.prefix_is_necessary

end JointResidual

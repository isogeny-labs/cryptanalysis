import Mathlib.Data.Finset.Card
import Mathlib.Data.Fintype.Card

namespace GeometricFiber

/-- The finite-fiber implication used in the geometric census: absence of
    off-diagonal collisions gives all 24 distinct image points.  The
    concrete modular evaluation and its certificate are separate inputs. -/
theorem image_card_of_pairwise_separation
    {Output : Type*} [DecidableEq Output]
    (projection : Fin 24 → Output)
    (separated : ∀ i j : Fin 24, projection i = projection j → i = j) :
    (Finset.univ.image projection).card = 24 := by
  have hinj : Function.Injective projection := by
    intro i j h
    exact separated i j h
  simpa using Finset.card_image_of_injective (Finset.univ : Finset (Fin 24)) hinj

#print axioms image_card_of_pairwise_separation

end GeometricFiber

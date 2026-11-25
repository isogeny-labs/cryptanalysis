import Mathlib.Data.Finset.Card
import Mathlib.Data.Fintype.Card

namespace YPrimitive

/-- If all 24 specialized sheets have different y-coordinates, that
    coordinate has a 24-element image on this fiber.  The concrete
    finite-field separation and generic modular bridge are external inputs. -/
theorem y_image_card
    {Coordinate : Type*} [DecidableEq Coordinate]
    (y : Fin 24 → Coordinate)
    (separated : ∀ i j : Fin 24, y i = y j → i = j) :
    (Finset.univ.image y).card = 24 := by
  have hinj : Function.Injective y := by
    intro i j h
    exact separated i j h
  simpa using Finset.card_image_of_injective (Finset.univ : Finset (Fin 24)) hinj

#print axioms y_image_card

end YPrimitive

import Std

namespace M31PackedLift

/-- One logical output row for each live input whose ordinate is present. -/
def rows (ordinate : Nat → Option Nat) (xs : List Nat) :=
  xs.filterMap (fun x => (ordinate x).map (fun y => (x, y)))

theorem ignore_padding (ordinate : Nat → Option Nat) (xs padding : List Nat) :
    rows ordinate ((xs ++ padding).take xs.length) = rows ordinate xs := by simp

theorem compact_chunks (ordinate : Nat → Option Nat) (blocks : List (List Nat)) :
    (blocks.map (rows ordinate)).flatten = rows ordinate blocks.flatten := by
  induction blocks with
  | nil => rfl
  | cons block blocks ih => simp only [List.map_cons, List.flatten_cons, ih]; exact (List.filterMap_append).symm

theorem zip_columns (points : List (Nat × Nat)) :
    (points.map Prod.fst).zip (points.map Prod.snd) = points := by
  induction points with
  | nil => rfl
  | cons point points ih => simp [ih]

end M31PackedLift

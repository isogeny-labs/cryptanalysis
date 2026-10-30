module

public import Init

/-! Exact free-module cancellation of four repeated outside-class trace points.
Coordinate 20 is the shared outside point for each theorem. -/
namespace OrbitCancellation

public def sparse (entries : List (Nat × Int)) (i : Fin 21) : Int :=
  entries.foldl (fun total entry => if i.val == entry.1 then total + entry.2 else total) 0

public def first_8_19 (i : Fin 21) : Int := sparse [(0, 1), (4, 1), (8, -1), (20, 1)] i
public def later_8_19 (i : Fin 21) : Int := sparse [(6, 1), (10, 1), (19, -1), (20, 1)] i
public def result_8_19 (i : Fin 21) : Int := sparse [(0, -1), (4, -1), (6, 1), (8, 1), (10, 1), (19, -1)] i
public theorem cancel_8_19 : ∀ i : Fin 21,
    later_8_19 i - first_8_19 i = result_8_19 i := by
  decide
#print axioms cancel_8_19

public def first_2_4 (i : Fin 21) : Int := sparse [(2, -1), (3, 1), (10, 1), (20, 1)] i
public def later_2_4 (i : Fin 21) : Int := sparse [(1, 1), (4, -1), (8, 1), (20, 1)] i
public def result_2_4 (i : Fin 21) : Int := sparse [(1, 1), (2, 1), (3, -1), (4, -1), (8, 1), (10, -1)] i
public theorem cancel_2_4 : ∀ i : Fin 21,
    later_2_4 i - first_2_4 i = result_2_4 i := by
  decide
#print axioms cancel_2_4

public def first_7_9 (i : Fin 21) : Int := sparse [(7, -1), (13, 1), (15, 1), (20, 1)] i
public def later_7_9 (i : Fin 21) : Int := sparse [(5, 1), (9, -1), (16, 1), (20, 1)] i
public def result_7_9 (i : Fin 21) : Int := sparse [(5, 1), (7, 1), (9, -1), (13, -1), (15, -1), (16, 1)] i
public theorem cancel_7_9 : ∀ i : Fin 21,
    later_7_9 i - first_7_9 i = result_7_9 i := by
  decide
#print axioms cancel_7_9

public def first_11_15 (i : Fin 21) : Int := sparse [(11, -1), (16, 1), (17, 1), (20, 1)] i
public def later_11_15 (i : Fin 21) : Int := sparse [(7, 1), (14, 1), (15, -1), (20, 1)] i
public def result_11_15 (i : Fin 21) : Int := sparse [(7, 1), (11, 1), (14, 1), (15, -1), (16, -1), (17, -1)] i
public theorem cancel_11_15 : ∀ i : Fin 21,
    later_11_15 i - first_11_15 i = result_11_15 i := by
  decide
#print axioms cancel_11_15

end OrbitCancellation

import Std

namespace M31SubsetFrontier.PayloadCounterexample

/-- Coefficients of P in the signed basis P, -P, 3P, -3P in the
archived cyclic group. The group order differs from the coordinate modulus. -/
private def order := 2147505293
private def signed : List Nat := [1, order - 1, 3, order - 3]

private def firstPair (target : Nat) : Option (Nat × Nat) :=
  let indices := List.range signed.length
  let pairs := indices.flatMap fun i =>
    (indices.filter (fun j => i ≤ j)).map (fun j => (i,j))
  pairs.find? fun (i,j) => (signed[i]! + signed[j]!) % order == target

/-- The first witnesses for opposite group elements need not reverse signs.
The reversal of indices (0,0) is (1,1), which is a later witness for -2P. -/
theorem opposite_first_witnesses :
    firstPair 2 = some (0,0) ∧
    firstPair (order - 2) = some (0,3) ∧
    (signed[1]! + signed[1]!) % order = order - 2 := by decide

end M31SubsetFrontier.PayloadCounterexample

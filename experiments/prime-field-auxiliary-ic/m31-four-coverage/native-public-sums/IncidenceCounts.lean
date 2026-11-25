import RectangleFree

namespace IncidenceCounts
open RectangleFree

/-- Set of point IDs encoded as a natural-number bit mask. -/
def mask (xs : List Nat) : Nat :=
  xs.foldl (fun bits x => bits ||| (1 <<< x)) 0

/-- Three different lines form a six-cycle precisely when each pair meets
and the three intersections are not concurrent (pairwise uniqueness is
RectangleFree.intersection_size). Count each line triple in increasing order. -/
def sixCycles : Nat := Id.run do
  let masks := lines.map mask
  let mut count := 0
  for k in [:masks.size] do
    for j in [:k] do
      let jk := masks[j]! &&& masks[k]!
      if jk != 0 then
        for i in [:j] do
          let v := masks[i]!
          if v &&& masks[j]! != 0 && v &&& masks[k]! != 0 && v &&& jk == 0 then
            count := count + 1
  return count

/-- At (p,L), count points of L distinct from p that share a line with p.
Modulo two, subtracting seven times the incidence entry adds that entry. -/
def oddEntries : Nat := Id.run do
  let mut count := 0
  for p in [:64] do
    let neighbors := lines.foldl (fun bits line =>
      if line.contains p then bits ||| mask line else bits) 0
    for line in lines do
      let adjacent := line.countP (fun x => x != p && neighbors.testBit x)
      count := count + (adjacent + (if line.contains p then 1 else 0)) % 2
  return count

theorem frozen_counts : sixCycles = 31360 ∧ oddEntries = 1792 := by
  native_decide

#print axioms frozen_counts
end IncidenceCounts

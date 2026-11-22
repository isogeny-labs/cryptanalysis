import Mathlib

namespace SignedGraphCounts

-- The two counts are for connected trees and connected components with one
-- unbalanced cycle, with labels on the vertices and signs on the edges.
def components (j : Nat) : Nat × Nat := Id.run do
  let tree := 2^(j-1)*j^(j-2)
  let mut oneCycle := j*tree
  for l in [2:j+1] do
    let core := if l=2 then 1 else (l-1).factorial*2^(l-2)
    let attach := if l=j then 1 else l*j^(j-l-1)*2^(j-l)
    oneCycle := oneCycle + j.choose l * core * attach
  return (tree,oneCycle)

def table (k : Nat) : Array (Array Nat) := Id.run do
  let mut rows := #[#[1]]
  for n in [1:k+1] do
    let mut row := #[]
    for r in [0:n+1] do
      let mut count := 0
      for j in [1:n+1] do
        let (t,u) := components j
        let prev := rows[n-j]!
        let a := if j-1 ≤ r then prev[r-(j-1)]?.getD 0 else 0
        let b := if j ≤ r then prev[r-j]?.getD 0 else 0
        count := count + (n-1).choose (j-1) * (t*a+u*b)
      row := row.push count
    rows := rows.push row
  return rows

-- Expected uniform group queries to the first dependency under the stated
-- model. Conditional on an independent r-subset, there are 2*(k²-r)
-- distinct usable points whose next occurrence gives a previously unseen row.
def expectedQueries (k : Nat) : ℚ := Id.run do
  let counts := (table k)[k]!
  let mut total : ℚ := 0
  for r in [0:k+1] do
    total := total + (counts[r]! : ℚ) / ((k*k).choose r : ℚ) *
      (2147505293 : ℚ) / (2*(k*k-r) : Nat)
  return total

theorem smallCase : (table 5)[5]! = #[1,25,300,2220,10410,25218] := by native_decide

theorem modelRatio : (1220:ℚ)/1000 < expectedQueries 17 / expectedQueries 20 ∧
    expectedQueries 17 / expectedQueries 20 < (1221:ℚ)/1000 := by native_decide

end SignedGraphCounts

import Mathlib

namespace FirstCycle

def trees (j : Nat) : Nat := 2^(j-1) * j^(j-2)

def forests (k : Nat) : Array (Array Nat) := Id.run do
  let mut rows := #[#[1]]
  for n in [1:k+1] do
    let mut row := #[]
    for r in [0:n] do
      let mut total := 0
      for j in [1:min n (r+1)+1] do
        let prev := rows[n-j]!
        total := total + (n-1).choose (j-1) * trees j * (prev[r+1-j]?.getD 0)
      row := row.push total
    rows := rows.push row
  return rows

def firstCycleProbability (k : Nat) (balancedOnly : Bool) : ℚ := Id.run do
  let rows := forests k
  let mut prob : ℚ := 0
  for r in [0:k] do
    let mut events := 0
    for j in [1:min k (r+1)+1] do
      let marked := k.choose j * trees j * ((rows[k-j]!)[r+1-j]?.getD 0)
      let nextEdges := if balancedOnly then j.choose 2 - (j-1) else j*j - (j-1)
      events := events + marked * nextEdges
    prob := prob + (events : ℚ) / (((k*k).choose r * (k*k-r) : Nat) : ℚ)
  return prob

theorem exhaustiveFive : firstCycleProbability 5 true = 932/8855 := by native_decide
theorem check17 : firstCycleProbability 17 false = 1 ∧
    19743/100000 < firstCycleProbability 17 true ∧
    firstCycleProbability 17 true < 19744/100000 := by native_decide

end FirstCycle

import Std

namespace M31Positions
structure Row where
  arm : String
  seed : Nat
  index : Nat
  query : Nat
  lane : Nat

def parse (line : String) : Option Row := do
  let [arm, seed, i, q, lane] := line.splitOn "," | none
  return ⟨arm, ← seed.toNat?, ← i.toNat?, ← q.toNat?, ← lane.toNat?⟩

def rows := ((((include_str "archived_positions.csv").trimAscii.toString).splitOn "\n").drop 1).filterMap parse

def prefixCounts (arm : String) := (List.range 3).map fun seed =>
  (rows.filter fun r => r.arm == arm && r.seed == seed && r.query ≤ 19000000).length

theorem commonPrefix : rows.length = 78 ∧ prefixCounts "v2_chain" = [3,3,7] ∧
    prefixCounts "v2_batch" = [9,13,2] := by native_decide

def seedOne := rows.filter fun r => r.arm == "v2_batch" && r.seed == 1
theorem laneSpread : seedOne.length = 14 ∧ (seedOne.map Row.lane).eraseDups.length = 13 ∧
    (seedOne.map Row.query).getLast? = some 19300166 := by native_decide

end M31Positions

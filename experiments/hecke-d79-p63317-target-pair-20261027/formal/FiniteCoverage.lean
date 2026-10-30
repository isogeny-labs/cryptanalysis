module

public import Init

namespace FiniteCoverage
set_option maxRecDepth 65536
set_option maxHeartbeats 0
public def logs : List Nat := [1, 1657, 1069, 1161, 1243, 215, 2385, 2266, 2394, 2306, 37, 834, 54, 22, 232, 2494, 1370, 1538, 1697, 1288, 993, 2299, 137, 2477, 561, 2158, 373, 146, 169, 2509, 2530, 2316, 2362, 1575, 956, 225, 1970, 265, 874, 1462]
public def targetScalar : Nat := 973
public theorem log_count : logs.length = 40 := by decide
public theorem logs_distinct : logs.eraseDups.length = 40 := by decide
public theorem logs_nonzero : logs.all (· != 0) = true := by decide
public theorem negation_closed :
    logs.all (fun x => logs.contains ((2531 - x) % 2531)) = true := by decide
public def unorderedSums : List Nat :=
  (List.range 40).flatMap (fun i =>
    ((List.range 40).filter (fun j => decide (i <= j))).map
      (fun j => ((logs.getD i 0) + (logs.getD j 0)) % 2531))
public theorem unordered_pattern_count : unorderedSums.length = 820 := by decide
public theorem distinct_coverage : unorderedSums.eraseDups.length = 689 := by decide
public theorem frozen_target_absent : unorderedSums.contains targetScalar = false := by decide
#print axioms log_count
#print axioms logs_distinct
#print axioms logs_nonzero
#print axioms negation_closed
#print axioms unordered_pattern_count
#print axioms distinct_coverage
#print axioms frozen_target_absent
end FiniteCoverage

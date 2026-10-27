module

public import Init

namespace DirectRankGateSeries
public def rankPairs : List (Nat × Nat) := [(32, 34), (35, 39), (31, 34), (32, 35)]
public def falseReject (x : Nat × Nat) : Bool := x.1 < 37 && x.2 >= 39
public theorem one_false_reject :
    (rankPairs.filter falseReject).length = 1 := by decide
public theorem p103357_gate_counterexample :
    falseReject (35, 39) = true := by decide
public theorem three_correct_rejections :
    (rankPairs.filter (fun x => x.1 < 37 && x.2 < 39)).length = 3 := by decide
#print axioms one_false_reject
#print axioms p103357_gate_counterexample
#print axioms three_correct_rejections
end DirectRankGateSeries

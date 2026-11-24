import Mathlib.Tactic.Eval

namespace M31SignedSmoothScore

def rows : List (List Nat) := eval%
  ((include_str "smooth-twist.csv").splitOn "\n").tail.filterMap
    (fun line => (line.splitOn ",").mapM String.toNat?)

def score (seed bound : Nat) (rule : Fin 16) :=
  (rows.map fun row =>
    match row with
    | [s,b,mask,twist,base] =>
      if s = seed ∧ b = bound then (if rule.val.testBit mask then base else twist) else 0
    | _ => 0).sum

-- Bits select the predicted base side for each of the four smoothness masks.
theorem discovery_optimal : ∀ r : Fin 16,
    score 291163 256 r ≤ score 291163 256 1 ∧
    score 291163 1024 r ≤ score 291163 1024 9 ∧
    score 291163 4096 r ≤ score 291163 4096 3 := by decide +kernel

theorem heldout : rows.length = 24 ∧
    score 291164 256 1 = 16279 ∧ score 291164 1024 9 = 16289 ∧
    score 291164 4096 3 = 16285 ∧ score 291164 256 0 = 16484 ∧
    ∀ r : Fin 16, score 291164 256 r ≤ 16514 ∧
      score 291164 1024 r ≤ 16534 ∧ score 291164 4096 r ≤ 16504 := by decide +kernel

end M31SignedSmoothScore

import BoundedCover

namespace M31CoverWork
open M31ArchiveData M31TerminalSeparation

-- Every occurrence is the source of one application of step. A cache
-- keyed by source evaluates step once for each distinct source value.
def sources (x : Nat) : Nat → List Nat
  | 0 => []
  | n+1 => x :: sources (step x) n

def common := archived.flatMap (fun q => sources q.1 31)
def mixed := archived.flatMap (fun q =>
  if label 31 q.1 = 2 then (sources q.1 31).takeWhile (· != 0) else [])

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
theorem exact_costs :
    (common.length, common.toFinset.card) = (527, 502) ∧
    (mixed.length, mixed.toFinset.card) = (202, 191) := by decide +kernel

-- Price one terminal operation at c units and one map evaluation at one
-- unit. Compare the explicit cached schedule with the depth-zero cover.
set_option maxRecDepth 32768 in
theorem mixed_break_even (c : Nat) :
    mixed.toFinset.card + 11*c < 17*c ↔ 32 ≤ c := by
  have h : mixed.toFinset.card = 191 := congrArg Prod.snd exact_costs.2
  rw [h]
  omega
end M31CoverWork

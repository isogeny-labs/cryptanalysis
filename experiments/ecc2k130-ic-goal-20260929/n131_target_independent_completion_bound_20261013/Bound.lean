import Std

/-! Ordered representation count for target-independent three-pair proposals
followed by two source-pair completions. Distinct target cardinality is at
most this length; the stronger unordered and probability bounds use the
concrete source law and are recorded in the proof map. -/
namespace ProposalBound
variable {G : Type} [Add G]

def pairJoin (t : G) : List G → List G → List G
  | [], _ => []
  | a :: rest, right => right.map (fun b => t + a + b) ++ pairJoin t rest right

theorem pairJoin_length (t : G) (left right : List G) :
    (pairJoin t left right).length = left.length * right.length := by
  induction left with
  | nil => simp [pairJoin]
  | cons a rest ih =>
    simp [pairJoin, ih, Nat.succ_mul]
    omega

def reachable : List G → List G → List G
  | [], _ => []
  | t :: rest, pairs => pairJoin t pairs pairs ++ reachable rest pairs

theorem reachable_length (triples pairs : List G) :
    (reachable triples pairs).length = triples.length * pairs.length * pairs.length := by
  induction triples with
  | nil => simp [reachable]
  | cons t rest ih =>
    simp [reachable, pairJoin_length, ih, Nat.succ_mul, Nat.add_mul]
    omega

theorem pairJoin_mem_iff (t q : G) (left right : List G) :
    q ∈ pairJoin t left right ↔ ∃ a ∈ left, ∃ b ∈ right, q = t + a + b := by
  induction left with
  | nil => simp [pairJoin]
  | cons a rest ih =>
    simp [pairJoin, ih, List.mem_map, eq_comm]

theorem reachable_mem_iff (q : G) (triples pairs : List G) :
    q ∈ reachable triples pairs ↔
      ∃ t ∈ triples, ∃ a ∈ pairs, ∃ b ∈ pairs, q = t + a + b := by
  induction triples with
  | nil => simp [reachable]
  | cons t rest ih =>
    simp [reachable, pairJoin_mem_iff, ih]

#print axioms ProposalBound.pairJoin_length
#print axioms ProposalBound.reachable_length
#print axioms ProposalBound.reachable_mem_iff
end ProposalBound

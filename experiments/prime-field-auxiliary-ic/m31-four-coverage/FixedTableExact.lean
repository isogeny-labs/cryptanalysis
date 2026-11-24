import FixedOrbitExact
import CanonicalLift

namespace M31FixedTableExact

open M31FiberRecurrence M31PanelInitializer M31FixedWeights M31FixedOrbitExact
open M31CanonicalLift M31PairedCubic

-- The fresh terminal panel uses odd powers 129,131,...,191.
def fresh : List Nat := [
  386028061, 409735712, 1068829641, 1674955285,
  1307008238, 53516727, 1411936336, 546456186,
  1888676053, 665013137, 917941791, 1212402559,
  1569408142, 1296200061, 103844401, 229556753,
  647815302, 1666284893, 1988405926, 299094813,
  2082647567, 1960002306, 644246330, 837699946,
  125377585, 1240453817, 1703250864, 1998287062,
  1498233859, 1647012842, 905031289, 660845652]

private def advance (u : Nat × Nat) : Nat × Nat :=
  (u.2, (340921998*u.2+2147483647-u.1)%2147483647)

set_option maxRecDepth 32768 in
theorem fresh_trace_identity :
    fresh = (List.range 32).map (fun i => (advance^[129+2*i] (2,340921998)).1) := by decide +kernel

def qualified (n : Nat) : Prop :=
  seedOK (leaf n) (fixedNeighbor (leaf n)) ∧ forward^[7] (leaf n) = n ∧
    (n : M) ≠ 2 ∧ (n : M) ≠ -2

private instance (n : Nat) : Decidable (qualified n) := by unfold qualified seedOK; infer_instance

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
private theorem archived : ∀ t ∈ terminals, qualified t := by decide +kernel

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
private theorem heldout : ∀ t ∈ M31HalfOrbit.holdout, qualified t := by decide +kernel

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
private theorem third : ∀ t ∈ fresh, qualified t := by decide +kernel

theorem panel_count : (panel ++ fresh).length = 96 ∧ (panel ++ fresh).Nodup := by decide +kernel

-- The theorem is stated directly for the independent-coordinate formula.
def direct (a b : M) (i : Nat) : M :=
  if i = 0 then a else generated fixed 0 1 i * b - generated fixed 0 1 (i-1) * a

private theorem direct_eq (a b : M) (i : Nat) : direct a b i = generated fixed a b i := by
  cases i with
  | zero => rfl
  | succ n => simpa [direct] using (weighted fixed a b n).symm

def coord (a b : M) (i : Fin 128) : M :=
  if i.val < 64 then direct a b i.val else -direct a b (i.val-64)

private theorem coord_eq (a b : M) (i : Fin 128) :
    coord a b i = generated fixed a b i.val := by
  unfold coord
  split
  · exact direct_eq _ _ _
  · rename_i upper
    rw [direct_eq, ← fixed_half, show i.val-64+64 = i.val by omega]

set_option maxRecDepth 8192 in
theorem packed_panel (n : Nat) (row : n ∈ panel ++ fresh) (eval : M → M) :
    let xs := List.ofFn (coord (leaf n) (fixedNeighbor (leaf n)))
    let table := (xs.filterMap (key eval)).mergeSort
    xs.Nodup ∧ table.Nodup ∧ ∀ x y : M, pack x.val y.val ∈ table ↔
      forward^[7] x = n ∧ y^2 = eval x ∧ y.val ≤ 1073741823 := by
  have ok : qualified n := by
    simp only [panel, List.mem_append] at row
    rcases row with (a | b) | c
    · exact archived _ a
    · exact heldout _ b
    · exact third _ c
  obtain ⟨seed, terminal, pos, neg⟩ := ok
  have good := And.intro (terminal.trans_ne pos) (terminal.trans_ne neg)
  have asFn : coord (leaf n) (fixedNeighbor (leaf n)) =
      fun i : Fin 128 => generated fixed (leaf n) (fixedNeighbor (leaf n)) i.val :=
    funext (coord_eq _ _)
  dsimp only
  rw [asFn]
  have nd := List.nodup_ofFn.mpr (injective_slots _ _ seed good)
  obtain ⟨nt, members⟩ := sorted_keys eval _ nd
  refine ⟨nd, nt, ?_⟩
  intro x y
  rw [members, List.mem_ofFn, ← exhausts _ _ seed good, terminal]

end M31FixedTableExact

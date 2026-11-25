import FixedOrbitExact
import FiberLift

namespace M31Base71
open M31PanelInitializer M31FiberRecurrence M31FixedWeights M31FixedOrbitExact

def first : M := 3
def neighbor := fixedNeighbor first

theorem seed_search (i : Fin 4) :
    forward^[30] (i.val : M) = -2 ↔ i.val = 3 := by
  fin_cases i <;> decide +kernel

theorem terminal : forward^[7] first = 340921998 := by decide +kernel
theorem step : forward^[24] first = fixed := by decide +kernel

theorem complete (x : M) :
    forward^[7] x = 340921998 ↔ ∃ i : Fin 128, generated fixed first neighbor i.val = x := by
  rw [← terminal]
  apply exhausts
  · unfold seedOK neighbor at *; decide +kernel
  · decide +kernel

theorem mirror_check (low high : Fin 64 → M) (t : M)
    (paired : ∀ i, high i = -low i) :
    (∀ i, forward^[7] (low i) = t) ↔
      (∀ i, forward^[7] (low i) = t) ∧ (∀ i, forward^[7] (high i) = t) := by
  refine ⟨fun h => ⟨h,fun i => ?_⟩, And.left⟩
  rw [paired]
  have eq : forward (-low i) = forward (low i) := by simp [forward]
  simpa only [Function.iterate_succ_apply, eq] using h i

def consecutive : Nat → M × M
  | 0 => (first,neighbor)
  | n+1 => let (a,b) := consecutive n; (b,fixed*b-a)

theorem same_orbit (n : Nat) : consecutive n =
    (generated fixed first neighbor n,generated fixed first neighbor (n+1)) := by
  induction n with
  | zero => rfl
  | succ n ih => rw [consecutive,ih]; rfl

def accepted (x : M) : Bool :=
  let rhs := fun z : M => z*z*z + 2*z + 14
  decide ((M31FiberLift.squares rhs 29 x)^2 = rhs x)

theorem accepted_iff (x : M) :
    accepted x = true ↔ ∃ y : M, y^2 = x*x*x+2*x+14 := by
  simpa only [accepted, decide_eq_true_eq, M31FiberLift.lane_power] using
    (M31FiberLift.lift_exact (fun x : M => x*x*x+2*x+14) x)

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
theorem base_count :
    ((List.range 128).filter (fun i => accepted (consecutive i).1)).length = 71 := by
  decide +kernel

def canonicalPoint (x : M) : Option (Nat × Nat) :=
  let rhs := fun z : M => z*z*z + 2*z + 14
  let y := M31FiberLift.squares rhs 29 x
  if y*y = rhs x then some (x.val, min y.val (-y).val) else none

private def parseRow (row : String) : Option (Nat × Nat) :=
  match row.splitOn "," with
  | [x,y] => return (← x.toNat?, ← y.toNat?)
  | _ => none

-- Expand the decimal CSV at elaboration so the kernel checks a literal point list.
elab "base71Fixture" : term => do
  let text := include_str "base71-points.csv"
  let lines := text.splitOn "\n"
  unless lines.getLast? == some "" do throwError "expected a final newline"
  let some rows := lines.dropLast.mapM parseRow | throwError "invalid point row"
  return Lean.toExpr rows

def fixture : List (Nat × Nat) := base71Fixture

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
theorem ordered_fixture :
    fixture.length = 71 ∧ fixture.Pairwise (fun a b => a.1 < b.1) ∧
    (List.range 128).all (fun i =>
      let x := (consecutive i).1
      fixture.lookup x.val == (canonicalPoint x).map Prod.snd) = true := by
  decide +kernel

end M31Base71

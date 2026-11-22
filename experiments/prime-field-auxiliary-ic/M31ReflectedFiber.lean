import Mathlib

/-! The public auxiliary map sends x to u + A + B/u for u = x-r.
Reflecting its source and destination negates r and A. A pole returns none. -/
namespace ReflectedFiber
abbrev Step (F : Type*) := F × F × F
def flip {F : Type*} [Neg F] (s : Step F) : Step F := (-s.1,-s.2.1,s.2.2)
def step {F : Type*} [Field F] [DecidableEq F] (s : Step F) (x : F) : Option F :=
  let u := x-s.1
  if u=0 then none else some (u+s.2.1+s.2.2/u)
theorem step_flip {F : Type*} [Field F] [DecidableEq F] (s : Step F) (x : F) :
    step (flip s) (-x) = (step s x).map Neg.neg := by
  simp only [step, flip, show -x - -s.1 = -(x-s.1) by ring, neg_eq_zero]
  by_cases h : x-s.1=0
  · simp [h]
  · simp only [h, if_false, Option.map_some, Option.some.injEq, div_neg]
    ring
def chain {F : Type*} [Field F] [DecidableEq F] (ss : List (Step F)) (x : F) : Option F :=
  match ss with
  | [] => some x
  | s::rest => (step s x).bind (chain rest)
theorem chain_flip {F : Type*} [Field F] [DecidableEq F] (ss : List (Step F)) (x : F) :
    chain (ss.map flip) (-x) = (chain ss x).map Neg.neg := by
  induction ss generalizing x with
  | nil => rfl
  | cons s rest ih =>
    simp only [List.map_cons, chain, step_flip]
    cases h : step s x with
    | none => rfl
    | some y => exact ih y
/-- Exact membership, including rejection at every pole, transports under reflection. -/
theorem fiber_flip {F : Type*} [Field F] [DecidableEq F] (ss : List (Step F)) (x c : F) :
    chain (ss.map flip) (-x) = some (-c) ↔ chain ss x = some c := by
  rw [chain_flip]
  cases h : chain ss x <;> simp

abbrev M31 := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) := ⟨by native_decide⟩

private def maps : List (Step M31) := [(0, 0, 1),
    (2, 6, 8),
    (262150, 786438, 3145792),
    (135006214, 403445766, 562160130),
    (199756251, 1939860868, 1327400300)]
private def roots : List M31 := [3, 308768278, 1213058799, 1950178058, 1620095117, 1685732321, 845665662, 1760557235, 1393679185, 536276641, 1896314920, 1171458932, 1533993268, 1528659296, 1851652048, 987367763, 1431655765, 1908835095, 1857409341, 975624154, 80168778, 1101836261, 985108144, 2084456163, 753804470, 1900319349, 1900239952, 141165527, 98625645, 1491270739, 2008905047, 1560638367]

/-- The frozen target of the five original maps rejects every reflected root.
The reflected maps take all 32 to the common reflected endpoint. -/
theorem fixture :
    roots.length = 32 ∧ roots.Nodup ∧
    roots.all (fun x => chain maps x == some 1569594640) = true ∧
    roots.all (fun x => chain maps (-x) != some 1569594640) = true ∧
    roots.all (fun x => chain (maps.map flip) (-x) == some 577889007) = true := by
  native_decide
end ReflectedFiber

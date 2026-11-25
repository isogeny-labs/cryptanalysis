import BatchInverse

namespace BatchPoint

variable {F : Type*} [Field F] [DecidableEq F]

abbrev Point (F : Type*) := Option (F × F)
abbrev Lane (F : Type*) := Point F × Point F

def denominator : Lane F → F
  | (some a, some b) => if a.1 = b.1 then 0 else b.1 - a.1
  | _ => 0

def finish (a b : F × F) (s : F) : Point F :=
  let x := s * s - a.1 - b.1
  some (x, s * (a.1 - x) - a.2)

def scalar (A : F) : Lane F → Point F
  | (none, b) => b
  | (some a, none) => some a
  | (some a, some b) =>
    if a.1 = b.1 then
      if a.2 + b.2 = 0 then none
      else finish a b ((3 * (a.1 * a.1) + A) * (a.2 + a.2)⁻¹)
    else finish a b ((b.2 - a.2) * (b.1 - a.1)⁻¹)

def applyLane (A : F) (l : Lane F) (inv : F) : Point F :=
  if denominator l = 0 then scalar A l
  else match l with
    | (some a, some b) => finish a b ((b.2 - a.2) * inv)
    | _ => none

theorem applyLane_correct (A : F) (l : Lane F) :
    applyLane A l (denominator l)⁻¹ = scalar A l := by
  obtain ⟨a,b⟩ := l
  cases a <;> cases b <;> simp [applyLane, denominator, scalar]
  split <;> simp_all [sub_eq_zero]

/-- Recover all inverses from a product rooted at one, then consume them
at the original lane indices. Repeated lanes and exceptional lanes are allowed. -/
def batch (A : F) (ls : List (Lane F)) : List (Point F) :=
  ls.zipWith (applyLane A) (BatchInverse.recover 1 (ls.map denominator)).2

theorem batch_eq_scalar (A : F) (ls : List (Lane F)) :
    batch A ls = ls.map (scalar A) := by
  unfold batch
  rw [BatchInverse.recover_correct _ _ one_ne_zero]
  simp only [List.map_map, Function.comp_def]
  induction ls with
  | nil => rfl
  | cons l ls ih => simp_all [applyLane_correct]

/-- Each row of the schedule supplies the next ordered addends. Record
every resulting state so that equality includes intermediate outputs. -/
def trace (step : List (Lane F) → List (Point F)) (state : List (Point F)) :
    List (List (Point F)) → List (List (Point F))
  | [] => []
  | adds :: later =>
    let next := step (state.zip adds)
    next :: trace step next later

theorem trace_eq_scalar (A : F) (state : List (Point F)) (schedule : List (List (Point F))) :
    trace (batch A) state schedule =
      trace (List.map (scalar A)) state schedule := by
  rw [show batch A = List.map (scalar A) from funext (batch_eq_scalar A)]

#print axioms trace_eq_scalar
end BatchPoint

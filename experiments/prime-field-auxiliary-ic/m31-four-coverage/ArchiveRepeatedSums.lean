import ArchiveSignedSums

namespace M31ArchiveRepeatedSums
open M31ArchiveSignedSums

private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def twice (a : Point) : Option Point :=
  if a.2 = 0 then none else
    let slope := (3*a.1^2+2)/(2*a.2)
    let x := slope^2-2*a.1
    some (x,slope*(a.1-x)-a.2)

def multiple (a : Point) : Nat → Option Point
  | 1 => some a
  | 2 => twice a
  | 3 => (twice a).bind (chord · a)
  | 4 => (twice a).bind twice
  | _ => none

/-- Distribute the absolute coefficient sum among sorted, distinct basis entries. -/
def weighted (budget : Nat) : List Point → List (List (Option Point))
  | [] => if budget = 0 then [[]] else []
  | a::tail => (List.range budget).flatMap fun t =>
      (weighted (budget-(t+1)) tail).map (multiple a (t+1) :: ·)

def evaluate (l : List (Option Point)) : List (Option Point) :=
  match l with
  | [] => []
  | a::rest => rest.foldl (fun partials b => partials.flatMap (fun q =>
        [q.bind (fun v => b.bind (chord v)),
         q.bind (fun v => b.bind (fun w => chord v (w.1,-w.2)))])) [a]

def layer (n : Nat) := ((List.range n).flatMap fun k =>
  (basis.sublistsLen (k+1)).flatMap (weighted n)).flatMap evaluate

def allRows := [1,2,3,4].flatMap layer
def xs := allRows.filterMap (fun q => q.map (fun a => a.1.val))

theorem counts : [1,2,3,4].map (fun n => (layer n).length) = [17,289,3281,28033] := by
  native_decide

theorem finite_points : allRows.all (fun q => match q with
    | none => false
    | some (x,y) => decide (y^2 = x^3+2*x+14 ∧ y≠0)) = true := by native_decide

private theorem ordered : xs.mergeSort.Pairwise (· < ·) := by native_decide

theorem different_abscissae : xs.Nodup :=
  (List.mergeSort_perm _ _).nodup_iff.mp (ordered.imp (fun h => Nat.ne_of_lt h))

end M31ArchiveRepeatedSums

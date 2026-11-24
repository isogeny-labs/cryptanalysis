import ArchiveData
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.Algebra.Field.ZMod
import Mathlib.Data.List.Sublists
import Mathlib.Tactic

namespace M31ArchiveSignedSums

abbrev F := ZMod 2147483647
private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩
abbrev Point := F × F
def basis : List Point := M31ArchiveData.archived.map (fun (x,y) => (x,y))

/-- Fail explicitly on any vertical or tangent chord. -/
def chord (a b : Point) : Option Point := do
  if a.1 = b.1 then none else
    let slope := (b.2-a.2)/(b.1-a.1)
    let x := slope^2-a.1-b.1
    some (x, slope*(a.1-x)-a.2)

/-- The first point has positive sign; every later point has both signs. -/
def sums : List Point → List (Option Point)
  | [] => []
  | a::rest => rest.foldl (fun partials b => partials.flatMap
      (fun q => [q.bind (chord · b), q.bind (chord · (b.1,-b.2))])) [some a]

def rows (n : Nat) := (basis.sublistsLen n).flatMap sums
def panel := ([1,2,3,4].flatMap rows)
def abscissae := panel.filterMap (fun q => q.map (fun pt => pt.1.val))

theorem counts : [1,2,3,4].map (fun n => (rows n).length) = [17,272,2720,19040] := by
  native_decide

theorem finite_points : panel.all (fun q => match q with
    | none => false
    | some (x,y) => decide (y^2=x^3+2*x+14 ∧ y≠0)) = true := by native_decide

private theorem ordered : abscissae.mergeSort.Pairwise (· < ·) := by native_decide

theorem distinct_across_arities : abscissae.Nodup := by
  exact (List.mergeSort_perm _ _).nodup_iff.mp (ordered.imp (fun h => Nat.ne_of_lt h))

end M31ArchiveSignedSums

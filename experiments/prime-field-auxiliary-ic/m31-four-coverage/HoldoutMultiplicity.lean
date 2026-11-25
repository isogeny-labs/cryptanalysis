import ArchiveRepeatedSums

namespace M31HoldoutMultiplicity
open M31ArchiveSignedSums M31ArchiveRepeatedSums

/-- Canonical lifts drawn on the public target curve with Python seed 323222. -/
def input : List Point := [(893117510,83761755),
    (136518158,851576062),
    (89678637,942826699),
    (1741639900,600187988),
    (2088946050,359659888),
    (696630858,447018906),
    (1793120079,258086746),
    (848218908,416904167),
    (290033814,799268687),
    (114311348,587971062),
    (1699742940,739267612),
    (1798090896,978329444),
    (208048621,113722949),
    (1987079298,809018465),
    (357405391,122946561),
    (1109442777,304740704),
    (1764367062,461780592)]

def repeated : List Nat := [98793600, 253268989, 365362231, 379222203, 505513408, 509747917, 556343569, 984082094, 1258876506, 1284641026, 1354518271, 1616935308, 1658742307]

def rows := ((List.range 4).flatMap fun k =>
  (input.sublistsLen (k+1)).flatMap (weighted 4)).flatMap evaluate
def points := rows.filterMap id
def coordinates := points.map (fun pt => pt.1.val)
def singles := coordinates.filter (fun x => !repeated.contains x)

theorem valid : input.length = 17 ∧ input.all (fun q =>
    decide (q.2^2 = q.1^3+2*q.1+14 ∧ q.2.val ≤ 1073741823)) = true ∧
    rows.length = 28033 ∧ points.length = 28033 ∧ points.all (fun q =>
      decide (q.2^2 = q.1^3+2*q.1+14 ∧ q.2 ≠ 0)) = true := by native_decide

theorem doubles : repeated.length = 13 ∧ repeated.Nodup ∧
    ∀ x ∈ repeated, coordinates.count x = 2 := by native_decide

theorem singles_count : singles.length = 28007 := by native_decide

theorem singles_unique : singles.Nodup := by
  have h : singles.mergeSort.Pairwise (· < ·) := by native_decide
  exact (List.mergeSort_perm _ _).nodup_iff.mp (h.imp (fun a => Nat.ne_of_lt a))

/-- Class 1 repeats the full point; class 2 repeats x with opposite nonzero ordinates. -/
def collisionClass (x : Nat) : Nat :=
  match points.filter (fun pt => pt.1.val == x) with
  | [a,b] => if a.2 = b.2 then 1 else if a.2 = -b.2 then 2 else 0
  | _ => 0

theorem orientations : (repeated.map collisionClass).count 1 = 10 ∧
    (repeated.map collisionClass).count 2 = 3 := by native_decide

end M31HoldoutMultiplicity

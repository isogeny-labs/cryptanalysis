import Mathlib

namespace ReflectedPair
notation "Ix" => BitVec 16
abbrev Pair := Ix × Ix

variable {G : Type} [AddCommGroup G]

def signedPoint (basis : Ix → G) (i : Ix) : G :=
  if i &&& 1 = 0 then basis (i >>> (1 : Nat)) else -basis (i >>> (1 : Nat))

theorem toggle (basis : Ix → G) (i : Ix) :
    signedPoint basis (i ^^^ 1) = -signedPoint basis i := by
  have addr : (i ^^^ 1) >>> (1 : Nat) = i >>> (1 : Nat) := by bv_decide
  have parity : ((i ^^^ 1) &&& 1 = 0) ↔ ¬(i &&& 1 = 0) := by bv_decide
  unfold signedPoint
  rw [addr]
  by_cases h : i &&& 1 = 0 <;> simp only [parity, h, if_true, if_false, not_true_eq_false, not_false_eq_true, neg_neg]

def direct (basis : Ix → G) (ij : Pair) :=
  signedPoint basis ij.1 + signedPoint basis ij.2

def reflected (basis : Ix → G) (ij : Pair) :=
  if ij.1 &&& 1 = 0 then direct basis ij
  else -direct basis (ij.1 ^^^ 1, ij.2 ^^^ 1)

theorem reflected_eq (basis : Ix → G) : reflected basis = direct basis := by
  funext ij
  unfold reflected
  split
  · rfl
  · simp only [direct, toggle, neg_add_rev, neg_neg, add_comm]

-- Every source read by an odd row is within its preceding even row's suffix.
theorem source_in_row (i j : Ix) (odd : i &&& 1 ≠ 0) (ordered : i ≤ j) :
    (i ^^^ 1) = i - 1 ∧ i - 1 ≤ (j ^^^ 1) := by bv_decide

theorem source_below_end (j n : Ix) (even : n &&& 1 = 0) (inside : j < n) :
    (j ^^^ 1) < n := by bv_decide

def payload (ij : Pair) := ij.1.toNat * 65536 + ij.2.toNat

-- The visitor can skip infinity/odd ordinates and keep the first payload
-- for each key. The result also holds with duplicate inputs and key collisions.
theorem exact_payloads {Table : Type} (basis : Ix → G) (pairs : List Pair)
    (visit : Table → G → Nat → Table) (initial : Table) :
    pairs.foldl (fun table ij => visit table (reflected basis ij) (payload ij)) initial =
    pairs.foldl (fun table ij => visit table (direct basis ij) (payload ij)) initial := by
  rw [reflected_eq]

-- Triangular rows retain their original indices and increasing column order.
def row (n i : Nat) : List (Nat × Nat) :=
  ((List.range n).drop i).map (fun j => (i, j))

def directRows (n start : Nat) : Nat → List (Nat × Nat)
  | 0 => []
  | remaining + 1 => row n start ++ directRows n (start + 1) remaining

def groupedRows (n start : Nat) : Nat → List (Nat × Nat)
  | 0 => []
  | 1 => row n start
  | remaining + 2 => row n start ++ row n (start + 1) ++
      groupedRows n (start + 2) remaining

theorem grouped_rows_eq (n count : Nat) :
    ∀ start, groupedRows n start count = directRows n start count := by
  induction count using Nat.twoStepInduction with
  | zero => intro start; rfl
  | one => intro start; simp [groupedRows, directRows]
  | more count ih ihNext =>
    intro start
    simp only [groupedRows, directRows]
    rw [ih]
    simp [List.append_assoc, Nat.add_assoc]

theorem grouped_exact_payloads {Table : Type} (basis : Ix → G) (n : Nat)
    (visit : Table → G → Nat → Table) (initial : Table) :
    let encode := fun ij : Nat × Nat =>
      (BitVec.ofNat 16 ij.1, BitVec.ofNat 16 ij.2)
    ((groupedRows n 0 n).map encode).foldl
        (fun table ij => visit table (reflected basis ij) (payload ij)) initial =
    ((directRows n 0 n).map encode).foldl
        (fun table ij => visit table (direct basis ij) (payload ij)) initial := by
  dsimp only
  rw [grouped_rows_eq, exact_payloads]

end ReflectedPair

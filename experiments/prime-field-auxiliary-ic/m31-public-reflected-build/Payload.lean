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

theorem adjacent_row_lengths (m k : Nat) (inside : k < m) :
    (row (2 * m) (2 * k)).length = 2 * (m - k) ∧
    (row (2 * m) (2 * k + 1)).length = 2 * (m - k) - 1 := by
  simp only [row, List.length_map, List.length_drop, List.length_range]
  omega

-- Reindexed suffix lengths for m signed pairs. The direct traversal submits
-- both suffixes of lengths 2m and 2m-1. Reflection submits the first suffix
-- and reconstructs the second. Counts include inputs whose sum is infinity.
def directInputs : Nat → Nat
  | 0 => 0
  | m + 1 => 2 * (m + 1) + (2 * m + 1) + directInputs m

def reflectedInputs : Nat → Nat
  | 0 => 0
  | m + 1 => 2 * (m + 1) + reflectedInputs m

def reconstructedInputs : Nat → Nat
  | 0 => 0
  | m + 1 => (2 * m + 1) + reconstructedInputs m

theorem direct_input_count (m : Nat) : directInputs m = m * (2 * m + 1) := by
  induction m with
  | zero => rfl
  | succ m ih => simp only [directInputs, ih]; ring

theorem reflected_input_count (m : Nat) : reflectedInputs m = m * (m + 1) := by
  induction m with
  | zero => rfl
  | succ m ih => simp only [reflectedInputs, ih]; ring

theorem reconstructed_input_count (m : Nat) : reconstructedInputs m = m * m := by
  induction m with
  | zero => rfl
  | succ m ih => simp only [reconstructedInputs, ih]; ring

-- Every eliminated batch input still needs a reconstruction and a visit.
theorem input_accounting (m : Nat) :
    directInputs m = reflectedInputs m + reconstructedInputs m := by
  rw [direct_input_count, reflected_input_count, reconstructed_input_count]
  ring

-- An explicit weighted model gives a strict reduction exactly when a saved
-- batch-input cost outweighs the corresponding reconstruction cost.
-- Actual timing additionally includes validation, allocation, hashing and I/O.
theorem weighted_reduction (m : Nat) (positive : 0 < m)
    (addition reconstruction : ℝ) (cheaper : reconstruction < addition) :
    (reflectedInputs m : ℝ) * addition + (reconstructedInputs m : ℝ) * reconstruction <
    (directInputs m : ℝ) * addition := by
  rw [input_accounting]
  push_cast
  have h : (0 : ℝ) < reconstructedInputs m := by
    rw [reconstructed_input_count]
    exact_mod_cast Nat.mul_pos positive positive
  nlinarith

end ReflectedPair

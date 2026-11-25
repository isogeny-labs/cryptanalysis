import FiberLift
import Mathlib.Tactic.Eval
import Mathlib.LinearAlgebra.Matrix.Rank

namespace M31TensorMinor
abbrev I := Fin 128
abbrev F := ZMod 2147483647
abbrev B := ZMod 2

def data : Array (Array Nat) := eval%
  (((include_str "tensor-minor.csv").splitOn "\n").tail.filterMap
    (fun line => ((line.splitOn ",").mapM String.toNat?).map List.toArray)).toArray

def minor : Matrix I I B := fun i j => (((data[i.val]!)[1]!).testBit j.val).toNat
def inverse : Matrix I I B := fun i j => (((data[i.val]!)[2]!).testBit j.val).toNat

def rhs (i j : I) : F :=
  let x : F := (512+i.val)*65536+j.val
  x^3+2*x+14

private theorem allPairs (a b : I → I → B)
    (h : (List.finRange 128).all (fun i => (List.finRange 128).all (fun j => decide (a i j = b i j)))) :
    ∀ i j, a i j = b i j := by
  intro i j
  have a := List.all_eq_true.mp h i (by simp)
  exact of_decide_eq_true (List.all_eq_true.mp a j (by simp))

theorem entries : ∀ i j : I, minor i j =
    (decide ((M31FiberLift.squares (fun _ : Unit => rhs i j) 29 ())^2 = rhs i j)).toNat := by
  apply allPairs
  native_decide

theorem lift (i j : I) : minor i j = 1 ↔ ∃ y : F, y^2 = rhs i j := by
  rw [entries]
  have h := M31FiberLift.lift_exact (fun _ : Unit => rhs i j) ()
  by_cases eq : (M31FiberLift.squares (fun _ : Unit => rhs i j) 29 ())^2 = rhs i j <;>
    simp [eq, ← h]

theorem identity_entries : ∀ i j : I, (minor * inverse) i j = (1 : Matrix I I B) i j := by
  apply allPairs
  native_decide

theorem inner_dimension {k : Nat} (left : Matrix I (Fin k) B) (right : Matrix (Fin k) I B)
    (factor : left * right = minor) : 128 ≤ k := by
  have identity : minor * inverse = 1 := Matrix.ext identity_entries
  calc
    128 = (1 : Matrix I I B).rank := by simp
    _ = (minor * inverse).rank := by rw [identity]
    _ ≤ minor.rank := Matrix.rank_mul_le_left _ _
    _ = (left * right).rank := by rw [factor]
    _ ≤ left.rank := Matrix.rank_mul_le_left _ _
    _ ≤ k := left.rank_le_card_width.trans_eq (Fintype.card_fin k)

def integerMinor : Matrix I I ℤ := fun i j => ((data[i.val]!)[1]!).testBit j.val |>.toNat

theorem integer_det_ne_zero : integerMinor.det ≠ 0 := by
  have reduced : integerMinor.map (fun x : ℤ => (x : B)) = minor := by
    ext i j
    simp [integerMinor, minor, Matrix.map_apply]
  have identity : minor * inverse = 1 := Matrix.ext identity_entries
  intro zero
  have h := Int.cast_det (R := B) integerMinor
  rw [zero, reduced, Int.cast_zero] at h
  have one := congrArg Matrix.det identity
  rw [Matrix.det_mul, ← h, zero_mul, Matrix.det_one] at one
  exact zero_ne_one one

theorem characteristic_zero_rank {K : Type*} [Field K] [CharZero K] :
    (integerMinor.map (fun x : ℤ => (x : K))).rank = 128 := by
  apply Matrix.rank_of_det_ne_zero
  rw [← Int.cast_det]
  exact_mod_cast integer_det_ne_zero

end M31TensorMinor

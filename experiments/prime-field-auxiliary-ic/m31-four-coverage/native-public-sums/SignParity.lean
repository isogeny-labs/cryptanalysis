import RectangleFree

namespace SignParity
open Matrix

abbrev P := Fin 64
abbrev L := Fin 68
abbrev Table := Matrix P L ℤ

def unsigned : Table := fun i j =>
  if (RectangleFree.points j).contains i.val then 1 else 0

def signed (flip : P → L → Bool) : Table := fun i j =>
  if flip i j then -unsigned i j else unsigned i j

/-- The off-diagonal Gram matrix with diagonal replaced by minus seven. -/
def shifted (H : Table) : Matrix P P ℤ := fun i j =>
  if i = j then -7 else (H * H.transpose) i j

def residual (H : Table) : Table := shifted H * H

private theorem sum_congr₂ {ι : Type*} (s : Finset ι) (a b : ι → ℤ)
    (h : ∀ i, a i ≡ b i [ZMOD 2]) : (∑ i ∈ s, a i) ≡ (∑ i ∈ s, b i) [ZMOD 2] := by
  classical
  induction s using Finset.induction_on with
  | empty => rfl
  | insert i s hi ih => simpa [hi] using (h i).add ih

theorem residual_parity (flip : P → L → Bool) (i : P) (j : L) :
    residual (signed flip) i j ≡ residual unsigned i j [ZMOD 2] := by
  have entry (x : P) (y : L) : signed flip x y ≡ unsigned x y [ZMOD 2] := by
    unfold signed unsigned
    split <;> split <;> decide
  have middle (x y : P) : shifted (signed flip) x y ≡ shifted unsigned x y [ZMOD 2] := by
    unfold shifted
    split
    · rfl
    · simpa only [Matrix.mul_apply, Matrix.transpose_apply] using
        sum_congr₂ Finset.univ _ _ (fun k => (entry x k).mul (entry y k))
  simpa only [residual, Matrix.mul_apply] using
    sum_congr₂ Finset.univ _ _ (fun k => (middle i k).mul (entry k j))

def oddCount (H : Table) : Nat :=
  (Finset.univ.filter (fun ij : P × L => residual H ij.1 ij.2 % 2 = 1)).card

private theorem unsigned_count : oddCount unsigned = 1792 := by native_decide

theorem signed_count (flip : P → L → Bool) : oddCount (signed flip) = 1792 := by
  rw [← unsigned_count]
  unfold oddCount
  apply congrArg Finset.card
  apply Finset.filter_congr
  intro ij _
  rw [show residual (signed flip) ij.1 ij.2 % 2 = residual unsigned ij.1 ij.2 % 2
      from residual_parity flip ij.1 ij.2]

#print axioms residual_parity
#print axioms signed_count
end SignParity

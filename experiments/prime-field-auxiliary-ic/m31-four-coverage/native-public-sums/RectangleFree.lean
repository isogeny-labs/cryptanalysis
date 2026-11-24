import Mathlib.Data.Sym.Sym2
import Mathlib.Tactic

namespace RectangleFree
open scoped Sym2

/-- The frozen affine-plane point IDs on each benchmark line, in generator order. -/
def lines : Array (List Nat) := #[
  [0, 8, 16, 24, 32, 40, 48, 56],
  [1, 9, 17, 25, 33, 41, 49, 57],
  [2, 10, 18, 26, 34, 42, 50, 58],
  [3, 11, 19, 27, 35, 43, 51, 59],
  [4, 12, 20, 28, 36, 44, 52, 60],
  [5, 13, 21, 29, 37, 45, 53, 61],
  [6, 14, 22, 30, 38, 46, 54, 62],
  [7, 15, 23, 31, 39, 47, 55, 63],
  [0, 9, 18, 27, 36, 45, 54, 63],
  [1, 8, 19, 26, 37, 44, 55, 62],
  [2, 11, 16, 25, 38, 47, 52, 61],
  [3, 10, 17, 24, 39, 46, 53, 60],
  [4, 13, 22, 31, 32, 41, 50, 59],
  [5, 12, 23, 30, 33, 40, 51, 58],
  [6, 15, 20, 29, 34, 43, 48, 57],
  [7, 14, 21, 28, 35, 42, 49, 56],
  [0, 10, 20, 30, 35, 41, 55, 61],
  [1, 11, 21, 31, 34, 40, 54, 60],
  [2, 8, 22, 28, 33, 43, 53, 63],
  [3, 9, 23, 29, 32, 42, 52, 62],
  [4, 14, 16, 26, 39, 45, 51, 57],
  [5, 15, 17, 27, 38, 44, 50, 56],
  [6, 12, 18, 24, 37, 47, 49, 59],
  [7, 13, 19, 25, 36, 46, 48, 58],
  [0, 11, 22, 29, 39, 44, 49, 58],
  [1, 10, 23, 28, 38, 45, 48, 59],
  [2, 9, 20, 31, 37, 46, 51, 56],
  [3, 8, 21, 30, 36, 47, 50, 57],
  [4, 15, 18, 25, 35, 40, 53, 62],
  [5, 14, 19, 24, 34, 41, 52, 63],
  [6, 13, 16, 27, 33, 42, 55, 60],
  [7, 12, 17, 26, 32, 43, 54, 61],
  [0, 12, 19, 31, 38, 42, 53, 57],
  [1, 13, 18, 30, 39, 43, 52, 56],
  [2, 14, 17, 29, 36, 40, 55, 59],
  [3, 15, 16, 28, 37, 41, 54, 58],
  [4, 8, 23, 27, 34, 46, 49, 61],
  [5, 9, 22, 26, 35, 47, 48, 60],
  [6, 10, 21, 25, 32, 44, 51, 63],
  [7, 11, 20, 24, 33, 45, 50, 62],
  [0, 13, 17, 28, 34, 47, 51, 62],
  [1, 12, 16, 29, 35, 46, 50, 63],
  [2, 15, 19, 30, 32, 45, 49, 60],
  [3, 14, 18, 31, 33, 44, 48, 61],
  [4, 9, 21, 24, 38, 43, 55, 58],
  [5, 8, 20, 25, 39, 42, 54, 59],
  [6, 11, 23, 26, 36, 41, 53, 56],
  [7, 10, 22, 27, 37, 40, 52, 57],
  [0, 14, 23, 25, 37, 43, 50, 60],
  [1, 15, 22, 24, 36, 42, 51, 61],
  [2, 12, 21, 27, 39, 41, 48, 62],
  [3, 13, 20, 26, 38, 40, 49, 63],
  [4, 10, 19, 29, 33, 47, 54, 56],
  [5, 11, 18, 28, 32, 46, 55, 57],
  [6, 8, 17, 31, 35, 45, 52, 58],
  [7, 9, 16, 30, 34, 44, 53, 59],
  [0, 15, 21, 26, 33, 46, 52, 59],
  [1, 14, 20, 27, 32, 47, 53, 58],
  [2, 13, 23, 24, 35, 44, 54, 57],
  [3, 12, 22, 25, 34, 45, 55, 56],
  [4, 11, 17, 30, 37, 42, 48, 63],
  [5, 10, 16, 31, 36, 43, 49, 62],
  [6, 9, 19, 28, 39, 40, 50, 61],
  [7, 8, 18, 29, 38, 41, 51, 60],
  [0, 1, 2, 3, 4, 5, 6, 7],
  [8, 9, 10, 11, 12, 13, 14, 15],
  [16, 17, 18, 19, 20, 21, 22, 23],
  [24, 25, 26, 27, 28, 29, 30, 31]
]

def points (i : Fin 68) := lines[i.val]'(by decide +revert)

theorem eight_distinct : ∀ i : Fin 68, (points i).length = 8 ∧ (points i).Nodup := by
  decide +kernel

theorem intersection_size : ∀ i j : Fin 68, i ≠ j →
    ((points i).filter (points j).contains).length ≤ 1 := by
  decide +kernel

private theorem short_list {x y : Nat} {l : List Nat}
    (h : l.length ≤ 1) (hx : x ∈ l) (hy : y ∈ l) : x = y := by
  cases l with
  | nil => simp at hx
  | cons a t =>
    cases t with
    | nil => simpa using (show x = a from by simpa using hx).trans
                (show y = a from by simpa using hy).symm
    | cons b t => simp at h

theorem rectangle {i j : Fin 68} {x y : Nat}
    (a : x ∈ points i) (b : y ∈ points j)
    (c : x ∈ points j) (d : y ∈ points i) : x = y ∨ i = j := by
  by_cases e : i = j
  · exact Or.inr e
  · exact Or.inl (short_list (intersection_size i j e)
      (by simpa using And.intro a c) (by simpa using And.intro d b))

/-- A cell pair is determined by its unordered point IDs and unordered line IDs. -/
theorem pair_unique {i j k l : Fin 68} {x y z w : Nat}
    (a : x ∈ points i) (b : y ∈ points j) (c : z ∈ points k) (d : w ∈ points l)
    (hx : s(x,y) = s(z,w)) (hi : s(i,j) = s(k,l)) :
    s((x,i),(y,j)) = s((z,k),(w,l)) := by
  rcases Sym2.eq_iff.mp hx with ⟨rfl,rfl⟩ | ⟨rfl,rfl⟩ <;>
    rcases Sym2.eq_iff.mp hi with ⟨rfl,rfl⟩ | ⟨rfl,rfl⟩ <;>
    apply Sym2.eq_iff.mpr <;> first | solve | simp | grind [rectangle]

#print axioms pair_unique
end RectangleFree

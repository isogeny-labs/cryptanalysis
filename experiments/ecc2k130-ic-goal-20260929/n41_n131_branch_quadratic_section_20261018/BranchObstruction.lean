import Std

namespace BranchObstruction

def sumList {V : Type} [Zero V] [Add V] : List V → V
  | [] => 0
  | x :: xs => x + sumList xs

theorem map_sum {V T : Type} [Zero V] [Add V] [Zero T] [Add T]
    (f : V → T) (hzero : f 0 = 0)
    (hadd : ∀ x y, f (x+y) = f x + f y)
    (xs : List V) : sumList (xs.map f) = f (sumList xs) := by
  induction xs with
  | nil => simpa [sumList] using hzero.symm
  | cons x xs ih => simp [sumList, ih, hadd]

/-- A feature dependency and a branch-invariant output parity exclude
every additive map from feature vectors to that output parity. -/
theorem no_branch_fit
    {I V W T : Type} [Zero V] [Add V] [Zero W] [Add W] [Zero T] [Add T]
    (indices : List I) (feature : I → V) (root delta choose : I → W)
    (parity : W → T)
    (parity_add : ∀ x y, parity (x+y) = parity x + parity y)
    (root_add_zero : ∀ x : W, x+0=x)
    (parity_add_zero : ∀ x : T, x+0=x)
    (branch : ∀ i, choose i = 0 ∨ choose i = delta i)
    (kill : ∀ i, parity (delta i) = 0)
    (feature_dependency : sumList (indices.map feature) = 0)
    (nonzero_parity : sumList (indices.map (fun i => parity (root i))) ≠ 0) :
    ¬ ∃ fit : V → T,
        fit 0 = 0 ∧
        (∀ x y, fit (x+y) = fit x + fit y) ∧
        (∀ i, fit (feature i) = parity (root i + choose i)) := by
  intro hfit
  obtain ⟨fit, fit_zero, fit_add, agreement⟩ := hfit
  have hchosen (i : I) : parity (root i + choose i) = parity (root i) := by
    rcases branch i with hz | hd
    · rw [hz, root_add_zero]
    · rw [hd, parity_add, kill i, parity_add_zero]
  have hfit_sum : sumList (indices.map (fun i => fit (feature i))) = 0 := by
    have hcomp : (indices.map feature).map fit =
        indices.map (fun i => fit (feature i)) := by simp [List.map_map]
    rw [← hcomp]
    rw [map_sum fit fit_zero fit_add, feature_dependency, fit_zero]
  have hmap : indices.map (fun i => fit (feature i)) =
              indices.map (fun i => parity (root i)) := by
    apply List.map_congr_left
    intro i _
    rw [agreement, hchosen]
  rw [hmap] at hfit_sum
  exact nonzero_parity hfit_sum

#print axioms BranchObstruction.map_sum
#print axioms BranchObstruction.no_branch_fit

end BranchObstruction

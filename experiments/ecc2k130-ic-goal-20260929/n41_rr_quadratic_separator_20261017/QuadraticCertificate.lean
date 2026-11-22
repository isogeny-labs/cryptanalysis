import Std

namespace QuadraticCertificate

/-- A Boolean polynomial with linear and squarefree quadratic terms and no
constant term. The lists are the selected feature indices of a certificate. -/
def evaluate {α : Type} (linear : List α) (quadratic : List (α × α))
    (bits : α → Bool) : Bool :=
  Bool.xor
    (linear.foldl (fun acc i => Bool.xor acc (bits i)) false)
    (quadratic.foldl (fun acc ij => Bool.xor acc (bits ij.1 && bits ij.2)) false)

private theorem fold_keep {β : Type} (xs : List β) (value : Bool) :
    xs.foldl (fun acc _ => acc) value = value := by
  induction xs with
  | nil => rfl
  | cons _ tail ih =>
      simpa only [List.foldl_cons] using ih

/-- A no-constant quadratic certificate evaluates to zero on the zero word. -/
theorem evaluate_zero {α : Type} (linear : List α)
    (quadratic : List (α × α)) :
    evaluate linear quadratic (fun _ => false) = false := by
  simp [evaluate, fold_keep]

/-- If one quadratic certificate equals one on every word in a family, the
family cannot contain the zero word. -/
theorem excludes_zero {α : Type} (linear : List α)
    (quadratic : List (α × α)) (family : List (α → Bool))
    (hall : ∀ bits ∈ family, evaluate linear quadratic bits = true) :
    (fun _ => false) ∉ family := by
  intro hmem
  have h := hall (fun _ => false) hmem
  rw [evaluate_zero] at h
  cases h

/-- A parity of selected input bits, represented by the input indices. -/
def linearForm {α : Type} (indices : List α) (bits : α → Bool) : Bool :=
  indices.foldl (fun acc i => Bool.xor acc (bits i)) false

/-- An XOR circuit whose nonlinear gates multiply pairs of binary-linear forms. -/
def factoredEvaluate {α : Type} (linear : List α)
    (products : List (List α × List α)) (bits : α → Bool) : Bool :=
  products.foldl
    (fun acc pair => Bool.xor acc
      (linearForm pair.1 bits && linearForm pair.2 bits))
    (linearForm linear bits)

theorem linearForm_zero {α : Type} (indices : List α) :
    linearForm indices (fun _ => false) = false := by
  simp [linearForm, fold_keep]

/-- The factored circuit rejects a zero word when it outputs one on a family. -/
theorem factored_excludes_zero {α : Type} (linear : List α)
    (products : List (List α × List α)) (family : List (α → Bool))
    (hall : ∀ bits ∈ family,
      factoredEvaluate linear products bits = true) :
    (fun _ => false) ∉ family := by
  have hzero : factoredEvaluate linear products (fun _ => false) = false := by
    simp [factoredEvaluate, linearForm_zero, fold_keep]
  intro hmem
  have h := hall (fun _ => false) hmem
  rw [hzero] at h
  cases h

#print axioms evaluate_zero
#print axioms excludes_zero
#print axioms linearForm_zero
#print axioms factored_excludes_zero
end QuadraticCertificate

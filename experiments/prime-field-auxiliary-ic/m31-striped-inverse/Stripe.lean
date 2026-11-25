import Mathlib.Algebra.Field.Basic

namespace M31StripedInverse
variable {F : Type*} [Field F] {lanes : Nat}

/-- Each column carries its own prefix product. On the reverse pass the incoming
state is its inverse after the current row. Return the outgoing state and row. -/
def walk (acc : Fin lanes → F) : List (Fin lanes → F) → (Fin lanes → F) × List (Fin lanes → F)
  | [] => (fun j => (acc j)⁻¹, [])
  | x :: xs =>
    let (r, tail) := walk (fun j => acc j * x j) xs
    (fun j => r j * x j, (fun j => acc j * r j) :: tail)

theorem walk_correct (rows : List (Fin lanes → F)) (acc : Fin lanes → F)
    (hp : ∀ j, acc j ≠ 0) (hx : ∀ x ∈ rows, ∀ j, x j ≠ 0) :
    walk acc rows = (fun j => (acc j)⁻¹, rows.map (fun x j => (x j)⁻¹)) := by
  induction rows generalizing acc with
  | nil => rfl
  | cons x xs ih =>
    have hn := hx x List.mem_cons_self
    rw [walk, ih _ (fun j => mul_ne_zero (hp j) (hn j))
      (fun y hy => hx y (List.mem_cons_of_mem _ hy))]
    simp [mul_inv_rev, mul_comm, hn]
    funext j
    rw [mul_left_comm, mul_inv_cancel₀ (hp j), mul_one]

end M31StripedInverse

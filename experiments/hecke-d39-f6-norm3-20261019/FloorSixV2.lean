module

public import Mathlib.Tactic.Linarith
public import Mathlib.Data.Fin.Basic

/-! Exact floor vectors from D39/f6 SHA-256 `a5659b83ff0418d2d99fc06d3125f7753b9fe4cff5c413554f1d28cad4b54f94`. -/

namespace D39Floor

public def pair0 (j : Fin 64) : ℚ :=
  if j.val = 15 then -1 else
  if j.val = 21 then 1 else
  if j.val = 30 then 1 else
  if j.val = 38 then -1 else
  if j.val = 45 then -1 else
  if j.val = 61 then 1 else
  0

public def pair1 (j : Fin 64) : ℚ :=
  if j.val = 3 then -1 else
  if j.val = 5 then 1 else
  if j.val = 20 then -1 else
  if j.val = 26 then 1 else
  if j.val = 40 then 1 else
  if j.val = 44 then -1 else
  0

public def pair2 (j : Fin 64) : ℚ :=
  if j.val = 33 then 1 else
  if j.val = 39 then -1 else
  if j.val = 41 then -1 else
  if j.val = 50 then 1 else
  if j.val = 54 then 1 else
  if j.val = 63 then -1 else
  0

public def pair3 (j : Fin 64) : ℚ :=
  if j.val = 2 then -1 else
  if j.val = 29 then 1 else
  if j.val = 31 then -1 else
  if j.val = 46 then 1 else
  if j.val = 49 then 1 else
  if j.val = 55 then -1 else
  0

public def cycle0 (j : Fin 64) : ℚ :=
  if j.val = 2 then 1 else
  if j.val = 3 then -1 else
  if j.val = 5 then -1 else
  if j.val = 20 then -1 else
  if j.val = 26 then -1 else
  if j.val = 29 then 1 else
  if j.val = 31 then 1 else
  if j.val = 40 then -1 else
  if j.val = 44 then -1 else
  if j.val = 46 then 1 else
  if j.val = 49 then 1 else
  if j.val = 55 then 1 else
  0

public def cycle1 (j : Fin 64) : ℚ :=
  if j.val = 15 then 1 else
  if j.val = 21 then 1 else
  if j.val = 30 then 1 else
  if j.val = 33 then -1 else
  if j.val = 38 then 1 else
  if j.val = 39 then -1 else
  if j.val = 41 then -1 else
  if j.val = 45 then 1 else
  if j.val = 50 then -1 else
  if j.val = 54 then -1 else
  if j.val = 61 then 1 else
  if j.val = 63 then -1 else
  0

public def combination (a0 a1 a2 a3 b0 b1 : ℚ) (j : Fin 64) : ℚ :=
  a0 * pair0 j + a1 * pair1 j + a2 * pair2 j + a3 * pair3 j +
  b0 * cycle0 j + b1 * cycle1 j

/-- The four degree-3 pair-difference vectors and two degree-2 cycle
vectors are linearly independent over `ℚ` on all 64 saved columns. -/
public theorem six_floor_vectors_independent (a0 a1 a2 a3 b0 b1 : ℚ)
    (h : ∀ j : Fin 64, combination a0 a1 a2 a3 b0 b1 j = 0) :
    a0 = 0 ∧ a1 = 0 ∧ a2 = 0 ∧ a3 = 0 ∧ b0 = 0 ∧ b1 = 0 := by
  have h3 : -a1 + -b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨3, by decide⟩ : Fin 64)
  have h5 : a1 + -b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨5, by decide⟩ : Fin 64)
  have h21 : a0 + b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨21, by decide⟩ : Fin 64)
  have h15 : -a0 + b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨15, by decide⟩ : Fin 64)
  have h33 : a2 + -b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨33, by decide⟩ : Fin 64)
  have h2 : -a3 + b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨2, by decide⟩ : Fin 64)
  constructor
  · linarith
  constructor
  · linarith
  constructor
  · linarith
  constructor
  · linarith
  constructor
  · linarith
  · linarith

end D39Floor

#print axioms D39Floor.six_floor_vectors_independent

module

public import Mathlib.Tactic.Linarith
public import Mathlib.Data.Fin.Basic

/-! Ten exact D183/f6 floor vectors from `floor_D183.json` SHA-256 `0c5af2a6e58b909f361828045f58d443cf7c00efe9da1aacbf37a87d99869fc1`. -/

namespace D183Floor

public def pair0 (j : Fin 128) : ℚ :=
  if j.val = 3 then -1 else
  if j.val = 36 then 1 else
  if j.val = 71 then -1 else
  if j.val = 89 then 1 else
  if j.val = 92 then -1 else
  if j.val = 96 then 1 else
  0

public def pair1 (j : Fin 128) : ℚ :=
  if j.val = 39 then 1 else
  if j.val = 63 then 1 else
  if j.val = 65 then 1 else
  if j.val = 81 then -1 else
  if j.val = 100 then -1 else
  if j.val = 113 then -1 else
  0

public def pair2 (j : Fin 128) : ℚ :=
  if j.val = 29 then 1 else
  if j.val = 43 then -1 else
  if j.val = 44 then -1 else
  if j.val = 54 then 1 else
  if j.val = 60 then -1 else
  if j.val = 111 then 1 else
  0

public def pair3 (j : Fin 128) : ℚ :=
  if j.val = 0 then 1 else
  if j.val = 13 then -1 else
  if j.val = 37 then -1 else
  if j.val = 66 then 1 else
  if j.val = 90 then 1 else
  if j.val = 117 then -1 else
  0

public def pair4 (j : Fin 128) : ℚ :=
  if j.val = 24 then 1 else
  if j.val = 32 then 1 else
  if j.val = 51 then -1 else
  if j.val = 56 then -1 else
  if j.val = 62 then 1 else
  if j.val = 121 then -1 else
  0

public def pair5 (j : Fin 128) : ℚ :=
  if j.val = 28 then 1 else
  if j.val = 76 then 1 else
  if j.val = 107 then -1 else
  if j.val = 115 then -1 else
  if j.val = 123 then -1 else
  if j.val = 126 then 1 else
  0

public def pair6 (j : Fin 128) : ℚ :=
  if j.val = 2 then 1 else
  if j.val = 7 then 1 else
  if j.val = 19 then -1 else
  if j.val = 47 then -1 else
  if j.val = 49 then -1 else
  if j.val = 94 then 1 else
  0

public def pair7 (j : Fin 128) : ℚ :=
  if j.val = 6 then 1 else
  if j.val = 16 then -1 else
  if j.val = 41 then 1 else
  if j.val = 42 then -1 else
  if j.val = 86 then -1 else
  if j.val = 105 then 1 else
  0

public def cycle0 (j : Fin 128) : ℚ :=
  if j.val = 0 then 1 else
  if j.val = 2 then -1 else
  if j.val = 6 then -1 else
  if j.val = 7 then -1 else
  if j.val = 13 then 1 else
  if j.val = 16 then -1 else
  if j.val = 19 then -1 else
  if j.val = 28 then 1 else
  if j.val = 37 then 1 else
  if j.val = 41 then -1 else
  if j.val = 42 then -1 else
  if j.val = 47 then -1 else
  if j.val = 49 then -1 else
  if j.val = 66 then 1 else
  if j.val = 76 then 1 else
  if j.val = 86 then -1 else
  if j.val = 90 then 1 else
  if j.val = 94 then -1 else
  if j.val = 105 then -1 else
  if j.val = 107 then 1 else
  if j.val = 115 then 1 else
  if j.val = 117 then 1 else
  if j.val = 123 then 1 else
  if j.val = 126 then 1 else
  0

public def cycle1 (j : Fin 128) : ℚ :=
  if j.val = 3 then -1 else
  if j.val = 24 then 1 else
  if j.val = 29 then 1 else
  if j.val = 32 then 1 else
  if j.val = 36 then -1 else
  if j.val = 39 then -1 else
  if j.val = 43 then 1 else
  if j.val = 44 then 1 else
  if j.val = 51 then 1 else
  if j.val = 54 then 1 else
  if j.val = 56 then 1 else
  if j.val = 60 then 1 else
  if j.val = 62 then 1 else
  if j.val = 63 then -1 else
  if j.val = 65 then -1 else
  if j.val = 71 then -1 else
  if j.val = 81 then -1 else
  if j.val = 89 then -1 else
  if j.val = 92 then -1 else
  if j.val = 96 then -1 else
  if j.val = 100 then -1 else
  if j.val = 111 then 1 else
  if j.val = 113 then -1 else
  if j.val = 121 then 1 else
  0

public def combination (a0 a1 a2 a3 a4 a5 a6 a7 b0 b1 : ℚ) (j : Fin 128) : ℚ :=
  a0 * pair0 j + a1 * pair1 j + a2 * pair2 j + a3 * pair3 j + a4 * pair4 j + a5 * pair5 j + a6 * pair6 j + a7 * pair7 j +
  b0 * cycle0 j + b1 * cycle1 j

/-- Eight degree-3 pair differences and two degree-2 signed cycle vectors
are linearly independent over `ℚ` on the 128 saved columns. -/
public theorem ten_floor_vectors_independent (a0 a1 a2 a3 a4 a5 a6 a7 b0 b1 : ℚ)
    (h : ∀ j : Fin 128, combination a0 a1 a2 a3 a4 a5 a6 a7 b0 b1 j = 0) :
    a0 = 0 ∧ a1 = 0 ∧ a2 = 0 ∧ a3 = 0 ∧ a4 = 0 ∧ a5 = 0 ∧ a6 = 0 ∧ a7 = 0 ∧ b0 = 0 ∧ b1 = 0 := by
  have h0 : a3 + b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨0, by decide⟩ : Fin 128)
  have h13 : -a3 + b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨13, by decide⟩ : Fin 128)
  have h3 : -a0 + -b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨3, by decide⟩ : Fin 128)
  have h36 : a0 + -b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨36, by decide⟩ : Fin 128)
  have h39 : a1 + -b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨39, by decide⟩ : Fin 128)
  have h29 : a2 + b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨29, by decide⟩ : Fin 128)
  have h24 : a4 + b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨24, by decide⟩ : Fin 128)
  have h28 : a5 + b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨28, by decide⟩ : Fin 128)
  have h2 : a6 + -b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨2, by decide⟩ : Fin 128)
  have h6 : a7 + -b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, pair4, pair5, pair6, pair7, cycle0, cycle1] using
      h (⟨6, by decide⟩ : Fin 128)
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
  constructor
  · linarith
  constructor
  · linarith
  constructor
  · linarith
  constructor
  · linarith
  · linarith

end D183Floor

#print axioms D183Floor.ten_floor_vectors_independent

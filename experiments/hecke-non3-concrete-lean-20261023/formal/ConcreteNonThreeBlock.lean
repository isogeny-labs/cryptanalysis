module

public import Mathlib.Tactic.Linarith
public import Mathlib.Tactic.FinCases
public import Mathlib.Data.Rat.Init

/-! Exact 30 by 30 conductor-2 nonfloor block from the sealed D=-227 matrix.
    Source SHA-256: 8ef0c2c318bc28337d3740561646cb005fddf769dd56fe7bb28d7f060fbda6ad -/

namespace ConcreteNonThreeBlock

public def blockRow (x : Fin 30 → ℚ) (i : Fin 30) : ℚ :=
  match i.val with
  | 0 => x 0 + x 1 + x 22
  | 1 => x 0 + x 1 + x 28
  | 2 => x 2 + x 10 + x 14
  | 3 => x 3 + x 13 + x 24
  | 4 => x 4 + x 8 + x 21
  | 5 => x 5 + x 7 + x 15
  | 6 => x 6 + x 8 + x 25
  | 7 => x 5 + x 7 + x 9
  | 8 => x 4 + x 6 + x 8
  | 9 => x 7 + x 9 + x 18
  | 10 => x 2 + x 10 + x 19
  | 11 => x 11 + x 13 + x 26
  | 12 => x 12 + x 17 + x 27
  | 13 => x 3 + x 11 + x 13
  | 14 => x 2 + x 14 + x 20
  | 15 => x 5 + x 15 + x 18
  | 16 => x 16 + x 22 + x 28
  | 17 => x 12 + x 17 + x 23
  | 18 => x 9 + x 15 + x 18
  | 19 => x 10 + x 19 + x 20
  | 20 => x 14 + x 19 + x 20
  | 21 => x 4 + x 21 + x 25
  | 22 => x 0 + x 16 + x 22
  | 23 => x 17 + x 23 + x 29
  | 24 => x 3 + x 24 + x 26
  | 25 => x 6 + x 21 + x 25
  | 26 => x 11 + x 24 + x 26
  | 27 => x 12 + x 27 + x 29
  | 28 => x 1 + x 16 + x 28
  | 29 => x 23 + x 27 + x 29
  | _ => 0

private theorem fiveCycle (a b c d e : ℚ)
    (h0 : a + b + e = 0) (h1 : b + a + c = 0)
    (h2 : c + b + d = 0) (h3 : d + c + e = 0)
    (h4 : e + d + a = 0) :
    a = 0 ∧ b = 0 ∧ c = 0 ∧ d = 0 ∧ e = 0 := by
  have ha : a = 0 := by linarith only [h0, h1, h2, h3, h4]
  have hb : b = 0 := by linarith only [h0, h1, h2, h3, h4]
  have hc : c = 0 := by linarith only [h0, h1, h2, h3, h4]
  have hd : d = 0 := by linarith only [h0, h1, h2, h3, h4]
  have he : e = 0 := by linarith only [h0, h1, h2, h3, h4]
  exact ⟨ha, hb, hc, hd, he⟩

public theorem blockRow_kernel_zero (x : Fin 30 → ℚ)
    (h : ∀ i, blockRow x i = 0) : ∀ i, x i = 0 := by
  have cycle0 := fiveCycle (x 0) (x 1) (x 28) (x 16) (x 22)
    (by have hx := h (⟨0, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨1, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨28, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨16, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨22, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
  rcases cycle0 with ⟨z0, z1, z28, z16, z22⟩
  have cycle1 := fiveCycle (x 2) (x 10) (x 19) (x 20) (x 14)
    (by have hx := h (⟨2, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨10, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨19, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨20, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨14, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
  rcases cycle1 with ⟨z2, z10, z19, z20, z14⟩
  have cycle2 := fiveCycle (x 3) (x 13) (x 11) (x 26) (x 24)
    (by have hx := h (⟨3, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨13, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨11, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨26, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨24, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
  rcases cycle2 with ⟨z3, z13, z11, z26, z24⟩
  have cycle3 := fiveCycle (x 4) (x 8) (x 6) (x 25) (x 21)
    (by have hx := h (⟨4, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨8, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨6, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨25, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨21, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
  rcases cycle3 with ⟨z4, z8, z6, z25, z21⟩
  have cycle4 := fiveCycle (x 5) (x 7) (x 9) (x 18) (x 15)
    (by have hx := h (⟨5, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨7, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨9, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨18, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨15, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
  rcases cycle4 with ⟨z5, z7, z9, z18, z15⟩
  have cycle5 := fiveCycle (x 12) (x 17) (x 23) (x 29) (x 27)
    (by have hx := h (⟨12, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨17, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨23, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨29, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
    (by have hx := h (⟨27, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])
  rcases cycle5 with ⟨z12, z17, z23, z29, z27⟩
  intro i
  have hcases : i.val = 0 ∨ i.val = 1 ∨ i.val = 2 ∨ i.val = 3 ∨ i.val = 4 ∨ i.val = 5 ∨ i.val = 6 ∨ i.val = 7 ∨ i.val = 8 ∨ i.val = 9 ∨ i.val = 10 ∨ i.val = 11 ∨ i.val = 12 ∨ i.val = 13 ∨ i.val = 14 ∨ i.val = 15 ∨ i.val = 16 ∨ i.val = 17 ∨ i.val = 18 ∨ i.val = 19 ∨ i.val = 20 ∨ i.val = 21 ∨ i.val = 22 ∨ i.val = 23 ∨ i.val = 24 ∨ i.val = 25 ∨ i.val = 26 ∨ i.val = 27 ∨ i.val = 28 ∨ i.val = 29 := by omega
  rcases hcases with h0 | h1 | h2 | h3 | h4 | h5 | h6 | h7 | h8 | h9 | h10 | h11 | h12 | h13 | h14 | h15 | h16 | h17 | h18 | h19 | h20 | h21 | h22 | h23 | h24 | h25 | h26 | h27 | h28 | h29
  · have hi : i = (0 : Fin 30) := Fin.ext h0
    simpa [hi] using z0
  · have hi : i = (1 : Fin 30) := Fin.ext h1
    simpa [hi] using z1
  · have hi : i = (2 : Fin 30) := Fin.ext h2
    simpa [hi] using z2
  · have hi : i = (3 : Fin 30) := Fin.ext h3
    simpa [hi] using z3
  · have hi : i = (4 : Fin 30) := Fin.ext h4
    simpa [hi] using z4
  · have hi : i = (5 : Fin 30) := Fin.ext h5
    simpa [hi] using z5
  · have hi : i = (6 : Fin 30) := Fin.ext h6
    simpa [hi] using z6
  · have hi : i = (7 : Fin 30) := Fin.ext h7
    simpa [hi] using z7
  · have hi : i = (8 : Fin 30) := Fin.ext h8
    simpa [hi] using z8
  · have hi : i = (9 : Fin 30) := Fin.ext h9
    simpa [hi] using z9
  · have hi : i = (10 : Fin 30) := Fin.ext h10
    simpa [hi] using z10
  · have hi : i = (11 : Fin 30) := Fin.ext h11
    simpa [hi] using z11
  · have hi : i = (12 : Fin 30) := Fin.ext h12
    simpa [hi] using z12
  · have hi : i = (13 : Fin 30) := Fin.ext h13
    simpa [hi] using z13
  · have hi : i = (14 : Fin 30) := Fin.ext h14
    simpa [hi] using z14
  · have hi : i = (15 : Fin 30) := Fin.ext h15
    simpa [hi] using z15
  · have hi : i = (16 : Fin 30) := Fin.ext h16
    simpa [hi] using z16
  · have hi : i = (17 : Fin 30) := Fin.ext h17
    simpa [hi] using z17
  · have hi : i = (18 : Fin 30) := Fin.ext h18
    simpa [hi] using z18
  · have hi : i = (19 : Fin 30) := Fin.ext h19
    simpa [hi] using z19
  · have hi : i = (20 : Fin 30) := Fin.ext h20
    simpa [hi] using z20
  · have hi : i = (21 : Fin 30) := Fin.ext h21
    simpa [hi] using z21
  · have hi : i = (22 : Fin 30) := Fin.ext h22
    simpa [hi] using z22
  · have hi : i = (23 : Fin 30) := Fin.ext h23
    simpa [hi] using z23
  · have hi : i = (24 : Fin 30) := Fin.ext h24
    simpa [hi] using z24
  · have hi : i = (25 : Fin 30) := Fin.ext h25
    simpa [hi] using z25
  · have hi : i = (26 : Fin 30) := Fin.ext h26
    simpa [hi] using z26
  · have hi : i = (27 : Fin 30) := Fin.ext h27
    simpa [hi] using z27
  · have hi : i = (28 : Fin 30) := Fin.ext h28
    simpa [hi] using z28
  · have hi : i = (29 : Fin 30) := Fin.ext h29
    simpa [hi] using z29

end ConcreteNonThreeBlock

#print axioms ConcreteNonThreeBlock.blockRow_kernel_zero

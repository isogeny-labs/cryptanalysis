module

public import Mathlib.Tactic.Ring
public import Mathlib.Algebra.Ring.Rat

/-! Four disjoint signed floor certificates have unique coefficients.
The concrete 140-by-168 row matrix and its rank receipt are checked in Sage/Python;
they are not yet encoded as Lean definitions. -/

namespace FloorKernel

public theorem separating_coordinates {n : ℕ}
    (v0 v1 v2 v3 : Fin n → ℚ) (w0 w1 w2 w3 : Fin n)
    (h00 : v0 w0 ≠ 0) (h11 : v1 w1 ≠ 0)
    (h22 : v2 w2 ≠ 0) (h33 : v3 w3 ≠ 0)
    (h10 : v1 w0 = 0) (h20 : v2 w0 = 0) (h30 : v3 w0 = 0)
    (h01 : v0 w1 = 0) (h21 : v2 w1 = 0) (h31 : v3 w1 = 0)
    (h02 : v0 w2 = 0) (h12 : v1 w2 = 0) (h32 : v3 w2 = 0)
    (h03 : v0 w3 = 0) (h13 : v1 w3 = 0) (h23 : v2 w3 = 0)
    (a0 a1 a2 a3 : ℚ)
    (hcomb : ∀ x, a0 * v0 x + a1 * v1 x + a2 * v2 x + a3 * v3 x = 0) :
    a0 = 0 ∧ a1 = 0 ∧ a2 = 0 ∧ a3 = 0 := by
  have h0 := hcomb w0
  have h1 := hcomb w1
  have h2 := hcomb w2
  have h3 := hcomb w3
  simp [h10, h20, h30] at h0
  simp [h01, h21, h31] at h1
  simp [h02, h12, h32] at h2
  simp [h03, h13, h23] at h3
  exact ⟨h0.resolve_right h00,
         h1.resolve_right h11,
         h2.resolve_right h22,
         h3.resolve_right h33⟩

end FloorKernel

#print axioms FloorKernel.separating_coordinates

namespace FloorKernel

/-! The four concrete 168-column floor vectors, generated from floor_structure.json. -/

public def cert0 (j : Fin 168) : ℚ :=
  if j.val = 14 then -1 else
  if j.val = 32 then 1 else
  if j.val = 40 then -1 else
  if j.val = 48 then -1 else
  if j.val = 51 then 1 else
  if j.val = 63 then -1 else
  if j.val = 68 then 1 else
  if j.val = 73 then -1 else
  if j.val = 92 then -1 else
  if j.val = 122 then -1 else
  if j.val = 127 then 1 else
  if j.val = 135 then 1 else
  if j.val = 140 then 1 else
  if j.val = 143 then 1 else
  0

public def cert1 (j : Fin 168) : ℚ :=
  if j.val = 0 then -1 else
  if j.val = 3 then -1 else
  if j.val = 21 then 1 else
  if j.val = 29 then 1 else
  if j.val = 47 then -1 else
  if j.val = 50 then -1 else
  if j.val = 57 then 1 else
  if j.val = 62 then -1 else
  if j.val = 70 then -1 else
  if j.val = 81 then 1 else
  if j.val = 90 then 1 else
  if j.val = 112 then 1 else
  if j.val = 149 then 1 else
  if j.val = 166 then -1 else
  0

public def cert2 (j : Fin 168) : ℚ :=
  if j.val = 2 then -1 else
  if j.val = 24 then 1 else
  if j.val = 25 then 1 else
  if j.val = 38 then -1 else
  if j.val = 39 then 1 else
  if j.val = 53 then -1 else
  if j.val = 54 then 1 else
  if j.val = 61 then -1 else
  if j.val = 98 then -1 else
  if j.val = 118 then 1 else
  if j.val = 129 then 1 else
  if j.val = 131 then -1 else
  if j.val = 146 then 1 else
  if j.val = 155 then -1 else
  0

public def cert3 (j : Fin 168) : ℚ :=
  if j.val = 8 then -1 else
  if j.val = 10 then 1 else
  if j.val = 11 then -1 else
  if j.val = 17 then 1 else
  if j.val = 23 then 1 else
  if j.val = 30 then -1 else
  if j.val = 64 then 1 else
  if j.val = 74 then 1 else
  if j.val = 99 then -1 else
  if j.val = 104 then 1 else
  if j.val = 119 then -1 else
  if j.val = 138 then -1 else
  if j.val = 142 then -1 else
  if j.val = 162 then 1 else
  0

public theorem concrete_certificates_independent
    (a0 a1 a2 a3 : ℚ)
    (hcomb : ∀ x : Fin 168,
      a0 * cert0 x + a1 * cert1 x + a2 * cert2 x + a3 * cert3 x = 0) :
    a0 = 0 ∧ a1 = 0 ∧ a2 = 0 ∧ a3 = 0 := by
  exact separating_coordinates cert0 cert1 cert2 cert3
    ⟨14, by decide⟩ ⟨0, by decide⟩ ⟨2, by decide⟩ ⟨8, by decide⟩
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    (by norm_num [cert0, cert1, cert2, cert3])
    a0 a1 a2 a3 hcomb

end FloorKernel

#print axioms FloorKernel.concrete_certificates_independent

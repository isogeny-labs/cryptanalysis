import Init

/-!
Arithmetic layer for the reduced-input contracts of `ca_addmod` and
`ca_submod` in `include/cryptanalysis/ca_modarith.h`. These Nat definitions
spell out unsigned 64-bit wrapping with `% (2^64)`. SAW separately checks
the actual compiled C against the independent Cryptol specifications.
The Lean declarations do not establish a C-to-Lean compiler refinement.
-/

namespace PqcAssay

def cAdd64 (a b m : Nat) : Nat :=
  let raw := a + b
  let s := raw % (2 ^ 64)
  if s < a || s >= m then (s + 2 ^ 64 - m) % (2 ^ 64) else s

def cSub64 (a b m : Nat) : Nat :=
  if a >= b then a - b else (a + (m - b)) % (2 ^ 64)

private theorem mod_once (x m : Nat) (_hm : 0 < m) (hx : x < 2 * m) :
    x % m = if x < m then x else x - m := by
  split
  · exact Nat.mod_eq_of_lt ‹x < m›
  · have h : x ≥ m := by omega
    rw [Nat.mod_eq_sub_mod h, Nat.mod_eq_of_lt (by omega)]

private theorem modulo_add_unit (x U : Nat) (_hU : 0 < U) (hx : x < U) :
    (U + x) % U = x := by
  simp [Nat.mod_eq_of_lt hx]

theorem cAdd64_correct (a b m : Nat)
    (hm : 0 < m) (hmU : m < 2 ^ 64)
    (ha : a < m) (hb : b < m) :
    cAdd64 a b m = (a + b) % m := by
  let U := 2 ^ 64
  have hU : 0 < U := by decide
  have hraw : a + b < 2 * m := by omega
  rw [mod_once (a + b) m hm hraw]
  dsimp [cAdd64, U]
  by_cases hover : a + b < U
  · have hs : (a + b) % U = a + b := Nat.mod_eq_of_lt hover
    rw [hs]
    have hcarry : ¬ a + b < a := by omega
    simp only [hcarry, Bool.false_or, decide_false]
    by_cases hred : a + b < m
    · have : ¬ a + b ≥ m := by omega
      simp [this, hred]
    · have hge : a + b ≥ m := by omega
      have hsmall : a + b - m < U := by omega
      have heq : a + b + U - m = U + (a + b - m) := by omega
      simp [hge, hred]
      calc
        (a + b + U - m) % U = (U + (a + b - m)) % U := by rw [heq]
        _ = a + b - m := modulo_add_unit _ U hU hsmall
  · have hge : a + b ≥ U := by omega
    have hlt2 : a + b < 2 * U := by omega
    have hs : (a + b) % U = a + b - U := by
      rw [Nat.mod_eq_sub_mod hge, Nat.mod_eq_of_lt (by omega)]
    rw [hs]
    have hcarry : a + b - U < a := by omega
    have hred : ¬ a + b < m := by omega
    have hsmall : a + b - m < U := by omega
    have heq : (a + b - U) + U - m = a + b - m := by omega
    simp [hcarry, hred]
    calc
      (a + b - U + U - m) % U = (a + b - m) % U := by rw [heq]
      _ = a + b - m := Nat.mod_eq_of_lt hsmall

theorem cSub64_correct (a b m : Nat)
    (hm : 0 < m) (hmU : m < 2 ^ 64)
    (ha : a < m) (hb : b < m) :
    cSub64 a b m = (a + m - b) % m := by
  dsimp [cSub64]
  by_cases h : a >= b
  · simp only [h, ite_true]
    have heq : a + m - b = m + (a - b) := by omega
    rw [heq]
    exact (modulo_add_unit (a - b) m hm (by omega)).symm
  · have hlt : a < b := by omega
    have heq : a + (m - b) = a + m - b := by omega
    have hsmall : a + m - b < m := by omega
    simp only [h, ite_false, heq, Nat.mod_eq_of_lt hsmall,
      Nat.mod_eq_of_lt (show a + m - b < 2 ^ 64 by omega)]

end PqcAssay

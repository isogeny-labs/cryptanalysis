import Mathlib.Data.Finset.Interval
import Mathlib.Data.ZMod.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset

namespace M31Degree
open Finset

/-- Each term is the set of bits in a square-free monomial. -/
def anf {n : ℕ} (terms : Finset (Finset (Fin n))) (x : Finset (Fin n)) : ZMod 2 :=
  ∑ t ∈ terms, if t ⊆ x then 1 else 0

theorem monomialParity {n : ℕ} (t : Finset (Fin n)) :
    (∑ x : Finset (Fin n), if t ⊆ x then (1 : ZMod 2) else 0) =
      if t = univ then 1 else 0 := by
  rw [sum_boole]
  have h : univ.filter (fun x : Finset (Fin n) => t ⊆ x) = Icc t univ := by
    ext x; simp
  rw [h, card_Icc_finset (subset_univ t), Nat.cast_pow]
  by_cases ht : t = univ
  · simp [ht]
  · have hs : t ⊂ univ := Finset.ssubset_iff_subset_ne.mpr ⟨subset_univ _, ht⟩
    have hn := Nat.sub_ne_zero_of_lt (Finset.card_lt_card hs)
    have hn' : n - t.card ≠ 0 := by simpa using hn
    simp [ht, show (2 : ZMod 2) = 0 by decide, hn']

theorem fullTermParity {n : ℕ} (terms : Finset (Finset (Fin n))) :
    (∑ x : Finset (Fin n), anf terms x) = if univ ∈ terms then 1 else 0 := by
  unfold anf
  rw [Finset.sum_comm]
  simp_rw [monomialParity]
  simp

/-- The numerical slice count is an explicit external hypothesis. -/
theorem m31Slice {terms : Finset (Finset (Fin 30))}
    (count : (univ.filter (fun x => anf terms x = 1)).card = 536874593) :
    (univ : Finset (Fin 30)) ∈ terms := by
  have hbit (v : ZMod 2) : (if v = 1 then 1 else 0) = v := by
    fin_cases v <;> decide
  have h := Finset.natCast_card_filter (R := ZMod 2) (fun x => anf terms x = 1) univ
  simp only [count, hbit, fullTermParity] at h
  by_contra hn
  simp [hn] at h
  exact (by decide : (536874593 : ZMod 2) ≠ 0) h

end M31Degree

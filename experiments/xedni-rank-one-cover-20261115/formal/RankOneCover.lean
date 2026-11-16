import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Int.Interval
import Mathlib.Tactic

namespace XedniRankOneCover

/-- A bounded integer-coordinate family covering a prime-order cyclic group
needs at least as many coordinates as group elements. -/
theorem coordinate_cover_lower_bound (q K : ℕ) [NeZero q] (g : ZMod q)
    (hcover : ∀ z : ZMod q, ∃ k : ℤ,
      -(K : ℤ) ≤ k ∧ k ≤ K ∧ k • g = z) :
    q ≤ 2 * K + 1 := by
  let S : Finset ℤ := Finset.Icc (-(K : ℤ)) (K : ℤ)
  have hs : Function.Surjective (fun k : S => (k.1 : ℤ) • g) := by
    intro z
    obtain ⟨k, hlo, hhi, hk⟩ := hcover z
    exact ⟨⟨k, Finset.mem_Icc.mpr ⟨hlo, hhi⟩⟩, hk⟩
  have hc := Fintype.card_le_of_surjective (fun k : S => (k.1 : ℤ) • g) hs
  have hsize : S.card = 2 * K + 1 := by
    simp only [S, Int.card_Icc]
    omega
  rw [ZMod.card, Fintype.card_coe, hsize] at hc
  exact hc

theorem torsion_coordinate_cover_lower_bound (q K T : ℕ) [NeZero q]
    (g : ZMod q) (torsion : Fin T → ZMod q)
    (hcover : ∀ z : ZMod q, ∃ t : Fin T, ∃ k : ℤ,
      -(K : ℤ) ≤ k ∧ k ≤ K ∧ k • g + torsion t = z) :
    q ≤ T * (2 * K + 1) := by
  let S : Finset ℤ := Finset.Icc (-(K : ℤ)) (K : ℤ)
  have hs : Function.Surjective
      (fun pair : Fin T × S => (pair.2.1 : ℤ) • g + torsion pair.1) := by
    intro z
    obtain ⟨t, k, hlo, hhi, hk⟩ := hcover z
    exact ⟨⟨t, ⟨k, Finset.mem_Icc.mpr ⟨hlo, hhi⟩⟩⟩, hk⟩
  have hc := Fintype.card_le_of_surjective
    (fun pair : Fin T × S => (pair.2.1 : ℤ) • g + torsion pair.1) hs
  have hsize : S.card = 2 * K + 1 := by
    simp only [S, Int.card_Icc]
    omega
  simpa [ZMod.card, Fintype.card_prod, Fintype.card_fin,
    Fintype.card_coe, hsize] using hc

theorem no_uniform_rank_one_cover (q K c L : ℕ) [NeZero q] (g : ZMod q)
    (hcover : ∀ z : ZMod q, ∃ k : ℤ,
      -(K : ℤ) ≤ k ∧ k ≤ K ∧ k • g = z)
    (hcoord : K ≤ c * L)
    (hrank : 2 * c + 1 < L)
    (hbudget : (4 * L + 1) ^ 2 - 1 < q) : False := by
  have hq := coordinate_cover_lower_bound q K g hcover
  have hL : 0 < L := by omega
  have hmul := Nat.mul_lt_mul_of_pos_right hrank hL
  have hpow : 1 ≤ (4 * L + 1) ^ 2 := by
    have hp : 0 < (4 * L + 1) ^ 2 := pow_pos (by omega) 2
    omega
  have hsub : ((4 * L + 1) ^ 2 - 1) + 1 =
      (4 * L + 1) ^ 2 := Nat.sub_add_cancel hpow
  nlinarith

theorem no_uniform_rank_one_cover_with_torsion
    (q K T c L : ℕ) [NeZero q] (g : ZMod q)
    (torsion : Fin T → ZMod q)
    (hcover : ∀ z : ZMod q, ∃ t : Fin T, ∃ k : ℤ,
      -(K : ℤ) ≤ k ∧ k ≤ K ∧ k • g + torsion t = z)
    (hcoord : K ≤ c * L)
    (hrank : T * (2 * c + 1) < L)
    (hbudget : (4 * L + 1) ^ 2 - 1 < q) : False := by
  have hq := torsion_coordinate_cover_lower_bound q K T g torsion hcover
  have hL : 0 < L := by omega
  have hcoord' := Nat.mul_le_mul_left T hcoord
  have hrank' := Nat.mul_lt_mul_of_pos_right hrank hL
  have hpow : 1 ≤ (4 * L + 1) ^ 2 := by
    have hp : 0 < (4 * L + 1) ^ 2 := pow_pos (by omega) 2
    omega
  have hsub : ((4 * L + 1) ^ 2 - 1) + 1 =
      (4 * L + 1) ^ 2 := Nat.sub_add_cancel hpow
  nlinarith

#print axioms coordinate_cover_lower_bound
#print axioms torsion_coordinate_cover_lower_bound
#print axioms no_uniform_rank_one_cover
#print axioms no_uniform_rank_one_cover_with_torsion

end XedniRankOneCover

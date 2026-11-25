import M31FixtureObstruction
open Finset
namespace M31CensusCard
abbrev F := M31FixtureObstruction.F

theorem card_points (s : Finset (F × F))
    (curve : ∀ a ∈ s, a.2^2 = a.1^3 + 2*a.1 + 14)
    (closed : ∀ a ∈ s, (a.1, -a.2) ∈ s) :
    s.card = 2 * (s.image Prod.fst).card := by
  have fiber (x : F) (hx : x ∈ s.image Prod.fst) :
      (s.filter (fun a => a.1 = x)).card = 2 := by
    obtain ⟨⟨u,y⟩, hy, rfl⟩ := mem_image.mp hx
    have cy := curve (u,y) hy
    have nz : y ≠ 0 := by
      rintro rfl
      exact M31FixtureObstruction.no_root u (by simpa using cy.symm)
    have distinct : (u,y) ≠ (u,-y) := by
      intro he
      have he' : y = -y := congrArg Prod.snd he
      have hz : (2:F)*y = 0 := by linear_combination he'
      exact nz ((mul_eq_zero.mp hz).resolve_left (by decide))
    have sets : s.filter (fun a => a.1 = u) = {(u,y),(u,-y)} := by
      ext ⟨v,z⟩
      constructor
      · intro h
        obtain ⟨hz, rfl⟩ := mem_filter.mp h
        have cz := curve (v,z) hz
        have sq : z^2 = y^2 := cz.trans cy.symm
        rcases sq_eq_sq_iff_eq_or_eq_neg.mp sq with h | h <;> simp [h]
      · intro h
        simp only [mem_insert, mem_singleton] at h
        rcases h with h | h <;> cases h
        · exact mem_filter.mpr ⟨hy,rfl⟩
        · exact mem_filter.mpr ⟨closed (u,y) hy,rfl⟩
    rw [sets]
    simp [distinct]
  calc
    s.card = _ := Finset.card_eq_sum_card_image Prod.fst s
    _ = ∑ _x ∈ s.image Prod.fst, 2 := Finset.sum_congr rfl fiber
    _ = _ := by simp [Nat.mul_comm]

#print axioms card_points
end M31CensusCard

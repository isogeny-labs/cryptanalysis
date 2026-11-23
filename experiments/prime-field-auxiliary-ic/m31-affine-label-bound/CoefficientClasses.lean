import Mathlib

namespace M31CoefficientClasses

abbrev F := ZMod 2147483647
instance : Fact (Nat.Prime 2147483647) := ⟨by native_decide⟩

def seven : Fˣ := Units.mk0 7 (by decide)

theorem generatorOrder : orderOf seven = 2147483646 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by native_decide)
  have checks : ∀ q ∈ Nat.primeFactors 2147483646, seven ^ (2147483646 / q) ≠ 1 := by
    native_decide
  exact fun q hq hd => checks q (Nat.mem_primeFactors.mpr ⟨hq, hd, by decide⟩)

private theorem represented (v : Fˣ) : ∃ n : ℕ, seven ^ n = v := by
  have top : Subgroup.zpowers seven = ⊤ := by
    rw [← Subgroup.card_eq_iff_eq_top, Nat.card_zpowers, generatorOrder,
      Nat.card_eq_fintype_card, ZMod.card_units_eq_totient, Nat.totient_prime Fact.out]
  exact mem_powers_iff_mem_zpowers.mpr (top ▸ Subgroup.mem_top v)

private theorem splitPower (v : Fˣ) (k : ℕ) (hk : 0 < k) :
    ∃ r : Fin k, ∃ m : ℕ, v = seven ^ r.val * (seven ^ k) ^ m := by
  obtain ⟨n, rfl⟩ := represented v
  refine ⟨⟨n % k, Nat.mod_lt _ hk⟩, n / k, ?_⟩
  rw [← pow_mul, ← pow_add, Nat.mod_add_div]

/-- The nonzero constant coefficients modulo sixth powers are represented
by 1,7,49,343,2401,16807. -/
theorem sextic (v : Fˣ) : ∃ r : Fin 6, ∃ u : Fˣ, v = seven ^ r.val * u ^ 6 := by
  obtain ⟨r,m,h⟩ := splitPower v 6 (by decide)
  exact ⟨r, seven ^ m, by simpa only [← pow_mul, Nat.mul_comm 6 m] using h⟩

/-- The nonzero linear coefficients modulo fourth powers are represented by 1,7. -/
theorem quartic (v : Fˣ) : ∃ r : Fin 2, ∃ u : Fˣ, v = seven ^ r.val * u ^ 4 := by
  obtain ⟨r,m,h⟩ := splitPower v 2 (by decide)
  have lift : seven ^ 2 = (seven ^ 536870912) ^ 4 := by native_decide
  rw [lift] at h
  exact ⟨r, (seven ^ 536870912) ^ m, by simpa only [← pow_mul, Nat.mul_comm 4 m, Nat.mul_assoc] using h⟩

open WeierstrassCurve

def shortCurve (a b : F) : WeierstrassCurve F := ⟨0, 0, 0, a, b⟩

private theorem scale (u : Fˣ) (a b : F) :
    (VariableChange.mk u⁻¹ 0 0 0) • shortCurve a b =
      shortCurve (a * (u : F)^4) (b * (u : F)^6) := by
  ext <;> simp [variableChange_a₁, variableChange_a₂, variableChange_a₃,
    variableChange_a₄, variableChange_a₆, shortCurve, mul_comm] <;> ring

theorem constantModels (b : Fˣ) : ∃ r : Fin 6, ∃ C : VariableChange F,
    C • shortCurve 0 (7 ^ r.val) = shortCurve 0 b := by
  obtain ⟨r,u,rfl⟩ := sextic b
  exact ⟨r, _, by simpa [seven] using scale u 0 (7 ^ r.val)⟩

theorem linearModels (a : Fˣ) : ∃ r : Fin 2, ∃ C : VariableChange F,
    C • shortCurve (7 ^ r.val) 0 = shortCurve a 0 := by
  obtain ⟨r,u,rfl⟩ := quartic a
  exact ⟨r, _, by simpa [seven] using scale u (7 ^ r.val) 0⟩

def fixtureScale : Fˣ := Units.mk0 771888343 (by decide)

/-- Coordinate scaling to linear coefficient -3 on the two public fixtures. -/
theorem firstMinusThree :
    (VariableChange.mk fixtureScale⁻¹ 0 0 0) • shortCurve 2 14 =
      shortCurve (-3) 378293461 := by
  rw [scale]
  congr 1

theorem secondMinusThree :
    (VariableChange.mk fixtureScale⁻¹ 0 0 0) • shortCurve 2 36 =
      shortCurve (-3) 972754614 := by
  rw [scale]
  congr 1

end M31CoefficientClasses

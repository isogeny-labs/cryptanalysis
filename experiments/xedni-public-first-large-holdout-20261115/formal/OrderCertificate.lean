import PointAddition

namespace XedniPublicFirstLargeHoldout

/-- The p=313 generator has order dividing 331 by the checked binary point chain. -/
theorem panel313_order_divides_331 :
    (331 : ℕ) • panelGenerator 313 panel313_good_prime = 0 := by
  let G := panelGenerator 313 panel313_good_prime
  have h2 : (2 : ℕ) • G = panel313Double := by
    change G + G = panel313Double
    exact panel313_double
  have h4 : (4 : ℕ) • G = panel313Quadruple := by
    calc
      (4 : ℕ) • G = (2 + 2 : ℕ) • G := by norm_num
      _ = (2 : ℕ) • G + (2 : ℕ) • G := by rw [add_nsmul]
      _ = panel313Quadruple := by rw [h2, panel313_second_double]
  have h8 : (8 : ℕ) • G = panel313Octuple := by
    calc
      (8 : ℕ) • G = (4 + 4 : ℕ) • G := by norm_num
      _ = (4 : ℕ) • G + (4 : ℕ) • G := by rw [add_nsmul]
      _ = panel313Octuple := by rw [h4, panel313_third_double]
  have h16 : (16 : ℕ) • G = panel313Sixteen := by
    calc
      (16 : ℕ) • G = (8 + 8 : ℕ) • G := by norm_num
      _ = (8 : ℕ) • G + (8 : ℕ) • G := by rw [add_nsmul]
      _ = panel313Sixteen := by rw [h8, panel313_fourth_double]
  have h32 : (32 : ℕ) • G = panel313ThirtyTwo := by
    calc
      (32 : ℕ) • G = (16 + 16 : ℕ) • G := by norm_num
      _ = (16 : ℕ) • G + (16 : ℕ) • G := by rw [add_nsmul]
      _ = panel313ThirtyTwo := by rw [h16, panel313_fifth_double]
  have h64 : (64 : ℕ) • G = panel313SixtyFour := by
    calc
      (64 : ℕ) • G = (32 + 32 : ℕ) • G := by norm_num
      _ = (32 : ℕ) • G + (32 : ℕ) • G := by rw [add_nsmul]
      _ = panel313SixtyFour := by rw [h32, panel313_sixth_double]
  have h128 : (128 : ℕ) • G = panel313OneTwentyEight := by
    calc
      (128 : ℕ) • G = (64 + 64 : ℕ) • G := by norm_num
      _ = (64 : ℕ) • G + (64 : ℕ) • G := by rw [add_nsmul]
      _ = panel313OneTwentyEight := by rw [h64, panel313_seventh_double]
  have h256 : (256 : ℕ) • G = panel313TwoFiftySix := by
    calc
      (256 : ℕ) • G = (128 + 128 : ℕ) • G := by norm_num
      _ = (128 : ℕ) • G + (128 : ℕ) • G := by rw [add_nsmul]
      _ = panel313TwoFiftySix := by rw [h128, panel313_eighth_double]
  have h320 : (320 : ℕ) • G = panel313ThreeTwenty := by
    calc
      (320 : ℕ) • G = (256 + 64 : ℕ) • G := by norm_num
      _ = (256 : ℕ) • G + (64 : ℕ) • G := by rw [add_nsmul]
      _ = panel313ThreeTwenty := by rw [h256, h64, panel313_add320]
  have h328 : (328 : ℕ) • G = panel313ThreeTwentyEight := by
    calc
      (328 : ℕ) • G = (320 + 8 : ℕ) • G := by norm_num
      _ = (320 : ℕ) • G + (8 : ℕ) • G := by rw [add_nsmul]
      _ = panel313ThreeTwentyEight := by rw [h320, h8, panel313_add328]
  have h330 : (330 : ℕ) • G = panel313ThreeThirty := by
    calc
      (330 : ℕ) • G = (328 + 2 : ℕ) • G := by norm_num
      _ = (328 : ℕ) • G + (2 : ℕ) • G := by rw [add_nsmul]
      _ = panel313ThreeThirty := by rw [h328, h2, panel313_add330]
  change (331 : ℕ) • G = 0
  calc
    (331 : ℕ) • G = (330 + 1 : ℕ) • G := by norm_num
    _ = (330 : ℕ) • G + G := by rw [add_nsmul, one_nsmul]
    _ = 0 := by rw [h330, panel313_add331]

#print axioms panel313_order_divides_331

instance : Fact (Nat.Prime 331) := ⟨by norm_num⟩

/-- The exact additive order of the p=313 panel generator. -/
theorem panel313_generator_order :
    addOrderOf (panelGenerator 313 panel313_good_prime) = 331 := by
  exact addOrderOf_eq_prime panel313_order_divides_331
    (panelGenerator_nonzero 313 panel313_good_prime)

/-- Concrete scalar recovery for distinct-offset public relations on the p=313 panel group. -/
theorem panel313_public_relation_iff_recovery
    (a b w t₁ t₂ : ZMod 331) (ha : a ≠ 0) (ht : t₁ ≠ t₂) :
    TorsionPublicRelation 331
        (cyclic_torsion 331 (panelGenerator 313 panel313_good_prime)
          panel313_order_divides_331)
        ⟨panelGenerator 313 panel313_good_prime, AddSubgroup.mem_zmultiples _⟩
        a b w t₁ t₂ ↔
      a + b ≠ 0 ∧ w = (a * t₁ + b * t₂) / (a + b) := by
  exact panel_curve_public_relation_iff_recovery 313 331 panel313_good_prime
    panel313_order_divides_331 a b w t₁ t₂ ha ht

#print axioms panel313_generator_order
#print axioms panel313_public_relation_iff_recovery

end XedniPublicFirstLargeHoldout


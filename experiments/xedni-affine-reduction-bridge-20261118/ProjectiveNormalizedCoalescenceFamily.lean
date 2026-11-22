import ProjectivePrimitiveAddition
import ProjectiveCoalescenceFamily
import Mathlib.Tactic

/-! The primitive reduction map agrees with reduced doubling throughout the
coalescing power family, while direct reduction of the integral chord class
does not. -/
namespace XedniProjectiveNormalizedCoalescenceFamily

open XedniProjectivePrimitiveReductionMap
open XedniProjectivePrimitiveUniqueness
open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

private instance : Fact (Nat.Prime 5) := ⟨by decide⟩

private def q : ℤ →+* ℚ := Int.castRingHom ℚ
private def f : ℤ →+* ZMod 5 := Int.castRingHom (ZMod 5)
private def W (d : ℤ) : WeierstrassCurve ℤ := ⟨0, 0, 0, -(d ^ 2), 1⟩
private def P : Fin 3 → ℤ := ![0, 1, 1]
private def T (d : ℤ) : Fin 3 → ℤ := ![d, 1, 1]
private def U (d : ℤ) : Fin 3 → ℤ := ![-d, -1, 1]

/-- A primitive integer triple defines a nonzero rational projective class. -/
noncomputable def classOfPrimitive (A : Fin 3 → ℤ) (hA : Primitive A) :
    NonzeroClass ℚ := by
  refine ⟨mapClass q (⟦A⟧ : PointClass ℤ), ?_⟩
  intro hzero
  have hAq := primitive_map_ne_zero q A hA
  change (⟦q ∘ A⟧ : PointClass ℚ) = ⟦(0 : Fin 3 → ℚ)⟧ at hzero
  obtain ⟨u, hu⟩ := Quotient.eq.mp hzero
  apply hAq
  have hz : u • (0 : Fin 3 → ℚ) = 0 := by simp
  exact hu.symm.trans hz

/-- The global primitive reduction agrees with reduction of every supplied
primitive integral representative. -/
theorem reduce_classOfPrimitive {S : Type*} [CommRing S] [Nontrivial S]
    (g : ℤ →+* S) (A : Fin 3 → ℤ) (hA : Primitive A) :
    (reduceNonzero g (classOfPrimitive A hA)).val =
      mapClass g (⟦A⟧ : PointClass ℤ) := by
  apply reduceNonzero_eq_of_rep g (classOfPrimitive A hA) A hA
  rfl

private theorem primP : Primitive P :=
  primitive_of_z_one P rfl

private theorem primT (d : ℤ) : Primitive (T d) :=
  primitive_of_z_one (T d) rfl

private theorem primU (d : ℤ) : Primitive (U d) :=
  primitive_of_z_one (U d) rfl

private noncomputable def CP : NonzeroClass ℚ := classOfPrimitive P primP
private noncomputable def CT (d : ℤ) : NonzeroClass ℚ :=
  classOfPrimitive (T d) (primT d)
private noncomputable def CU (d : ℤ) : NonzeroClass ℚ :=
  classOfPrimitive (U d) (primU d)

/-- At every positive 5-adic depth, the rational sum reduces through the
primitive class to the doubled point on the smooth residue curve. -/
theorem power_family_normalized_add (k : ℕ) :
    WeierstrassCurve.Projective.addMap
      ((W ((5 : ℤ) ^ (k + 1))).map q)
      (CP.val) ((CT ((5 : ℤ) ^ (k + 1))).val) =
      (CU ((5 : ℤ) ^ (k + 1))).val ∧
    WeierstrassCurve.Projective.addMap
      ((W ((5 : ℤ) ^ (k + 1))).map f)
      (reduceNonzero f CP).val
      (reduceNonzero f (CT ((5 : ℤ) ^ (k + 1)))).val =
      (reduceNonzero f (CU ((5 : ℤ) ^ (k + 1)))).val := by
  constructor
  · change WeierstrassCurve.Projective.addMap
      ((W ((5 : ℤ) ^ (k + 1))).map q)
      (mapClass q (⟦P⟧ : PointClass ℤ))
      (mapClass q (⟦T ((5 : ℤ) ^ (k + 1))⟧ : PointClass ℤ)) =
      mapClass q (⟦U ((5 : ℤ) ^ (k + 1))⟧ : PointClass ℤ)
    exact XedniProjectiveCoalescenceFamily.power_family_rational_add_eq_primitive k
  · unfold CP CT CU
    rw [reduce_classOfPrimitive, reduce_classOfPrimitive,
      reduce_classOfPrimitive]
    exact (XedniProjectiveCoalescenceFamily.power_family_primitive_reduction k).symm

/-- On the same smooth residue curve, reducing the unnormalized integral
chord class gives a different class from the reduced addition. -/
theorem power_family_raw_map_differs (k : ℕ) :
    mapClass f (WeierstrassCurve.Projective.addMap
      (W ((5 : ℤ) ^ (k + 1)))
      (⟦P⟧ : PointClass ℤ)
      ⟦T ((5 : ℤ) ^ (k + 1))⟧) ≠
    WeierstrassCurve.Projective.addMap
      ((W ((5 : ℤ) ^ (k + 1))).map f)
      (reduceNonzero f CP).val
      (reduceNonzero f (CT ((5 : ℤ) ^ (k + 1)))).val := by
  unfold CP CT
  rw [reduce_classOfPrimitive, reduce_classOfPrimitive]
  exact XedniProjectiveCoalescenceFamily.power_family_raw_mapClass_not_addMap k

theorem power_family_reduced_smooth (k : ℕ) :
    ((W ((5 : ℤ) ^ (k + 1))).map f).IsElliptic :=
  XedniProjectiveCoalescenceFamily.power_family_reduced_curve_elliptic k

#print axioms reduce_classOfPrimitive
#print axioms power_family_normalized_add
#print axioms power_family_raw_map_differs
#print axioms power_family_reduced_smooth

end XedniProjectiveNormalizedCoalescenceFamily

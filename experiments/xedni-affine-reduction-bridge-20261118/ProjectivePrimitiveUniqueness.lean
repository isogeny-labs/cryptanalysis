import ProjectiveAffineNormalizationUniqueness
import Mathlib.Tactic

/-! Primitive integral representatives of one rational projective class
differ by an integer unit. This gives a choice-independent reduction for
all primitive projective triples, including the point at infinity. -/
namespace XedniProjectivePrimitiveUniqueness

open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

private def q : ℤ →+* ℚ := Int.castRingHom ℚ

/-- An explicit Bézout certificate that the three coordinates generate the
unit ideal of `ℤ`. -/
def Primitive (U : Fin 3 → ℤ) : Prop :=
  ∃ a b c : ℤ, a * U 0 + b * U 1 + c * U 2 = 1

theorem primitive_of_z_one (U : Fin 3 → ℤ) (hZ : U 2 = 1) :
    Primitive U := by
  refine ⟨0, 0, 1, ?_⟩
  simp [hZ]

/-- A primitive integer triple never reduces to the zero vector in a
nontrivial target ring. -/
theorem primitive_map_ne_zero {S : Type*} [CommRing S] [Nontrivial S]
    (g : ℤ →+* S) (U : Fin 3 → ℤ) (hU : Primitive U) :
    g ∘ U ≠ (0 : Fin 3 → S) := by
  obtain ⟨a, b, c, hbez⟩ := hU
  intro hzero
  have h0 : g (U 0) = 0 := by
    have h := congrFun hzero 0
    simpa using h
  have h1 : g (U 1) = 0 := by
    have h := congrFun hzero 1
    simpa using h
  have h2 : g (U 2) = 0 := by
    have h := congrFun hzero 2
    simpa using h
  have hbad : (1 : S) = 0 := by
    calc
      (1 : S) = g (a * U 0 + b * U 1 + c * U 2) := by rw [hbez]; simp
      _ = 0 := by simp only [map_add, map_mul, h0, h1, h2, mul_zero, add_zero]
  exact one_ne_zero hbad

/-- Rational projective equivalence of primitive integral triples descends
to equivalence by an integer unit. -/
theorem int_equiv_of_rational_equiv_primitive (U V : Fin 3 → ℤ)
    (hU : Primitive U) (hV : Primitive V)
    (h : (q ∘ U) ≈ (q ∘ V)) : U ≈ V := by
  obtain ⟨a, b, c, ha⟩ := hU
  obtain ⟨e, f, g, hb⟩ := hV
  obtain ⟨scale, hscale⟩ := h
  have hcoord (i : Fin 3) : ((U i : ℤ) : ℚ) =
      (scale : ℚ) * ((V i : ℤ) : ℚ) := by
    have hi := congrFun hscale i
    simpa [q, Units.smul_def] using hi.symm
  let m : ℤ := e * U 0 + f * U 1 + g * U 2
  let n : ℤ := a * V 0 + b * V 1 + c * V 2
  have hbQ : (e : ℚ) * (V 0 : ℚ) + (f : ℚ) * (V 1 : ℚ) +
      (g : ℚ) * (V 2 : ℚ) = 1 := by exact_mod_cast hb
  have haQ : (a : ℚ) * (U 0 : ℚ) + (b : ℚ) * (U 1 : ℚ) +
      (c : ℚ) * (U 2 : ℚ) = 1 := by exact_mod_cast ha
  have hscalem : (scale : ℚ) = (m : ℚ) := by
    calc
      (scale : ℚ) = (scale : ℚ) * 1 := by ring
      _ = (scale : ℚ) * ((e : ℚ) * (V 0 : ℚ) +
          (f : ℚ) * (V 1 : ℚ) + (g : ℚ) * (V 2 : ℚ)) := by rw [hbQ]
      _ = (e : ℚ) * (U 0 : ℚ) + (f : ℚ) * (U 1 : ℚ) +
          (g : ℚ) * (U 2 : ℚ) := by rw [hcoord 0, hcoord 1, hcoord 2]; ring
      _ = (m : ℚ) := by simp [m]
  have hmnQ : (m : ℚ) * (n : ℚ) = 1 := by
    calc
      (m : ℚ) * (n : ℚ) =
          (scale : ℚ) * ((a : ℚ) * (V 0 : ℚ) +
            (b : ℚ) * (V 1 : ℚ) + (c : ℚ) * (V 2 : ℚ)) := by
              rw [hscalem]
              simp [n]
      _ = (a : ℚ) * (U 0 : ℚ) + (b : ℚ) * (U 1 : ℚ) +
          (c : ℚ) * (U 2 : ℚ) := by rw [hcoord 0, hcoord 1, hcoord 2]; ring
      _ = 1 := haQ
  have hmn : m * n = 1 := by exact_mod_cast hmnQ
  have hmUnit : IsUnit m := isUnit_iff_dvd_one.mpr ⟨n, hmn.symm⟩
  obtain ⟨u, hu⟩ := hmUnit
  have hUV : U = m • V := by
    ext i
    have hi := hcoord i
    rw [hscalem] at hi
    exact_mod_cast hi
  refine ⟨u, ?_⟩
  simpa only [Units.smul_def, hu] using hUV.symm

/-- Primitive integral representatives of the same rational class reduce to
the same projective class through every ring homomorphism. -/
theorem primitive_reduction_independent {S : Type*} [CommRing S]
    (g : ℤ →+* S) (U V : Fin 3 → ℤ)
    (hU : Primitive U) (hV : Primitive V)
    (hClass : mapClass q (⟦U⟧ : WeierstrassCurve.Projective.PointClass ℤ) =
      mapClass q ⟦V⟧) :
    mapClass g (⟦U⟧ : WeierstrassCurve.Projective.PointClass ℤ) =
      mapClass g ⟦V⟧ := by
  change (⟦q ∘ U⟧ : WeierstrassCurve.Projective.PointClass ℚ) = ⟦q ∘ V⟧ at hClass
  have hInt := int_equiv_of_rational_equiv_primitive U V hU hV (Quotient.eq.mp hClass)
  exact Quotient.eq.mpr (XedniProjectiveClassReduction.map_equiv g hInt)

#print axioms primitive_of_z_one
#print axioms primitive_map_ne_zero
#print axioms int_equiv_of_rational_equiv_primitive
#print axioms primitive_reduction_independent

end XedniProjectivePrimitiveUniqueness

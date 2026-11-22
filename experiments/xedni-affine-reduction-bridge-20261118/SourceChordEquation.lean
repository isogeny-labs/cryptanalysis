import ResidueProjectiveZero
import Mathlib.Tactic

/-! A compact polynomial certificate puts the homogeneous chord triple on
the source short-Weierstrass curve without dividing by the x-difference. -/
namespace XedniSourceChordEquation

open XedniRegularChainReduction XedniResidueVerticalObstruction

/-- The compact four-variable factorization behind the chord identity. -/
theorem chord_key_factor {S : Type*} [CommRing S]
    (x d X a : S) :
    let L := x * d ^ 2 - X
    let s := 3 * x ^ 2 + 3 * x * d + d ^ 2 + a
    (X + (2 * x + d) * d ^ 2) * L * (L + d ^ 3) =
      X ^ 3 + a * X * d ^ 4 + L * d ^ 4 * s - x ^ 3 * d ^ 6 -
        a * x * d ^ 6 := by
  dsimp
  ring

/-- The full chord identity follows from the small factorization and a
single defining equation for the x-numerator. -/
theorem chord_polynomial_identity {S : Type*} [CommRing S]
    (x y d n a b X : S)
    (hX : X = n ^ 2 - (2 * x + d) * d ^ 2) :
    let L := x * d ^ 2 - X
    let Y := n * L - y * d ^ 3
    let E := n * (2 * y + n) - d * (3 * x ^ 2 + 3 * x * d + d ^ 2 + a)
    Y ^ 2 - X ^ 3 - a * X * d ^ 4 - b * d ^ 6 =
      -d ^ 3 * L * E + d ^ 6 * (y ^ 2 - x ^ 3 - a * x - b) := by
  let L := x * d ^ 2 - X
  let s := 3 * x ^ 2 + 3 * x * d + d ^ 2 + a
  have hkey : (X + (2 * x + d) * d ^ 2) * L * (L + d ^ 3) =
      X ^ 3 + a * X * d ^ 4 + L * d ^ 4 * s - x ^ 3 * d ^ 6 -
        a * x * d ^ 6 := chord_key_factor x d X a
  have hn2 : n ^ 2 = X + (2 * x + d) * d ^ 2 := by
    linear_combination -hX
  change (n * L - y * d ^ 3) ^ 2 - X ^ 3 - a * X * d ^ 4 - b * d ^ 6 =
    -d ^ 3 * L * (n * (2 * y + n) - d * s) +
      d ^ 6 * (y ^ 2 - x ^ 3 - a * x - b)
  linear_combination (norm := ring1) hkey + L * (L + d ^ 3) * hn2

/-- Subtracting two short-Weierstrass curve equations gives the secant
relation over any commutative ring. -/
theorem secant_relation {S : Type*} [CommRing S] {a b : S}
    (P T : CurvePoint S a b) :
    (T.y - P.y) * (P.y + T.y) =
      (T.x - P.x) * (P.x ^ 2 + P.x * T.x + T.x ^ 2 + a) := by
  linear_combination T.onCurve - P.onCurve

/-- The homogeneous chord numerators satisfy the weighted short-Weierstrass
equation over the source ring, including when the x-difference is a nonunit. -/
theorem source_chord_weighted_equation {S : Type*} [CommRing S] {a b : S}
    (P T : CurvePoint S a b) :
    let d := T.x - P.x
    let X := chordXNumerator P T
    let Y := chordYNumerator P T
    Y ^ 2 = X ^ 3 + a * X * d ^ 4 + b * d ^ 6 := by
  let d := T.x - P.x
  let n := T.y - P.y
  let X := chordXNumerator P T
  have hX : X = n ^ 2 - (2 * P.x + d) * d ^ 2 := by
    dsimp [X, n, d, chordXNumerator]
    ring
  have hsec : n * (2 * P.y + n) =
      d * (3 * P.x ^ 2 + 3 * P.x * d + d ^ 2 + a) := by
    calc
      n * (2 * P.y + n) = n * (P.y + T.y) := by dsimp [n]; ring
      _ = d * (P.x ^ 2 + P.x * T.x + T.x ^ 2 + a) := secant_relation P T
      _ = d * (3 * P.x ^ 2 + 3 * P.x * d + d ^ 2 + a) := by dsimp [d]; ring
  have hcurve : P.y ^ 2 - P.x ^ 3 - a * P.x - b = 0 := by
    linear_combination P.onCurve
  have hpoly := chord_polynomial_identity P.x P.y d n a b X hX
  dsimp only at hpoly
  rw [show n * (2 * P.y + n) -
      d * (3 * P.x ^ 2 + 3 * P.x * d + d ^ 2 + a) = 0 from
      sub_eq_zero.mpr hsec, hcurve] at hpoly
  simp only [mul_zero, add_zero] at hpoly
  change (chordYNumerator P T) ^ 2 - X ^ 3 - a * X * d ^ 4 - b * d ^ 6 = 0 at hpoly
  linear_combination hpoly

/-- The standard source-ring homogeneous chord representative. -/
def sourceChordTriple {S : Type*} [CommRing S] {a b : S}
    (P T : CurvePoint S a b) : Fin 3 → S :=
  ![chordXNumerator P T * (T.x - P.x),
    chordYNumerator P T, (T.x - P.x) ^ 3]

private def shortCurveRing {S : Type*} [CommRing S] (a b : S) :
    WeierstrassCurve S := ⟨0, 0, 0, a, b⟩

/-- The homogeneous chord representative satisfies the source projective
curve equation over any commutative ring. -/
theorem sourceChordTriple_on_curve {S : Type*} [CommRing S] {a b : S}
    (P T : CurvePoint S a b) :
    WeierstrassCurve.Projective.Equation (shortCurveRing a b)
      (sourceChordTriple P T) := by
  rw [WeierstrassCurve.Projective.equation_iff]
  have hw := source_chord_weighted_equation P T
  dsimp only at hw
  simp only [sourceChordTriple, shortCurveRing,
    WeierstrassCurve.Projective.fin3_def_ext, zero_mul, add_zero]
  linear_combination (norm := ring1) (T.x - P.x) ^ 3 * hw

#print axioms chord_key_factor
#print axioms chord_polynomial_identity
#print axioms secant_relation
#print axioms source_chord_weighted_equation
#print axioms sourceChordTriple_on_curve

end XedniSourceChordEquation

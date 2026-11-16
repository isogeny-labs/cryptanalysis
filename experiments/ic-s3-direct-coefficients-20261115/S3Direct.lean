import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.CharP.Two
import Mathlib.Tactic.Ring
import Mathlib.Tactic.LinearCombination

/- Algebraic coefficient identity only. This does not verify Rust memory,
word arithmetic, canonical-order emission or the full IC pipeline. -/
namespace S3Direct
open scoped BigOperators
variable {R I : Type*} [CommRing R] [CharP R 2] [Fintype I]

def s3 (x y z b : R) : R := (x+y)^2*z^2 + x*y*z + (x*y)^2 + b

theorem square_linear_form (u v : I → R) (h : ∀ i, u i ^ 2 = u i) :
    (∑ i, u i * v i)^2 = ∑ i, u i * v i^2 := by
  rw [CharTwo.sum_sq]
  apply Finset.sum_congr rfl
  intro i _
  rw [mul_pow, h]

omit [CharP R 2] in
theorem linear_coefficients (u w v : I → R) (z : R) :
    ((∑ i, u i * v i^2) + (∑ i, w i * v i^2))*z^2 =
      ∑ i, (u i + w i)*(v i^2*z^2) := by
  rw [← Finset.sum_add_distrib, Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro i _
  ring

omit [CharP R 2] in
theorem cross_coefficients (u w v : I → R) (z : R) :
    (∑ i, u i*v i)*(∑ j, w j*v j)*z +
      (∑ i, u i*v i^2)*(∑ j, w j*v j^2) =
      ∑ j, ∑ i, (u i*w j)*((v i*v j)*z + (v i*v j)^2) := by
  simp only [Finset.sum_mul, Finset.mul_sum]
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro i _
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro j _
  ring

theorem direct_s3_coefficients (u w v : I → R) (z b : R)
    (hu : ∀ i, u i^2 = u i) (hw : ∀ i, w i^2 = w i) :
    s3 (∑ i, u i*v i) (∑ i, w i*v i) z b =
      b + (∑ i, (u i+w i)*(v i^2*z^2)) +
        ∑ j, ∑ i, (u i*w j)*((v i*v j)*z + (v i*v j)^2) := by
  unfold s3
  rw [CharTwo.add_sq, mul_pow,
    square_linear_form u v hu, square_linear_form w v hw]
  rw [linear_coefficients]
  have hc := cross_coefficients u w v z
  linear_combination hc

omit [CharP R 2] in
theorem cross_symmetric (x y z : R) :
    (x*y)*z + (x*y)^2 = (y*x)*z + (y*x)^2 := by ring

end S3Direct
#print axioms S3Direct.direct_s3_coefficients
#print axioms S3Direct.cross_symmetric

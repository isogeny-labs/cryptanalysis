import Init.Grind.Ring.Basic

/-! Faithful algebraic lemmas for the independent adapters. These statements
do not formalize curves, Picard functors, projective completion or the old
balanced reducer. Those bridges remain explicit in the written proof. -/
set_option autoImplicit false
namespace PrimeNormPullback
open Lean.Grind

theorem cleared_fibre_factorization {K : Type} [CommRing K]
    (n q X a b : K) :
    n^3+a*n*q^4+b*q^6-(X^3+a*X+b)*q^6 =
      (n-X*q^2)*(n^2+X*n*q^2+(X^2+a)*q^4) := by grind

theorem image_support_substitution {K : Type} [CommRing K]
    (z a b A B : K) :
    (A+B*z)^2+(a*B-2*A)*(A+B*z)+(A^2-a*A*B+b*B^2) =
      B^2*(z^2+a*z+b) := by grind

theorem image_ordinate_substitution {K : Type} [CommRing K]
    (z A B C D slope : K) (unit_slope : slope*B=D) :
    C-slope*A+slope*(A+B*z)=C+D*z := by grind

theorem unit_ordinate_recovery {K : Type} [CommRing K]
    (f m inverse n q X Y a b : K)
    (unit : m*inverse=1)
    (cover : f*m^2=n^3+a*n*q^4+b*q^6)
    (fibre : n=X*q^2)
    (target : Y^2=X^3+a*X+b) :
    (Y*q^3*inverse)^2=f := by grind

theorem actual_ordinate_normalization {K : Type} [CommRing K]
    (z : K) (characteristic : (101 : K)=0) :
    50*(44+47*z+55*z^2+2*z^3)=79+27*z+23*z^2+100*z^3 ∧
    50*(87+17*z+53*z^2+5*z^3)=7+42*z+24*z^2+48*z^3 ∧
    50^2*(100+12*z+74*z^2+50*z^3+6*z^4+46*z^5+z^6)=
      25+3*z+69*z^2+63*z^3+52*z^4+62*z^5+76*z^6 := by grind

theorem actual_first_normalized_cover {K : Type} [CommRing K]
    (z : K) (characteristic : (101 : K)=0) :
    (100+12*z+74*z^2+50*z^3+6*z^4+46*z^5+z^6)*
      (79+27*z+23*z^2+100*z^3)^2 =
      (53+52*z+54*z^2+10*z^4)^3 +
      59*(53+52*z+54*z^2+10*z^4)*(z^2+38)^4 +
      27*(z^2+38)^6 := by grind

theorem actual_second_normalized_cover {K : Type} [CommRing K]
    (z : K) (characteristic : (101 : K)=0) :
    (100+12*z+74*z^2+50*z^3+6*z^4+46*z^5+z^6)*
      (7+42*z+24*z^2+48*z^3)^2 =
      (49+92*z^2+96*z^3+71*z^4)^3 +
      44*(49+92*z^2+96*z^3+71*z^4)*(z^2+46)^4 +
      21*(z^2+46)^6 := by grind

theorem actual_first_degree_drop {K : Type} [CommRing K]
    (z : K) (characteristic : (101 : K)=0) :
    (53+52*z+54*z^2+10*z^4)-10*(z^2+38)^2 =
      z^2+52*z+56 := by grind

theorem actual_second_degree_drop {K : Type} [CommRing K]
    (z : K) (characteristic : (101 : K)=0) :
    (49+92*z^2+96*z^3+71*z^4)-71*(z^2+46)^2 =
      z^2*(96*z+24) := by grind

theorem balanced_completion_accounting
    (d nplus nminus : Int) (degree_four : d+nplus+nminus=4) :
    nplus-2=(nplus-1)-1 ∧ nminus-2=1-d-(nplus-1) := by grind

theorem actual_public_inverse_constants :
    (4 : Nat)*9238%12317=1 ∧ (4 : Nat)*82%109=1 ∧
    (4 : Nat)*85%113=1 ∧ (2 : Nat)*6159%12317=1 := by decide

end PrimeNormPullback
#print axioms PrimeNormPullback.cleared_fibre_factorization
#print axioms PrimeNormPullback.image_support_substitution
#print axioms PrimeNormPullback.image_ordinate_substitution
#print axioms PrimeNormPullback.unit_ordinate_recovery
#print axioms PrimeNormPullback.actual_ordinate_normalization
#print axioms PrimeNormPullback.actual_first_normalized_cover
#print axioms PrimeNormPullback.actual_second_normalized_cover
#print axioms PrimeNormPullback.actual_first_degree_drop
#print axioms PrimeNormPullback.actual_second_degree_drop
#print axioms PrimeNormPullback.balanced_completion_accounting
#print axioms PrimeNormPullback.actual_public_inverse_constants

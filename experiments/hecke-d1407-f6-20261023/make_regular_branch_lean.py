"""Generate a faithful Lean polynomial certificate for the regular x=16 branch."""
from hashlib import sha256
from pathlib import Path
import json
import sys

from sage.all import QQ, PolynomialRing

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'tools'))
import hecke11 as H

def expression(coefficients):
    return ' + '.join(f'({int(c)} : ℚ) * x ^ {i}' for i,c in enumerate(coefficients) if c)

def main():
    _,jfun=H.build([2,3]);A=jfun[0]
    R=PolynomialRing(QQ,'x');x=R.gen()
    a0=sum(QQ(v)*x**a for (a,b),v in A.items() if b==0)
    a1=sum(QQ(v)*x**a for (a,b),v in A.items() if b==1)
    g=x**3-x**2-10*x-20
    f=x**4-52820*x**3+1333262*x**2+4971236*x+9789217
    norm=a0*a0-a0*a1-a1*a1*g
    assert norm==-(x-16)**11*f**3
    cusp=a0(16)-61*a1(16)
    assert cusp!=0 and -f(16)**3/cusp==-121
    lean=f'''module

public import Mathlib.Tactic.Ring
public import Mathlib.Tactic.NormNum
public import Mathlib.Tactic.Linarith
public import Mathlib.Algebra.Ring.Rat

/-! Exact regularization of the j-function on X₀(11) at (16,60). -/
namespace RegularBranch

public def a0 (x : ℚ) : ℚ := {expression(a0.list())}
public def a1 (x : ℚ) : ℚ := {expression(a1.list())}
public def curveRhs (x : ℚ) : ℚ := x ^ 3 - x ^ 2 - 10 * x - 20
public def quartic (x : ℚ) : ℚ := {expression(f.list())}
public def extendedJ (x y : ℚ) : ℚ :=
  -(quartic x) ^ 3 / (a0 x + a1 x * (-1-y))

/-- Norm of the j-numerator under the elliptic-curve involution. -/
public theorem norm_identity (x : ℚ) :
    a0 x ^ 2 - a0 x * a1 x - a1 x ^ 2 * curveRhs x =
      -((x-16) ^ 11) * quartic x ^ 3 := by
  unfold a0 a1 curveRhs quartic
  ring

/-- The conjugate numerator stays nonzero at the regular point. -/
public theorem conjugate_nonzero : a0 16 + a1 16 * (-61) ≠ 0 := by
  norm_num [a0, a1]

/-- Both x=16 branches lie on the stated elliptic-curve model. -/
public theorem regular_point_on_curve :
    (60 : ℚ) ^ 2 + 60 = curveRhs 16 := by
  norm_num [curveRhs]

public theorem cusp_point_on_curve :
    (-61 : ℚ) ^ 2 - 61 = curveRhs 16 := by
  norm_num [curveRhs]

/-- The rational extension has the exact value -121 at (16,60). -/
public theorem regular_value : extendedJ 16 60 = -121 := by
  norm_num [extendedJ, quartic, a0, a1]

/-- Away from x=16, the extension agrees with the original j quotient on
the curve whenever its conjugate denominator is nonzero. -/
public theorem matches_original (x y : ℚ)
    (hcurve : y ^ 2 + y = curveRhs x) (hx : x ≠ 16)
    (hconj : a0 x + a1 x * (-1-y) ≠ 0) :
    (a0 x + a1 x * y) / (x-16) ^ 11 = extendedJ x y := by
  have hprod : (a0 x + a1 x * y) * (a0 x + a1 x * (-1-y)) =
      -((x-16) ^ 11) * quartic x ^ 3 := by
    calc
      _ = a0 x ^ 2 - a0 x * a1 x - a1 x ^ 2 * (y ^ 2 + y) := by ring
      _ = a0 x ^ 2 - a0 x * a1 x - a1 x ^ 2 * curveRhs x := by rw [hcurve]
      _ = -((x-16) ^ 11) * quartic x ^ 3 := norm_identity x
  unfold extendedJ
  have hpow : (x-16) ^ 11 ≠ 0 := pow_ne_zero _ (sub_ne_zero.mpr hx)
  apply (div_eq_div_iff hpow hconj).2
  nlinarith [hprod]

end RegularBranch

#print axioms RegularBranch.norm_identity
#print axioms RegularBranch.conjugate_nonzero
#print axioms RegularBranch.regular_point_on_curve
#print axioms RegularBranch.cusp_point_on_curve
#print axioms RegularBranch.regular_value
#print axioms RegularBranch.matches_original
'''
    target=P/'formal/RegularBranch.lean'
    target.write_text(lean)
    receipt={'status':'GENERATED_EXACT_REGULAR_BRANCH_LEAN',
             'j_source_sha256':sha256((P/'tools/hecke11.py').read_bytes()).hexdigest(),
             'generator_sha256':sha256((P/'make_regular_branch_lean.py').read_bytes()).hexdigest(),
             'lean_sha256':sha256(target.read_bytes()).hexdigest(),
             'a0_coefficients':[str(v) for v in a0.list()],
             'a1_coefficients':[str(v) for v in a1.list()],
             'quartic_coefficients':[str(v) for v in f.list()],
             'conjugate_numerator_at_16':str(cusp),
             'regular_j':'-121'}
    (P/'formal/regular-branch-generation.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':receipt['status'],'lean_sha256':receipt['lean_sha256']}))

if __name__=='__main__':main()

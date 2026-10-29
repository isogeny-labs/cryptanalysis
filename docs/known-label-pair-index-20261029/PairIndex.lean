import Mathlib

/- Native build is required by the source-bound corpus admission in this PR.
These declarations prove an abstract module path/cycle bridge and the cleared
addition identity. They do not instantiate the concrete elliptic subgroup,
verify the Python implementation or establish a cost improvement. -/
namespace KnownLabelPairIndex

variable {K V : Type*} [Field K] [AddCommGroup V] [Module K V]

theorem affine_composition (a b : K) (z u v : V) :
    a • (b • z + v) + u = (a*b) • z + (a • v + u) := by
  simp only [smul_add, smul_smul, add_assoc]

theorem affine_path (es : List (K × V)) (z : V) (a : K) (c : V) :
    es.foldl (fun point e => e.1 • point + e.2) (a • z + c) =
      (es.foldl (fun ac e => (e.1*ac.1, e.1 • ac.2 + e.2)) (a,c)).1 • z +
      (es.foldl (fun ac e => (e.1*ac.1, e.1 • ac.2 + e.2)) (a,c)).2 := by
  induction es generalizing a c with
  | nil => rfl
  | cons e es ih =>
    simpa only [List.foldl_cons, smul_add, smul_smul, add_assoc] using
      ih (e.1*a) (e.1 • c + e.2)

theorem cycle_constraint (a : K) (z c : V) (h : z = a • z + c) :
    (1-a) • z = c := by
  rw [sub_smul, one_smul]
  apply sub_eq_iff_eq_add.mpr
  simpa only [add_comm] using h

theorem cycle_recovery (a : K) (z c : V) (ha : a ≠ 1)
    (h : z = a • z + c) : z = (1-a)⁻¹ • c := by
  have hc := congrArg (fun w : V => (1-a)⁻¹ • w) (cycle_constraint a z c h)
  simpa only [smul_smul, inv_mul_cancel₀ (sub_ne_zero.mpr (Ne.symm ha)),
    one_smul] using hc

theorem label_recovery (gamma a b : K) (z p q : V) (hg : gamma ≠ 0)
    (h : gamma • z = a • p + b • q) :
    z = (gamma⁻¹*a) • p + (gamma⁻¹*b) • q := by
  have hc := congrArg (fun w : V => gamma⁻¹ • w) h
  simpa only [smul_add, smul_smul, inv_mul_cancel₀ hg, one_smul] using hc

theorem signed_square (r0 r1 r2 r3 t01 t12 t23 t30 : V)
    (h01 : r1 = t01-r0) (h12 : r2 = t12-r1)
    (h23 : r3 = t23-r2) (h30 : r0 = r3-t30) :
    r0+r0 = t01-t12+t23-t30 := by
  calc
    r0+r0 = (r3-t30)+r0 := congrArg (fun w : V => w+r0) h30
    _ = t01-t12+t23-t30 := by rw [h23, h12, h01]; abel

theorem semaev_pair_identity (x y z u v a b : K)
    (hu : u^2 = x^3+a*x+b) (hv : v^2 = y^3+a*y+b) :
    ((x-y)^2*(z+x+y)-(u+v)^2) *
      ((x-y)^2*(z+x+y)-(u-v)^2) =
    (x-y)^2 * ((x-y)^2*z^2-2*((x+y)*(x*y+a)+2*b)*z+
      (x*y-a)^2-4*b*(x+y)) := by
  linear_combination
    (u^2+(x^3+a*x+b)-2*v^2-2*(x-y)^2*(z+x+y))*hu +
    (v^2+(y^3+a*y+b)-2*(x^3+a*x+b)-2*(x-y)^2*(z+x+y))*hv

#print axioms affine_composition
#print axioms affine_path
#print axioms cycle_constraint
#print axioms cycle_recovery
#print axioms label_recovery
#print axioms signed_square
#print axioms semaev_pair_identity

end KnownLabelPairIndex

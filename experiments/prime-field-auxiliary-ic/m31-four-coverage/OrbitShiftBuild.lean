import Std.Tactic.BVDecide
import OrbitLabels
import Mathlib.GroupTheory.OrderOfElement

namespace M31OrbitShiftBuild
variable {F : Type*} [Field F]

/-- With X=aZ² and Y=bZ³, both chord numerator and denominator
pick up a common Z⁶ when the shift stays projective. -/
theorem raw_chord (x y a b z : F) :
    let X := a*z^2
    let Y := b*z^3
    let dx := x*z^2-X
    let dy := y*z^3-Y
    (dy^2-(x*z^2+X)*dx^2,z^2*dx^2) =
    (((y-b)^2-(x+a)*(x-a)^2)*z^6,((x-a)*z^3)^2) := by
  dsimp only
  congr 1 <;> ring

theorem raw_label (x y a b z : F) (hx : x≠a) (hz : z≠0) :
    let X := a*z^2
    let Y := b*z^3
    let dx := x*z^2-X
    let dy := y*z^3-Y
    let u := ((y-b)/(x-a))^2-x-a
    (∃ t, t^2=M31OrbitLabels.rhs u) ↔
      ∃ t, t^2=M31OrbitLabels.cleared (dy^2-(x*z^2+X)*dx^2) (z^2*dx^2) := by
  dsimp only
  have num := congrArg Prod.fst (raw_chord x y a b z)
  have den := congrArg Prod.snd (raw_chord x y a b z)
  dsimp only at num den
  rw [num, den, M31OrbitLabels.chord_cleared x y a b hx]
  have h : ∀ v : F, v*(x-a)^2*z^6 = v*((x-a)*z^3)^2 := by intro v; ring
  rw [h]
  exact M31OrbitLabels.label _ _ (mul_ne_zero (sub_ne_zero.mpr hx) (pow_ne_zero _ hz))

/-- A mixed addition scales h and r by Z² and Z³. Its coordinates represent
the ordinary chord result with the new scale Z*h. -/
theorem mixed_add (x y a b z m : F) (slope : b-y=m*(a-x)) :
    let X := x*z^2
    let Y := y*z^3
    let h := a*z^2-X
    let r := b*z^3-Y
    let v := X*h^2
    let xn := r^2-h^3-2*v
    let yn := r*(v-xn)-Y*h^3
    let x₁ := m^2-x-a
    (xn,yn) = (x₁*(z*h)^2,(m*(x-x₁)-y)*(z*h)^3) := by
  dsimp only
  have hb : b=m*(a-x)+y := by linear_combination slope
  rw [hb]
  congr 1 <;> ring

theorem double_affine (x y m : F) (slope : 3*x^2+1=m*(2*y)) :
    let s := 4*x*y^2
    let n := 3*x^2+1
    let xn := n^2-2*s
    let yn := n*(s-xn)-8*y^4
    let x₁ := m^2-2*x
    (xn,yn)=(x₁*(2*y)^2,(m*(x-x₁)-y)*(2*y)^3) := by
  dsimp only
  rw [slope]
  congr 1 <;> ring

theorem reciprocal_step (acc d : F) (hp : acc≠0) (hd : d≠0) :
    acc*(acc*d)⁻¹=d⁻¹ ∧ (acc*d)⁻¹*d=acc⁻¹ := by
  constructor <;> field_simp

theorem reindex {G : Type*} [AddCommGroup G] (g : G) (order : addOrderOf g=32)
    (stride j : Nat) : ((j*stride)%32) • g = j • (stride • g) := by
  rw [← order, mod_addOrderOf_nsmul, mul_smul]

/-- Reordering the output preserves any pointwise public label. -/
theorem label_reindex {G L : Type*} [AddCommGroup G] (label : G → L)
    (q g : G) (order : addOrderOf g=32) (stride j : Nat) :
    label (q+((j*stride)%32) • g) = label (q+j • (stride • g)) := by
  rw [reindex g order]

/-- The byte multiply wraps at 256; its low five bits still index the 32-byte table.
Adding 16 to the lane toggles bit four of the index for every odd stride. -/
theorem upper_byte_index (i stride : BitVec 8) (odd : stride &&& 1 = 1) :
    (((i+16)*stride) &&& 31) = (((i*stride) &&& 31) ^^^ 16) := by bv_decide

end M31OrbitShiftBuild

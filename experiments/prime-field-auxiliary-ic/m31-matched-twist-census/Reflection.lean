import Mathlib.Tactic

namespace MatchedTwist

variable {K : Type*} [Field K]

abbrev Triple (K : Type*) := K × K × K

def reflect (v : Triple K) : Triple K := (-v.1, v.2.1, v.2.2)
def scale (c : K) (v : Triple K) : Triple K := (c*v.1, c*v.2.1, c*v.2.2)

def onCubic (s : K) (v : Triple K) : Prop :=
  v.2.1^2*v.2.2 = s*(v.1^3 + v.1*v.2.2^2)

theorem involution (v : Triple K) : reflect (reflect v) = v := by
  rcases v with ⟨x,y,z⟩
  simp [reflect]

theorem projective_scaling (c : K) (v : Triple K) :
    reflect (scale c v) = scale c (reflect v) := by
  simp [reflect, scale]

theorem exchanges_models (s : K) (v : Triple K) :
    onCubic (-s) (reflect v) ↔ onCubic s v := by
  unfold onCubic reflect
  dsimp
  ring_nf

theorem fixes_infinity : reflect ((0,1,0) : Triple K) = (0,1,0) := by
  simp [reflect]

/-- The same affine reflection fails on a specific point of the M31 target. -/
theorem target_counterexample :
    let y : ZMod 2147483647 := 814455902
    y^2 = (1:ZMod 2147483647)^3 + 2*1 + 14 ∧
    y^2 ≠ (-1:ZMod 2147483647)^3 + 2*(-1) + 14 := by decide

end MatchedTwist

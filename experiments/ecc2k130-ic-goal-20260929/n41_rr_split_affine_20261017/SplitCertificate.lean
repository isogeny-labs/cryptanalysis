import Std

/- A binary-linear functional of a bilinear minor pairing is constant one
   on two affine source families when all three difference terms vanish. -/
namespace SplitCertificate

theorem affine_bilinear_separation
    {L R : Type} (addL : L → L → L) (addR : R → R → R)
    (evaluation : L → R → Bool) (leftFamily : L → Prop) (rightFamily : R → Prop)
    (l₀ : L) (r₀ : R)
    (leftLinear : ∀ a b r, evaluation (addL a b) r =
      Bool.xor (evaluation a r) (evaluation b r))
    (rightLinear : ∀ l a b, evaluation l (addR a b) =
      Bool.xor (evaluation l a) (evaluation l b))
    (baseOne : evaluation l₀ r₀ = true)
    (leftZero : ∀ u, leftFamily u → evaluation u r₀ = false)
    (rightZero : ∀ v, rightFamily v → evaluation l₀ v = false)
    (crossZero : ∀ u v, leftFamily u → rightFamily v →
      evaluation u v = false) :
    ∀ u v, leftFamily u → rightFamily v →
      evaluation (addL l₀ u) (addR r₀ v) = true := by
  intro u v hu hv
  rw [leftLinear, rightLinear, rightLinear]
  simp [baseOne, leftZero u hu, rightZero v hv, crossZero u v hu hv]

#print axioms affine_bilinear_separation

end SplitCertificate

import Std

/- Integer-polynomial lift of the characteristic-two S3 target inversion. -/
namespace TargetQuadratic

def forward (u v t : Int) : Int :=
  (1 + (u*v)^2)*t^2 + u*v*t + (u+v)^2

def inverseForm (u v t : Int) : Int :=
  (1+(u*t)^2)*v^2 + (u*t)*v + (u^2+t^2)

theorem target_inverse_identity (u v t : Int) :
    forward u v t = inverseForm u v t + 2*u*v := by
  unfold forward inverseForm
  grind +ring

theorem target_inverse_parity (u v t k : Int)
    (h : forward u v t = 2*k) :
    ∃ j : Int, inverseForm u v t = 2*j := by
  rw [target_inverse_identity] at h
  refine ⟨k-u*v, ?_⟩
  grind +ring

theorem target_inverse_mod_two (u v t : Int) :
    forward u v t % 2 = 0 ↔ inverseForm u v t % 2 = 0 := by
  rw [target_inverse_identity]
  simp [Int.add_emod, Int.mul_emod]

#print axioms target_inverse_identity
#print axioms target_inverse_parity
#print axioms target_inverse_mod_two

end TargetQuadratic

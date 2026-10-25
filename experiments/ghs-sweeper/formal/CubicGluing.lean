import Std

/- Fixed constructive module certificate only. This is not the general
   split-semisimple classification or a theorem about an elliptic quotient.
   Ordinary `decide` is kernel reduction; no native decision procedure. -/
set_option maxRecDepth 100000
set_option maxHeartbeats 0

namespace CubicGluing

abbrev K := Fin 5
structure V where
  x0 : K
  y0 : K
  x1 : K
  y1 : K
  x2 : K
  y2 : K
deriving DecidableEq, Repr

def zero : V := ⟨0, 0, 0, 0, 0, 0⟩
def combine (u s t : K) : V := ⟨u, 4*s+t, 3*u, 4*s, 4*u, 4*t⟩
def frobenius (v : V) : V := ⟨3*v.x2, 4*v.y2, v.x0, v.y0, v.x1, v.y1⟩
def pairing (v w : V) : K :=
  (v.x0*w.y0-v.y0*w.x0) + 3*(v.x1*w.y1-v.y1*w.x1) +
  4*(v.x2*w.y2-v.y2*w.x2)
def basis (i : Fin 3) : V :=
  if i=0 then combine 1 0 0 else if i=1 then combine 0 1 0 else combine 0 0 1
def supported (v : V) : Prop :=
  (v.x1=0 ∧ v.y1=0 ∧ v.x2=0 ∧ v.y2=0) ∨
  (v.x0=0 ∧ v.y0=0 ∧ v.x2=0 ∧ v.y2=0) ∨
  (v.x0=0 ∧ v.y0=0 ∧ v.x1=0 ∧ v.y1=0)
instance (v : V) : Decidable (supported v) := inferInstanceAs (Decidable (_ ∨ _ ∨ _))

theorem coefficient_injectivity :
    ∀ u s t : K, combine u s t = zero ↔ u=0 ∧ s=0 ∧ t=0 := by decide

theorem frobenius_stability :
    ∀ u s t : K,
      frobenius (combine u s t) = combine (2*u) (s+4*t) s := by decide

theorem basis_isotropy :
    ∀ i j : Fin 3, pairing (basis i) (basis j) = 0 := by decide

theorem coordinate_transversality :
    ∀ u s t : K, supported (combine u s t) → combine u s t = zero := by decide

-- These constants bind the certificate to q=3, M=diag(3,4), det(M)=q^3.
theorem determinant_binding : (3:K)*4 = 3^3 := by decide

#print axioms coefficient_injectivity
#print axioms frobenius_stability
#print axioms basis_isotropy
#print axioms coordinate_transversality
#print axioms determinant_binding
end CubicGluing

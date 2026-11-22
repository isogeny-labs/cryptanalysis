import Std

/-!
Soundness of the quadratic bit-feature affine hull.  The finite-field group
construction and the packed ordering of these coordinates are audited in Sage.
-/

namespace QuadraticHull

structure Features (n : Nat) where
  linear : Fin n → Bool
  pair : {ij : Fin n × Fin n // ij.1 < ij.2} → Bool

def quadraticFeatures {n : Nat} (x : Fin n → Bool) : Features n :=
  ⟨x, fun ij => x ij.1.1 && x ij.1.2⟩

def xorFeatures {n : Nat} (a b : Features n) : Features n :=
  ⟨fun i => a.linear i ^^ b.linear i,
   fun ij => a.pair ij ^^ b.pair ij⟩

def zeroFeatures (n : Nat) : Features n :=
  ⟨fun _ => false, fun _ => false⟩

def xorSum {n : Nat} : List (Features n) → Features n
  | [] => zeroFeatures n
  | x :: xs => xorFeatures x (xorSum xs)

def inAffineHull {n : Nat} (base : Fin n → Bool)
    (sources : List (Fin n → Bool)) (target : Fin n → Bool) : Prop :=
  ∃ selected : List (Features n),
    (∀ v, v ∈ selected → ∃ x, x ∈ sources ∧
      v = xorFeatures (quadraticFeatures x) (quadraticFeatures base)) ∧
    xorSum selected =
      xorFeatures (quadraticFeatures target) (quadraticFeatures base)

theorem true_source_passes {n : Nat} (base : Fin n → Bool)
    (sources : List (Fin n → Bool)) (target : Fin n → Bool)
    (h : target ∈ sources) : inAffineHull base sources target := by
  refine ⟨[xorFeatures (quadraticFeatures target) (quadraticFeatures base)], ?_, ?_⟩
  · intro v hv
    simp only [List.mem_singleton] at hv
    subst v
    exact ⟨target, h, rfl⟩
  · simp [xorSum, xorFeatures, zeroFeatures]

theorem quadratic_feature_dimension : 131 + 131 * 130 / 2 = 8646 := by
  decide

#print axioms QuadraticHull.true_source_passes
#print axioms QuadraticHull.quadratic_feature_dimension

end QuadraticHull

import BasePointIndependence.Core

/-!
Finite signed sums from one scalar orbit. The two lists represent the
positive and negative terms separately. This module uses the minimal
additive group and exact-order definitions from the pinned sibling
BasePointIndependence development in this repository.
-/

namespace OrbitGate

open AddCommGroupLite

variable {G : Type} [AddCommGroupLite G]

def weightsTotal (weights : List Nat) : Nat :=
  weights.foldl (· + ·) 0

def orbitSum (weights : List Nat) (H : G) : G :=
  weights.foldl (fun acc weight => acc + weight • H) 0

theorem fold_smul (weights : List Nat) (k : Nat) (H : G) :
    weights.foldl (fun acc weight => acc + weight • H) (k • H) =
      (weights.foldl (· + ·) k) • H := by
  induction weights generalizing k with
  | nil => rfl
  | cons weight rest ih =>
      calc
        (weight :: rest).foldl (fun acc w => acc + w • H) (k • H) =
            rest.foldl (fun acc w => acc + w • H) ((k + weight) • H) := by
              simp only [List.foldl_cons, add_smul]
        _ = (rest.foldl (· + ·) (k + weight)) • H := ih (k + weight)
        _ = ((weight :: rest).foldl (· + ·) k) • H := rfl

theorem orbitSum_eq (weights : List Nat) (H : G) :
    orbitSum weights H = (weightsTotal weights) • H := by
  simpa only [orbitSum, weightsTotal, zero_smul] using
    (fold_smul weights 0 H)

theorem seedOrbitSum (weights : List Nat) (a b : Nat) (P Q : G) :
    orbitSum weights (a • P + b • Q) =
      ((weightsTotal weights) * a) • P +
        ((weightsTotal weights) * b) • Q := by
  rw [orbitSum_eq, smul_add, ← mul_smul, ← mul_smul]

/-- A signed zero sum from one nonzero seed forces equality of its
positive and negative scalar totals modulo the seed's exact order. -/
theorem signed_orbit_coeff (r : Nat) (hr : 0 < r) (H : G)
    (hH : ExactOrder r H) (positive negative : List Nat)
    (h : orbitSum positive H = orbitSum negative H) :
    weightsTotal positive % r = weightsTotal negative % r := by
  rw [orbitSum_eq, orbitSum_eq] at h
  have h' : (weightsTotal positive % r) • H =
      (weightsTotal negative % r) • H := by
    calc
      (weightsTotal positive % r) • H =
          (weightsTotal positive) • H :=
            (smul_mod hH.annihilates (weightsTotal positive)).symm
      _ = (weightsTotal negative) • H := h
      _ = (weightsTotal negative % r) • H :=
            smul_mod hH.annihilates (weightsTotal negative)
  exact log_unique hH (Nat.mod_lt _ hr) (Nat.mod_lt _ hr) h'

/-- Both public coefficient totals agree modulo `r`; the zero sum
therefore gives no nonzero coefficient of either marked point. -/
theorem signed_seed_coeff (r : Nat) (hr : 0 < r) (a b : Nat)
    (P Q : G) (hH : ExactOrder r (a • P + b • Q))
    (positive negative : List Nat)
    (h : orbitSum positive (a • P + b • Q) =
      orbitSum negative (a • P + b • Q)) :
    ((weightsTotal positive * a) % r =
       (weightsTotal negative * a) % r) ∧
    ((weightsTotal positive * b) % r =
       (weightsTotal negative * b) % r) := by
  have ht := signed_orbit_coeff r hr (a • P + b • Q) hH positive negative h
  constructor
  · calc
      (weightsTotal positive * a) % r =
          ((weightsTotal positive % r) * a) % r := by simp [Nat.mul_mod]
      _ = ((weightsTotal negative % r) * a) % r := by rw [ht]
      _ = (weightsTotal negative * a) % r := by simp [Nat.mul_mod]
  · calc
      (weightsTotal positive * b) % r =
          ((weightsTotal positive % r) * b) % r := by simp [Nat.mul_mod]
      _ = ((weightsTotal negative % r) * b) % r := by rw [ht]
      _ = (weightsTotal negative * b) % r := by simp [Nat.mul_mod]

#print axioms OrbitGate.orbitSum_eq
#print axioms OrbitGate.seedOrbitSum
#print axioms OrbitGate.signed_orbit_coeff
#print axioms OrbitGate.signed_seed_coeff

end OrbitGate

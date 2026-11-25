import BasePointIndependence.Core

/-!
Finite zero-sum witnesses are invariant when the same labelled point base is
transported through an injective additive map. The elliptic-curve instance
uses a prime-to-subgroup-order isogeny restricted to the rational subgroup;
that separate geometric hypothesis is not asserted by this group proof.
-/

namespace TransportGate

open AddCommGroupLite

variable {G H : Type} [AddCommGroupLite G] [AddCommGroupLite H]

def sumList : List G → G
  | [] => 0
  | x :: xs => x + sumList xs

theorem map_sum (f : G → H)
    (hzero : f 0 = 0) (hadd : ∀ x y, f (x + y) = f x + f y)
    (xs : List G) :
    sumList (xs.map f) = f (sumList xs) := by
  induction xs with
  | nil =>
      exact hzero.symm
  | cons x xs ih =>
      change f x + sumList (xs.map f) = f (x + sumList xs)
      rw [ih, hadd]

theorem relation_iff (f : G → H)
    (hzero : f 0 = 0) (hadd : ∀ x y, f (x + y) = f x + f y)
    (hinj : Function.Injective f) (xs : List G) (R : G) :
    sumList xs = R ↔ sumList (xs.map f) = f R := by
  rw [map_sum f hzero hadd xs]
  constructor
  · intro h
    exact congrArg f h
  · intro h
    exact hinj h

theorem zero_relation_iff (f : G → H)
    (hzero : f 0 = 0) (hadd : ∀ x y, f (x + y) = f x + f y)
    (hinj : Function.Injective f) (xs : List G) :
    sumList xs = 0 ↔ sumList (xs.map f) = 0 := by
  simpa only [hzero] using relation_iff f hzero hadd hinj xs 0

theorem signed_relation_iff (f : G → H)
    (hzero : f 0 = 0) (hadd : ∀ x y, f (x + y) = f x + f y)
    (hinj : Function.Injective f) (positive negative : List G) :
    sumList positive = sumList negative ↔
      sumList (positive.map f) = sumList (negative.map f) := by
  rw [map_sum f hzero hadd positive,
      map_sum f hzero hadd negative]
  constructor
  · intro h
    exact congrArg f h
  · intro h
    exact hinj h

#print axioms TransportGate.map_sum
#print axioms TransportGate.relation_iff
#print axioms TransportGate.zero_relation_iff
#print axioms TransportGate.signed_relation_iff

end TransportGate

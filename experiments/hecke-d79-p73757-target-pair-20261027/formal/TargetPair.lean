module

public import Init

namespace TargetPair
public theorem pair_transport {G H : Type}
    (addG : G → G → G) (negG : G → G)
    (addH : H → H → H) (negH : H → H)
    (φ : G → H) (B1 B4 Q : G)
    (map_add : ∀ x y, φ (addG x y) = addH (φ x) (φ y))
    (map_neg : ∀ x, φ (negG x) = negH (φ x))
    (pair_relation : Q = addG (negG B1) B4) :
    φ Q = addH (negH (φ B1)) (φ B4) := by
  rw [pair_relation, map_add, map_neg]
public def firstLog : Nat := 163
public def secondLog : Nat := 50
public def recovered : Nat := 86
public theorem scalar_certificate : ((199 - firstLog) + secondLog) % 199 = recovered := by decide
#print axioms pair_transport
#print axioms scalar_certificate
end TargetPair

module

public import Init

namespace FourTermCoverage
public theorem four_transport {G H : Type}
    (addG : G → G → G) (addH : H → H → H) (φ : G → H)
    (B0 B1 B2 B3 Q : G)
    (map_add : ∀ x y, φ (addG x y) = addH (φ x) (φ y))
    (relation : Q = addG (addG (addG B0 B1) B2) B3) :
    φ Q = addH (addH (addH (φ B0) (φ B1)) (φ B2)) (φ B3) := by
  rw [relation, map_add, map_add, map_add]
#print axioms four_transport

public theorem residual_0 : ((-1069) + (1243) + (-2385) + (-1)) % 2531 = 319 := by decide
#print axioms residual_0
public theorem residual_1 : ((1657) + (-1069) + (2266) + (-1)) % 2531 = 322 := by decide
#print axioms residual_1
public theorem residual_2 : ((1657) + (1243) + (54) + (-1)) % 2531 = 422 := by decide
#print axioms residual_2
public theorem residual_3 : ((1657) + (-1161) + (54) + (-1)) % 2531 = 549 := by decide
#print axioms residual_3
public theorem residual_4 : ((1657) + (-169) + (-874) + (-1)) % 2531 = 613 := by decide
#print axioms residual_4
public theorem residual_5 : ((1069) + (2385) + (-146) + (-1)) % 2531 = 776 := by decide
#print axioms residual_5
public theorem residual_6 : ((1069) + (2306) + (-37) + (-1)) % 2531 = 806 := by decide
#print axioms residual_6
public theorem residual_7 : ((1657) + (-1069) + (-2306) + (-1)) % 2531 = 812 := by decide
#print axioms residual_7
public theorem residual_8 : ((-1161) + (2266) + (-265) + (-1)) % 2531 = 839 := by decide
#print axioms residual_8
public theorem residual_9 : ((1069) + (2385) + (22) + (-1)) % 2531 = 944 := by decide
#print axioms residual_9
public theorem residual_10 : ((1069) + (-2394) + (2306) + (-1)) % 2531 = 980 := by decide
#print axioms residual_10
public theorem residual_11 : ((1657) + (215) + (-874) + (-1)) % 2531 = 997 := by decide
#print axioms residual_11
public theorem residual_12 : ((-1161) + (2394) + (-169) + (-1)) % 2531 = 1063 := by decide
#print axioms residual_12
public theorem residual_13 : ((1657) + (2266) + (2394) + (-1)) % 2531 = 1254 := by decide
#print axioms residual_13
public theorem residual_14 : ((1069) + (-1161) + (1370) + (-1)) % 2531 = 1277 := by decide
#print axioms residual_14
public theorem residual_15 : ((1657) + (2306) + (37) + (-1)) % 2531 = 1468 := by decide
#print axioms residual_15
public theorem residual_16 : ((1657) + (834) + (1575) + (-1)) % 2531 = 1534 := by decide
#print axioms residual_16
public theorem residual_17 : ((-1243) + (-2266) + (2530) + (-1)) % 2531 = 1551 := by decide
#print axioms residual_17
public theorem residual_18 : ((1657) + (-215) + (-2385) + (-1)) % 2531 = 1587 := by decide
#print axioms residual_18
public theorem residual_19 : ((-1657) + (2394) + (-1575) + (-1)) % 2531 = 1692 := by decide
#print axioms residual_19
public theorem residual_20 : ((1657) + (232) + (-169) + (-1)) % 2531 = 1719 := by decide
#print axioms residual_20
public theorem residual_21 : ((1657) + (215) + (2385) + (-1)) % 2531 = 1725 := by decide
#print axioms residual_21
public theorem residual_22 : ((-215) + (-561) + (-2530) + (-1)) % 2531 = 1755 := by decide
#print axioms residual_22
public theorem residual_23 : ((1657) + (-2306) + (37) + (-1)) % 2531 = 1918 := by decide
#print axioms residual_23
public theorem residual_24 : ((2385) + (2266) + (2394) + (-1)) % 2531 = 1982 := by decide
#print axioms residual_24
public theorem residual_25 : ((-215) + (-37) + (-169) + (-1)) % 2531 = 2109 := by decide
#print axioms residual_25
public theorem residual_26 : ((1161) + (215) + (834) + (-1)) % 2531 = 2209 := by decide
#print axioms residual_26
public theorem residual_27 : ((-2385) + (-232) + (2299) + (-1)) % 2531 = 2212 := by decide
#print axioms residual_27

end FourTermCoverage

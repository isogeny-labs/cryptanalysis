import Std

namespace W29AdviceThreshold

def subgroupOrder : Nat := 680564733841876926932320129493409985129
def signedStateCeiling : Nat := 4 * 2^28
def orderedPairCeiling : Nat := signedStateCeiling * signedStateCeiling
def projectedSignedStates : Nat := 4 * 68308992
def projectedOrderedPairs : Nat := projectedSignedStates * projectedSignedStates

theorem sixtyEightBitsInsufficient :
    2 * (2^68) * orderedPairCeiling < subgroupOrder := by
  decide

theorem sixtyNineBitsCrossArithmeticThreshold :
    subgroupOrder ≤ 2 * (2^69) * orderedPairCeiling := by
  decide

/-- Under the exact W29 mask-capacity ceiling, 43 advice bits and
    twenty million fixed proposals cannot make the counting upper bound
    reach one half. -/
theorem fortyThreeBitsInsufficient :
    2 * (2^43) * 20000000 * orderedPairCeiling < subgroupOrder := by
  decide

theorem fortyFourBitsCrossArithmeticThreshold :
    subgroupOrder ≤ 2 * (2^44) * 20000000 * orderedPairCeiling := by
  decide

theorem twentyEightBitsInsufficient :
    2 * (2^28) * 600000000000 * orderedPairCeiling < subgroupOrder := by
  decide

theorem twentyNineBitsCrossArithmeticThreshold :
    subgroupOrder ≤ 2 * (2^29) * 600000000000 * orderedPairCeiling := by
  decide

/-- The sample-rate projection is a conditional arithmetic instance.
    It is not a census of the actual W29 source. -/
theorem projectedFortySevenBitsInsufficient :
    2 * (2^47) * 20000000 * projectedOrderedPairs < subgroupOrder := by
  decide

theorem projectedFortyEightBitsCrossArithmeticThreshold :
    subgroupOrder ≤ 2 * (2^48) * 20000000 * projectedOrderedPairs := by
  decide

theorem projectedSeventyOneBitsInsufficient :
    2 * (2^71) * projectedOrderedPairs < subgroupOrder := by
  decide

theorem projectedSeventyTwoBitsCrossArithmeticThreshold :
    subgroupOrder ≤ 2 * (2^72) * projectedOrderedPairs := by
  decide

theorem projectedThirtyTwoBitsInsufficient :
    2 * (2^32) * 600000000000 * projectedOrderedPairs < subgroupOrder := by
  decide

theorem projectedThirtyThreeBitsCrossArithmeticThreshold :
    subgroupOrder ≤ 2 * (2^33) * 600000000000 * projectedOrderedPairs := by
  decide

#print axioms sixtyEightBitsInsufficient
#print axioms sixtyNineBitsCrossArithmeticThreshold
#print axioms fortyThreeBitsInsufficient
#print axioms fortyFourBitsCrossArithmeticThreshold
#print axioms twentyEightBitsInsufficient
#print axioms twentyNineBitsCrossArithmeticThreshold
#print axioms projectedFortySevenBitsInsufficient
#print axioms projectedFortyEightBitsCrossArithmeticThreshold
#print axioms projectedSeventyOneBitsInsufficient
#print axioms projectedSeventyTwoBitsCrossArithmeticThreshold
#print axioms projectedThirtyTwoBitsInsufficient
#print axioms projectedThirtyThreeBitsCrossArithmeticThreshold
end W29AdviceThreshold

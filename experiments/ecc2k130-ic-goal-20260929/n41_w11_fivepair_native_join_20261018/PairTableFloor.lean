import Std

namespace PairTableFloor

/-- If a compatible ordered-pair table retains all but at most two
orientations for each of the 2,093 colliding unordered code pairs, then
even 16 key bytes per retained pair exceed four GiB. -/
theorem storage_floor_from_count
    (compatible keyBytes : Nat)
    (pair_bound : compatible + 2 * 2093 ≥ 132045 * (132045 - 1))
    (bytes_bound : keyBytes ≥ 16 * compatible) :
    keyBytes > 4 * 1024 ^ 3 := by
  omega

theorem exact_key_floor :
    16 * (132045 * (132045 - 1) - 2 * 2093) = 278971932704 := by
  decide

#print axioms PairTableFloor.storage_floor_from_count
#print axioms PairTableFloor.exact_key_floor

end PairTableFloor

import ArchiveData
import ArchiveRoots

namespace M31ArchiveMembershipWitness

-- The first accepted row in v2_batch_seed0.relations.jsonl uses signs (+1,+1)
-- and zero-based indices 3 and 10. Certify the distinct-x chord equations and
-- nonmembership of its x coordinate in both archived lists.
theorem first_row :
    let p := 2147483647
    let (a,b) := M31ArchiveData.archived[3]!
    let (c,e) := M31ArchiveData.archived[10]!
    let m := 412957247
    let x := 1322330102
    a < c ∧ c < p ∧ (m*(c-a) + b) % p = e ∧
      (x+a+c) % p = m^2 % p ∧ x < p ∧
      x ∉ M31ArchiveRoots.roots ∧ x ∉ M31ArchiveData.archived.map Prod.fst := by
  decide +kernel

end M31ArchiveMembershipWitness

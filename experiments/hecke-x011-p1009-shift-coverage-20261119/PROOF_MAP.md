# Proof map

| Result | Lean declaration | Exact hypotheses | Verification |
| --- | --- | --- | --- |
| A prepared log transports through an additive shift hit | `X011Target.shift_recovery` in `../hecke-x011-p1009-one-target-20261119/formal/ShiftRecovery.lean` | Additive commutative group, integers `k,l`, `P=l•G`, `Q+k•G=P` | Built and axiom audited in the preceding experiment; `propext` |
| Every p1009 group point hits the prepared fiber within 49 shifts | none | Specific 11a1 model over `F_1009`, order-1020 generator, frozen 84-point fiber | Complete 1020-entry enumeration; independently replayed with Sage; concrete Lean curve bridge open |
| Mean `11189/1020` and target percentile `508/1020` | none | Same frozen prepared set and shift orientation | Integer distance vector, histogram and cyclic-gap identity; independent Sage replay; Lean finite histogram bridge open |

The finite numerical statements rely on the explicit p1009 point set and group law. Their computational witnesses are retained in `distances.json`, `result.json`, and `audit.json`; the generic shift theorem alone is not used as a substitute for those checks.

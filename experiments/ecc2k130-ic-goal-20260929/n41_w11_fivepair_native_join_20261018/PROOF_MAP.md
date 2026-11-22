# Proof map: public relation and N131 explicit-table floor

For the N41 result, the native solver returns five signed pair-state IDs.
Independent checked Sage reconstructs two source points for each ID,
verifies their folded columns, re-applies the slot Frobenius rotations,
and checks the exact raw curve sum against the frozen public point.
Multiplication by four then gives a nonidentity relation in the subgroup
of order 549,756,390,943. These are computational group-law certificates
recorded in [audit_result.json](audit_result.json); the curve arithmetic
and exact finite-field representation are not formalized in Lean here.

For the storage result, the width-20 source is a subset of the width-33
source because they use the same field and seed and the 19 free source
positions are included in the 32 width-33 positions. There are exactly
132,045 valid width-20 codes. Choosing one pair output per code gives
`n(n−1)` ordered pairs with unequal codes. The independently verified
width-29 table contains 2,093 unordered folded-column collision pairs
over a source that also contains width 20; excluding both orientations of
every such pair removes at most 4,186 ordered pairs. The remaining count
is at least 17,435,745,794. Even a bare 16-byte point key for each needs
278,971,932,704 bytes.

| Result | Lean declaration and exact verification status |
| --- | --- |
| Storage exceeds four GiB from the explicit compatible-pair count and 16-byte keys | `PairTableFloor.storage_floor_from_count` in [PairTableFloor.lean](PairTableFloor.lean); hypotheses retain the count inequality and byte cost; kernel checked. |
| Exact 16-byte-key arithmetic | `PairTableFloor.exact_key_floor`; kernel checked. |
| Width-20 valid-code count, width-29 collision count, source subset, and relation group replay | Frozen prior enumerations and current [projection_result.json](projection_result.json), [audit_result.json](audit_result.json), and [verification_result.json](verification_result.json); independently checked numerically. The finite-set counting bridge and concrete curve model remain open Lean obligations. |

The module uses pinned [Lean 4.34.1](lean-toolchain).
`lean PairTableFloor.lean` returned exit code zero; [lean_check.log](lean_check.log)
records `#print axioms`. The storage implication uses only `propext` and
`Quot.sound`; the exact arithmetic declaration has no axioms. No theorem
contains `sorry`, `admit`, a custom research axiom, or native-evaluation
proof step. `lean4checker --fresh` was unavailable on this host.

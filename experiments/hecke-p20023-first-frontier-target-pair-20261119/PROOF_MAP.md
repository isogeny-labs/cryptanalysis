# Proof map

| Result | Lean declaration | Exact hypotheses | Verification |
| --- | --- | --- | --- |
| A checked shift transports a group log | `ShiftClosure.log_from_generator_shift` in `../hecke-l29-final-kernel-search-20261024/formal/ShiftClosure.lean` | Additive commutative groups, additive homomorphism, `known = unknown + steps•generator` | Built and axiom audited for this experiment; `propext` |
| The 1,760 projected representatives have the archived logs | none here | Exact `F_20023` curve, subgroup generator, frozen source and solved-table digests | Checked by local integer group law and independently by Sage; concrete Lean bridge open |
| New target is outside the table and needs two shifts | none here | Frozen hash target law and prepared table | Public point, separate fixture, least-shift check and independent Sage replay; concrete Lean bridge open |
| Connector and rho answers are 495 | structural shift theorem for connector; no rho theorem here | Same public point and order-4021 subgroup | Both scalar replays checked independently in Sage; concrete Lean bridge open |

The structural theorem supplies the algebraic recovery rule. It does not certify the finite table, target selection, or measured intervals; those are preserved and independently replayed as separate evidence. `lean4checker --fresh` was unavailable on this host.

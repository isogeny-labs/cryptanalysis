# Proof map

This experiment introduces an incremental search implementation and a bounded measurement, with no new mathematical theorem. The exact first-code partition used by the implementation is the previously checked `CubePartition.exactAllowedPartition` theorem in [CubePartition.lean](../n41_public_code_cube_20261017/CubePartition.lean). It quantifies over Boolean assignments and allowed code lists: an assignment satisfying the forbidden-code clauses belongs to exactly one complete allowed-code cube. The pinned Lean 4.34.1 build and `#print axioms` output are in the prior [proof log](../n41_public_code_cube_20261017/lean_build.stdout); the reported foundations are `propext`, `Classical.choice`, and `Quot.sound`.

| Bridge to this implementation | Evidence |
| --- | --- |
| The 40-code order is exactly the prior allowed first-slot partition | `verify.py` compares `codes.tsv`, `protocol_v2.json`, and the previous frozen partition protocol |
| Assumptions apply to the seven archived first-slot wires | `codes.tsv` is bound to the prior `wires.json` by `freeze.py`; `verify.py` checks the wire and code order, and the archived formula hash |
| The C API parser loaded the exact public formula | `incremental.cpp` checks header and record counts; `verify.py` checks the formula, source, binary, library, run protocol, and raw `LOADED` line hashes |
| The known relation lies in code 6 of this same formula | The prior `witness_control.py` checks all 82,957 clauses and 3,689 XOR rows, and `verify.py` checks that witness receipt and formula hash |
| Each measured call used one solver instance with code assumptions | `incremental.cpp`, frozen binary digest, one `LOADED` line, and 40 ordered `CODE` lines in `full_v2.stdout` |

The partition theorem establishes exhaustive coverage of the first code. The solver's bounded `UNKNOWN` statuses are empirical observations under the recorded limits.

# Proof map

| Result | Evidence | Status |
| --- | --- | --- |
| Triple Frobenius transport and target lookup equivalence | `FoldedJoin.right_triple_from_left` and `FoldedJoin.folded_target_lookup` in `../n41_frobenius_folded_join_20261016/FoldedJoin.lean`, Lean 4.34.1 `#print axioms` | Checked previously without axioms; mathematical statement unchanged |
| Pointwise concrete source correspondence and twelve-column witness | `audit.py`, `audit_result.json`, frozen 960-row source | Independently replayed in this experiment |
| Pointer entries remain valid through probing | `pointer.cpp`: hash-table reserve precedes insertion, entries are never erased, and the vector stores addresses of hash-table elements; C++ unordered-container element references and pointers remain valid across insertion and rehash | Source-level implementation argument; same six-run output and hit replay check behavior on frozen input |
| Recorded run integrity | `verify.py`, `terminal.json`, protocol and result SHA-256 | PASS |

This experiment changes a data structure, not the algebraic theorem. The concrete field/curve bridge remains outside Lean and is covered by the independent finite replay. The N131 source-family compression needed for the goal remains an open algorithmic obligation.

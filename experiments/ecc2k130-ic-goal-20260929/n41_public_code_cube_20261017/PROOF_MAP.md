# Proof map

`CubePartition.exactAllowedPartition` in `CubePartition.lean` states that an
assignment surviving every forbidden seven-bit code clause belongs to the
allowed list and matches exactly one complete seven-bit cube. It quantifies
over any allowed list and all Boolean assignments. Lean 4.34.1 built the
theorem; `lean_build.stdout` records its `#print axioms` result:
`propext`, `Classical.choice`, and `Quot.sound`.

| Bridge to the measured circuit | Evidence |
| --- | --- |
| The 40 numeric codes are exactly the canonical N41 permitted pair codes | `verify.py` recomputes them from archived geometry and compares the frozen `protocol.json` order |
| Every one of the other 88 seven-bit patterns has its exclusion clause in the public formula | `verify.py` checks the literal clause for each pattern against `rebuilt_public.xcnf` |
| The first-slot wires refer to the exact archived public-target circuit | `freeze.py` rebuilds the XCNF and requires SHA-256 equality to the archived formula; `wires.json` records the builder's wire IDs |
| Each queried cube is that public formula plus exactly seven units for its code | `verify.py` regenerates all 40 byte strings, compares their full contents and hashes, and audits parser/search logs |
| The archived six-pair relation gives a satisfying assignment in one queried cube | `witness_control.py` checks every public formula clause and XOR row with the independently replayed relation, after the campaign was frozen and completed |

The theorem covers logical partitioning. It does not assert that bounded SAT
search resolves any cube. Solver statuses and the control assignment are
separate evidence.

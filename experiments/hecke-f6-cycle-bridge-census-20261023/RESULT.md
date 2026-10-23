# Splitting of 3 predicts three projected Hecke operators on the saved conductor-6 walks

Across all 14 frozen `f = 6`, degree-`{2,3}` class-walk outputs in this workspace, the quadratic field's behavior at 3 separates the conductor-2 degree-3 projected rows into **three exact operators**. The complete saved outputs comprise eleven verified operator bridges: one inert class with singleton identity blocks, five ramified outputs with two-point `I+P` blocks, and five split outputs with `I+P+P⁻¹` cycle blocks. One output has an empty class, and two older outputs have a missing neighbor in their saved class. Every case remains in the census.

| `3` in the CM field | Horizontal neighbors in each audited row | Projected block | Rational kernel per block | Complete saved outputs |
| --- | ---: | --- | ---: | ---: |
| Inert | 0 | `[1]` | 0 | 1 |
| Ramified | 1 | `[[1,1],[1,1]]` | 1 | 5 |
| Split | 2 | `I+P+P⁻¹` on a cycle of length `n` | 2 if `3 | n`, else 0 | 5 |

The horizontal-neighbor count `0,1,2` and the ideal-class cycles in the split case are the ordinary CM isogeny-volcano structure described in [Sutherland, *Isogeny volcanoes*, §§2.8–2.9](https://msp.org/obs/2013/1-1/obs-v1-n1-p25-s.pdf). For the conductor-2 source order here, 3 does not divide its conductor. The signed coefficient in these `X₀(11)` Hecke rows is also essential: `a₃ = −1`, so moving `a₃ P` to the row side contributes `+P`. The saved matrices confirm the remaining nonfloor entries are exactly the horizontal neighbors, with all other entries on the conductor-6 floor.

| Saved discriminant and field | Type at 3 | Complete projected components | Kernel dimensions |
| --- | --- | --- | --- |
| `D = −127`, `p = 1399` | inert | 10 singletons | all 0 |
| `D = −87`, `p = 787` | ramified | 6 pairs | all 1 |
| `D = −39`, `p = 367` | ramified | 4 pairs | all 1 |
| `D = −183`, `p = 1663` | ramified | 8 pairs | all 1 |
| `D = −1407`, `p = 12763` regularized and `p = 20407` | ramified | 24 pairs in each field | all 1 |
| `D = −215`, `p = 2131` regularized | split | 2 cycles of length 14 | 0, 0 |
| `D = −431`, `p = 12343` | split | 2 cycles of length 21 | 2, 2 |
| `D = −527`, `p = 11467` | split | 2 cycles of length 18 | 2, 2 |
| `D = −623`, `p = 11083` | split | 2 cycles of length 22 | 0, 0 |
| `D = −1055`, `p = 10651` | split | 2 cycles of length 36 | 2, 2 |

`freeze_inputs.py` hashed all 14 files before the audit. The first script, retained as `audit_initial.py` with `audit_initial.json`, tested only the split-cycle form and recorded five passes, eight partial cases and one empty class. `revision_protocol.json` then froze the inert/ramified/split interpretation before a revised replay. The checked-Sage `audit.py` reconstructed every saved point, endomorphism conductor and relevant degree-3 Hecke row. It matched each reconstructed row to a saved matrix row, checked the elliptic-curve group sum, found the horizontal graph, and computed exact rational component ranks. The revised outcome is eleven complete passes, two incomplete legacy walks, and one empty class. The two incomplete files are the original `D = −1407` and `D = −215` outputs; each has one source whose neighbor is absent from the saved class. Their repaired or fresh counterparts pass.

`validate.py` independently checks every frozen file hash, enumerates the conductor-2 class numbers from reduced quadratic forms, replays saved row indices and component matrices, and checks their ranks by separate dense elimination modulo 1000000007. The [Lean component module](/Volumes/SSD990/cryptanalysis/experiments/hecke-f6-cycle-bridge-census-20261023/formal/HorizontalOperators.lean) proves the singleton kernel is zero and the pair kernel has one unique rational parameter, with a nonzero witness; its compiled module and axiom audit are recorded in [build.json](/Volumes/SSD990/cryptanalysis/experiments/hecke-f6-cycle-bridge-census-20261023/formal/build.json). The split-cycle kernel classification is proved in the earlier [general Lean module](/Volumes/SSD990/cryptanalysis/experiments/hecke-cycle-rank-theorem-20261023/formal/GeneralCycleKernel.lean).

This supplies the missing case distinction for the **saved** conductor-6 Hecke matrices. The literature establishes the horizontal isogeny count and ideal-class action on elliptic-curve `j`-invariants; a general proof that their rational `X₀(11)` lifts and explicit Hecke rows preserve precisely these projected blocks remains an open bridge. The two incomplete outputs also show why a class-size or row-count receipt alone cannot certify the block structure. This is a relation-stage diagnostic with `candidate_id: null` and `timing_claim: null`.

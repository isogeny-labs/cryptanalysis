# Four signed 14-row cycles span the D = −215 floor kernel

The regularized D = −215, conductor-6 Hecke matrix has a **four-dimensional floor-only row space**, and this experiment identifies an integer basis for it. Its 56 degree-2 rows sourced at conductor 3 form four connected signed incidence components of 14 rows each. Alternating the row signs in each component cancels every nonfloor coordinate and leaves a vector with 14 coefficients in `{−1,1}` on conductor-6 columns. The four floor supports are disjoint and partition all 56 conductor-6 columns. The saved exact ranks are 112 for the full row space and 108 after nonfloor projection, so the four independent vectors span the full projection kernel.

The order-class computation supplies a matching conditional explanation of the component count. For discriminants `−215`, `−860`, `−1935`, and `−7740`, the class numbers are 14, 14, 28, and 28. The norm-2 ideal class in the conductor-3 order has order 14. If its action lifts separately to the two rational X₀(11) sheets, 56 parent points split into `2·28/14 = 4` length-14 orbits. The matrix audit independently finds exactly those four components and checks their signed row sums. The sheet-action identification remains a separate uniform proof obligation.

| Checked object | Result |
| --- | ---: |
| Conductor-3 degree-2 rows | 56 |
| Signed components | 4 of length 14 |
| Nonfloor terms in each signed sum | 0 |
| Distinct floor columns per sum | 14 |
| Floor columns covered once | 56 |
| Full / nonfloor projected rank over ℚ | 112 / 108 |
| Conductor-2 degree-3 rows with distinct lower signatures | 28 / 28 |

## Proof and formalization boundary

Let `R ⊆ ℚ¹⁶⁸` be the saved row space and `π` the coordinate projection onto the 112 nonfloor columns. The exact matrix audit gives `dim R = 112` and `dim π(R) = 108`; rank-nullity therefore gives `dim ker(π|R) = 4`. Each of the four recorded signed row combinations lies in that kernel by exact integer cancellation. Their nonempty disjoint floor supports make them linearly independent: evaluate a zero linear combination at one support coordinate from each vector. Four independent vectors in a four-dimensional kernel form a basis.

`formal/FloorKernel.lean` contains the faithful coordinate-separation implication and four concrete 168-coordinate vectors generated from `floor_structure.json`. Lean `v4.35.0-rc4` with pinned Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` builds the module; `#print axioms` reports only `propext`, `Classical.choice`, and `Quot.sound`. The proof map is:

| Mathematical step | Lean declaration or evidence | Status |
| --- | --- | --- |
| Disjoint witness coordinates force four coefficients to vanish | `FloorKernel.separating_coordinates` | Kernel-checked |
| The four saved vectors have such witnesses | `FloorKernel.concrete_certificates_independent`; generator receipt | Kernel-checked |
| Each vector is a signed combination of saved rows and cancels below the floor | `floor_structure.json`; independent integer replay in `validation.json` | Checked externally; Lean bridge open |
| Full row rank 112 and projected rank 108 | `exact_rank.json` from checked Sage | Checked externally; Lean matrix-rank bridge open |
| The four vectors span this specific floor kernel | Written rank-nullity proof plus the two preceding receipts | Formalization partial |

The first attempt to import Mathlib's full finite-dimensional submodule API failed because the pinned local cache lacks a compiled `Mathlib.Algebra.Algebra.Bilinear` dependency; `formal/attempt-full-span-failed.txt` preserves that build error. The narrower concrete independence module builds and contains no `sorry`, `admit`, custom axioms, or native-evaluation proof. `lean4checker --fresh` was unavailable. A complete Lean formalization would encode the saved row matrix and projection, prove the four integer row identities, and certify their rational ranks or an equivalent exact elimination witness.

`protocol.json` froze the D = −215 source hashes and the previously measured floor-kernel rank before this structural audit. `class_action.py` computes order-class data through the checked repository Sage launcher. `floor_structure.py` emits the four signed row certificates; `validate.py` independently replays every coefficient from the saved matrix and checks the Lean-generation digests. The experiment remains a relation-stage diagnostic with `candidate_id: null` and `timing_claim: null`. The next discriminant test should freeze the class-action orbit prediction for another split-degree-3 conductor-6 class before running its producer.

Run Sage through `/Volumes/SSD990/cryptanalysis/sage`; run the Lean module from `formal/` with `lake env lean FloorKernel.lean`. `SEAL.json` binds all scripts, receipts, and proofs.

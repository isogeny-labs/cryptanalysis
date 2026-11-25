# CT320 — Distinct public-target cold-cost admission (preregistered 2026-11-22)

**Status:** proposed source-only coverage gate; [pcc:unverified]. Continue the existing draft PR #1920 after CT319. No original S3 model is available in this lane.

## Reproducible deficiency and hypothesis

CT315 requires four seven-arm matched cold blocks, but neither CT315 nor CT317/CT318/CT319 requires the **public elliptic-curve target to change between blocks**. The positive mock uses four repetitions of the same tiny `Q=[2]P`. Such a panel could report a provisional advantage even if an executable were specialized to one public target or reused an uncharged answer. This does not prove the actual original solver is cheating.

**Hypothesis:** requiring at least four distinct source-curve group elements `Q`, one per full matched block, removes the specific degenerate repeated-target acceptance while preserving properly matched within-block comparisons. This is not proof of random-blinded challenge generation, cold-cache isolation, independent execution or cryptanalytic speedup.

## Frozen acceptance logic

1. First run the *unchanged* CT319 receipt/cold-cost/group-equation audit on the exact supplied raw panel, public witness, raw-output directory and literal fixture bytes. Abort if any upstream gate fails.
2. Require at least four seven-run blocks and four distinct **actual affine Q coordinates** across the complete panel. Each block must carry one witness target ID, scalar, curve, subgroup and Q; CT315/317 already check all seven agree. Reject a target-ID alias that points to the same Q, too few distinct Q, or an undeclared/unused target. Accept repeated target in later blocks only if at least four distinct Q are present overall; extra repeats must still be cold and paired.
3. Do not identify diversity by distinct target-ID strings alone. Require the set of target IDs associated with each Q to have cardinality one (no aliases). Record number of blocks, distinct Q, distinct scalars, and block-to-target map; do not report a speedup.
4. Source-only tests: (a) CT319's four-block repeated `Q=[2]P` mock **passes CT319 but is refused by CT320**; (b) real independent F97 group arithmetic witnesses for `[1]P,[2]P,[3]P,[4]P` (order-five P) produce four different, correctly recalculated source Q and pass all upstream gates; (c) a four-ID alias fixture pointing to three Q passes CT319 but is refused; (d) a two-Q repetition passes CT319 but is refused. Preserve CT319 positive/negative cost arms and both normal and `-O` execution.
5. Do not change original frozen 695/701 fixtures, CT304/315/317/318/319 validators, provenance pins, solver binaries, AWS/EKS, protected-branch review, or PCC. Avoid speculative speedup claims.

## Residual scientific obligations

Distinct Q is necessary but not sufficient: a target might still be leaked through an unexamined channel, cached across runs, hand-picked or represented by a trapdoored subgroup. A genuine benchmark additionally needs a precommitted target-generation protocol hiding k from every tested solver, source-isolated cold execution, source-to-binary provenance, actual measured C169/C13a/C13b/D/N2_actual and all setup, transfer, LA, recovery and memory charges. Original six-object remote-S3 custody/tool parity and owner-approved STS remain blocked by CT304. Comparison must use the strongest matched rho/BSGS/frontier IC and retained lift, with independent signed PCC. [pcc:unverified]

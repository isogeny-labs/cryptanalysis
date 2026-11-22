# CT184 — cross-stack v2 cold-panel compatibility contract (prospective)

2026-11-17 UTC · [pcc:unverified] · no native execution, no ECDLP solve, no budget admission.

## Prior exact sources and branching

- CT183 producer: [cryptanalysis #1713](https://github.com/isogeny-labs/cryptanalysis/pull/1713), `39c67c946a39cecdd7ed2aa8b2d515711e5adc4c`, stacked on CT178 #1706. Preserve its original 48 selected public packets (Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`) and all 21 counters.
- CT182 v2 offline reader: [cryptanalysis #1711](https://github.com/isogeny-labs/cryptanalysis/pull/1711), immutable pinned commit `92d0c646a757046f8f10a015ae17ce0ed9d0fd2c`, stacked on CT180 #1710 and CT179 #1708. It is **not** merged into the CT183 branch. The test uses a separate read-only, pinned, sparse GitHub Actions checkout so upstream authors can work without duplicate code or branch mutations.
- Original mathematical context: merged [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [selected-call cost #4215](https://github.com/isogeny-labs/crypto/pull/4215) and [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523); active [queue #3904](https://github.com/isogeny-labs/crypto/issues/3904). No new algebraic mechanism or novelty claim. Shared KB service and authenticated 695/701 custody not accessible; this is only a source-level interface check.

## Frozen acceptance test

1. Verify the exact CT183 source Git object and pinned CT182 checkout, original fixed-fixture Git blob, and both independent SHA-256 calculations of the full 2,304-slot roster. Require 48 original packet IDs, 8 blocks per packet, 4 ABBA + 4 BAAB per packet, and A/A controls. Any mismatch fails, never adapts silently.
2. Using a **patched** `bounded.run_sample` that synthesizes canonical CT179 child JSON from the frozen original vectors, execute the real CT183 `run(... --execute --admission-approved ...)` **as code-path simulation**, never invoking its native child. Patch the host identifier stable; use a known local Python executable only for an SHA/path identity check; no cryptocurrency computation, network, EKS, Spot or GPU. A fake flag in a unit test conveys no real-world admission.
3. Feed the **actual panel bytes emitted by CT183**, including real producer manifest, samples and terminal, to the exact pinned CT182 `adjudicate_v2`. Positive synthetic oracle: slot-dependent stationary wall effects are independent of treatment and must yield ratio 1.0 for every stratum. Programmed arm-specific ratio 1.25 must yield 1.25 across strata, with exact A/A controls. These numbers are synthetic only.
4. Fail-closed controls: alter the manifest to v1, corrupt one sample's treatment arm or child digest, truncate terminal, inject invalid clock nesting, and/or cause incomplete producer output. Reader must reject each mutated copy. Neither writer nor reader may report a complete real ECDLP advantage or signed PCC.
5. Run normal Python and `python3 -O -S` tests on the exact pair of checked-out trees; preserve immutable source refs, explicit source-only CI status, and limits. Tests must use `unittest`/exceptions, not security-relevant `assert`. Keep existing main/PR workflows, trust roots, ledgers and artifact gates unchanged.

## Stop and next scientific step

If any source mismatch occurs, preserve failing test output and repair in this isolated feature branch, not in concurrent CT182/183 PR branches. If compatibility passes, move to owner-authorized native Rust compilation + full 48-case arithmetic parity and authenticated 695/701 custody; then same-host actual C169/C13a/C13b/N2_actual/D pricing, matched complete cold prime-field rho/BSGS/IC solves with all setup, transfer, LA, verification, peak memory and uncertainty. Accept speedup **only** on independent signed PCC and complete baseline/candidate >1. This source test does not satisfy those conditions.

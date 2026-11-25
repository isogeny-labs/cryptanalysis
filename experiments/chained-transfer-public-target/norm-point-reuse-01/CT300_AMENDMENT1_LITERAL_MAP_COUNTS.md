# CT300 Amendment 1 — literal CT125 map counts (before source-code repair)

**Registered 2026-11-21, [pcc:unverified].** Supersedes CT300's initial "change only scalar" assumption. The first authentic-fixture source gate [Actions #44982679363](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44982679363), job `137086407754`, ran the exact authentic frozen blob and failed at selected **sample 1**, with `ValueError: sample 1: selected source degree13_elliptic_evaluation differs`. This failure is retained, not waived.

## Mathematical/source diagnosis

The actual CT125 optimized derivative implements the literal sequential route by two `transfer_entry` calls, each evaluating one degree-13 directed gamma and one target norm point doubling. The frozen native CT125 48-vector Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3` records literal `degree13_elliptic_evaluation=2` and `transported_norm_doubling=2` per packet. CT248's **synthetic** `expected_slots()` had retained the **unoptimized pre-CT125** degree-13 call count of four for literal while already accepting the optimized single direct C169 and strongest-retained two C13 calls. That makes genuine CT125 literal samples fail native audit, independent of the CT299 wrong scalar.

## Scoped amendment and negative controls

Fix the CT248/CT300 auditor's literal arm only: for directions `(0,2)` use slots `C13_0_to_1=1`, `C13_1_to_2=1`; for reverse `(2,0)` use `C13_2_to_1=1`, `C13_1_to_0=1`; both directions use `D_target_norm=2`. Direct remains one C169 plus D=1; strongest retained remains two C13 plus D=1. No other fields, gate, scope or source Rust are changed.

Add a source-only regression that explicitly rejects the outdated four-C13 literal pattern and checks the complete authenticated actual48 program, including original full native Calls dictionaries, in Python normal and `-O`. Preserve the initial failed CI receipt and synthetic/test-only clocks. Do not infer physical timing, native compilation, 695/701 replay, or ECDLP speedup. Leave PR draft and do not bypass object-store custody, paid-compute, protected merge or signed PCC gates.

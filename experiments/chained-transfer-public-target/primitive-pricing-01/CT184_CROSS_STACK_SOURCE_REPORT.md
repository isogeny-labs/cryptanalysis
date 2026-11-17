# CT184 — Cross-stack producer/reader compatibility result

2026-11-17 UTC · source/synthetic only · [pcc:unverified]

## Measurable result

- Draft [cryptanalysis PR #1714](https://github.com/isogeny-labs/cryptanalysis/pull/1714) carries an **independent exact-revision** source integration; it stacks only on CT183 [#1713](https://github.com/isogeny-labs/cryptanalysis/pull/1713). The CT182 reader [#1711](https://github.com/isogeny-labs/cryptanalysis/pull/1711) is checked out at immutable SHA `92d0c646a757046f8f10a015ae17ce0ed9d0fd2c`, not copied or altered in this PR.
- [GitHub Actions source workflow #44096935980](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44096935980) completed **success**, job `134086422253`, exact source head `426d21a13272249e2ed762e830d8f81b576b3b5d`. Decoded logs independently confirm 3/3 normal Python tests (2.694s), 3/3 optimized `-O -S` tests (4.631s); all work is synthetic and children are mocked.
- The workflow checked source Git SHA-1 objects for the original 48-packet fixture (`9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`), CT183 producer (`5d6c027b24e2c22fb7e20d94813f55a6569b7ef2`), and CT182 reader (`da70198f0a4b4b673c50f103f02be75da292d115`), plus pinned checkout revision.
- Full **actual CT183 producer serialization** (manifest + 2,304 mocked synthetic child samples + terminal = 2,306 JSONL records) was accepted by exact pinned CT182 reader, preserving the original roster digest `1dddb4839321ad6560fd429330778aa083ff3a13625393250e964c05f9fc5ee4`, original frozen counter values and 16 separate frozen strata.
- Slot-only **synthetic null** produced 1.0 ratio in every stratum, with A/A zero drift and four ABBA/four BAAB packet blocks. Programmed **synthetic 5:4 ratio** produced 1.25 in every stratum. These are test oracles, not measured arithmetic timings or ECDLP improvements.
- The pinned reader refused all five corrupted-panel controls: wrong arm assignment, changed output digest, impossible nested child/external clock, legacy v1 schema and missing terminal.
- All native child calls were mocked; `bounded_subprocess` was explicitly forbidden. No EKS/Spot, GPU or native Rust binary was invoked, and no paid compute or merge bypass occurred.

## Exact reproduction

From the PR head, with the second pinned source checkout made by the workflow:

```bash
root=experiments/chained-transfer-public-target/primitive-pricing-01
export CT182_SOURCE_ROOT="$PWD/ct182-pinned/experiments/chained-transfer-public-target/primitive-pricing-01"
test "$(git -C ct182-pinned rev-parse HEAD)" = 92d0c646a757046f8f10a015ae17ce0ed9d0fd2c
python3 -S -m unittest discover -s "$root" -p test_ct184_cross_stack_v2.py -v
python3 -O -S -m unittest discover -s "$root" -p test_ct184_cross_stack_v2.py -v
```

Source of record: `.github/workflows/ct184-cross-stack-v2-source-gate.yml`; prospective test contract in `CT184_CROSS_STACK_SOURCE_CONTRACT.md`.

## Known blockers, next action and proof status

This settles **only the source interface between a versioned producer and its offline evidence reader**, not underlying native field arithmetic, ECDLP transfer, nor full solve economics. Both modules and these tests were authored in the research pipeline and are not independently signed. [pcc:unverified]

Next scientific task: get authenticated custody for the original 695/701 records, then typecheck the CT125 Rust evaluator, execute all 48 public packet parity cases under owner/provider admission, and run fresh-process paired C169/C13a/C13b/N2_actual/D prices (with unknowns priced, not inferred). Only after this should complete cold single-target prime-field transfer-plus-solve be compared with matched strongest rho, BSGS and index calculus, including setup, inverse, map, memory, LA, recovery, uncertainty, source identity and independently signed PCC. If transfer route is slower, retain the negative result and switch to the next genuine algorithmic lead.

The prior source and negative history remain in [root crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [#4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523) and [queue #3904](https://github.com/isogeny-labs/crypto/issues/3904). Shared research KB unavailable, so no novelty or mathematical obstruction theorem is claimed.

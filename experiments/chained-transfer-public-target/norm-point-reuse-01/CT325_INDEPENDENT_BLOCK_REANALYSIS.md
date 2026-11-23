# CT325 — independent target-block reanalysis of the CT324 cold rho control

2026-11-22 Mountain / 2026-11-23 UTC. **Exploratory, independently recomputed original-record arithmetic; [pcc:unverified].** This is *not* a complete chained-transfer solver, not an independent re-execution of the native ECDLP, and not a signed PCC verdict.

## Original unchanged source and replay

The source was the actual 24-child JSON artifact from [GitHub Actions run 45104053819](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45104053819), [artifact 14786980671](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45104053819/artifacts/14786980671). The archived ZIP was 2811 bytes, SHA-256 `eb095b6d6eb29195ced78751fc6a220999c2765a6b49df9e1e9341e1ae6a56a9` (also present in the actual original upload job log). Its sole file `ct324-panel.json` was 14435 bytes, SHA-256 `0ded77e0a6c955d27383b96d2aff128a680f32436328df199f385fd0ae2a5667`. The original writer's output records only four distinct public target IDs (`ct321-0000`…`0003`), with two fresh cold processes for each of three arms per target.

Separately implemented `ct325_independent_block_audit.py` requires the full original byte digest, exact 24-child schema and ABBA-style positions, four target IDs and per-arm digests, same-public-Q argv/counters, positive OS wall and RSS, and independent recomputation of the eight-child medians, total additions and inversions. Local normal Python and `-O` each accepted the original and rejected all **14** deliberately corrupted semantic panels. An extra changed-byte digest control was refused. These are **record checks**, not independent group-equation/native-execution replay.

Run from the repository root after downloading that artifact (no secrets or paid compute):

```sh
gh run download 45104053819 --repo isogeny-labs/cryptanalysis --name ct324-public-raw-panel --dir /tmp/ct325
sha256sum /tmp/ct325/ct324-panel.json
d=experiments/chained-transfer-public-target/norm-point-reuse-01
python3 -S "$d/ct325_independent_block_audit.py" --panel /tmp/ct325/ct324-panel.json --self-test
python3 -O -S "$d/ct325_independent_block_audit.py" --panel /tmp/ct325/ct324-panel.json
```

## The scientifically relevant unit is the public target, not the child process

Within each block, first take the mean of two wall observations for that same public target/arm. The direction of each ratio is **baseline wall / CT324 wall**; values greater than one favor the batched rho, and values below one favor the previous affine rho or BSGS. All are descriptive single-host values.

| Public target | CT323 affine rho (ms) | CT324 batched rho (ms) | CT323 / CT324 | CT322 BSGS / CT324 |
|---|---:|---:|---:|---:|
| ct321-0000 | 7.104 | 11.910 | **0.596** (CT324 loses) | 1.857 |
| ct321-0001 | 12.480 | 12.293 | **1.015** (near parity) | 2.226 |
| ct321-0002 | 22.379 | 12.293 | **1.821** | 2.258 |
| ct321-0003 | 22.393 | 12.295 | **1.821** | 2.467 |

The reported ratio of *unpaired arm medians*, `17.6181735ms / 12.261483ms = 1.437×`, is arithmetically correct but is **not** the target-matched effect size. The four-block geometric mean of `CT323/CT324` is **1.19036×**, with the enumerated 4^4=256 target-bootstrap percentile interval **[0.77816, 1.82092]**. The 16-pattern one-sided sign-flip sensitivity statistic is **p=0.1875** under its strong independent, symmetric-block null assumptions; this is not confirmatory evidence of superiority.

For `BSGS/CT324`, the matched geometric mean is **2.19047×**, the exploratory four-target percentile interval is **[1.95000, 2.40452]**, and one-sided sign-flip sensitivity is **p=0.0625**. **CT322 is not the strongest BSGS/IC control**; the p values and bootstraps are a small-n sensitivity display, *not independently calibrated confidence intervals* or proof of an asymptotic advantage.

Repeated runs for each Q have identical arithmetic work per arm (for instance target 0000 has 4,603 CT323 steps versus 74,576 CT324 steps, in both respective processes). They represent timing replication, **not eight independent rho collision samples**. Furthermore CT324 changes the distinguished-point threshold from 1/16 to 1/64; walk distributions and stopping times differ. Thus we cannot isolate whether any difference is from batched inversion, changed walk behavior or combined effects. Aggregate new/old additions rise to 606,612/327,580 while inversions fall to 70,766/327,564; none of these counters establishes a full source-to-Jacobian advantage.

The published original all-arm cold medians remain exactly reproduced: CT322 27.539010ms, CT323 17.6181735ms and CT324 12.261483ms; each arm recorded eight children, with median peak RSS 19,140KiB in the parent source. This audit adds a **necessary interpretation correction**: one favorable *marginal median* over an affine reference does not imply a robust, independently repeated per-target speedup.

## Decision and next experiment

**Verdict: retain as an interesting provisional rho-control engineering lead; not a transferred ECDLP win.** Require a prospectively frozen >=16-independent-Q, >=2-host comparison against optimized negation-map/batched/SIMD rho and the existing strongest IC/BSGS frontier, with A/A, public scalar recovery, full cold setup/RSS, same-walk-distribution controls and independent PCC. Never import the 1.437× headline as a qualified baseline/candidate improvement.

For chained transfers, the decisive blocker remains actual original **695/701** authenticated corpus hydration (six S3 objects and approved STS/artifact-tool/config parity), **48 physical `C169/C13a/C13b/N2_actual/D`** matched packet measurements, and full single-target source-to-Jacobian-plus-IC cost against the strongest same-source optimized rho, BSGS and index calculus. The transfer-side generator, Cantor, source lifts, LA, recovery, verification, setup, memory, confidence and signatures must all be counted. Stop on failed admission; never substitute synthetic 694 rows or known-scalar toy fixtures. No paid compute, merge override or credential-policy change was performed.

Source and concurrent-PR checks: [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [#4215](https://github.com/isogeny-labs/crypto/pull/4215), [#4178](https://github.com/isogeny-labs/crypto/pull/4178), [#4715](https://github.com/isogeny-labs/crypto/pull/4715), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [CT315–317 #1912](https://github.com/isogeny-labs/cryptanalysis/pull/1912), active [CT318–324 #1920](https://github.com/isogeny-labs/cryptanalysis/pull/1920), [crypto issue #3904](https://github.com/isogeny-labs/crypto/issues/3904). The separate CT325 PR does not edit the active producer's files. All scientific statements [pcc:unverified].

## Exact-source hosted audit adjudication (2026-11-23 03:57 UTC)

[GitHub Actions CT325 run 45108859889](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45108859889), job `137476347075`, **completed success** on source head `839863e05907cd02e38d4b30cf4c5c2b29f22e58`. Inspected decoded job logs, not only GitHub's status: exact original 14,435-byte JSON SHA-256 passed; 24/24 source rows and parent sums passed; 14 forged schema/counter/value/metadata mutations were refused in normal Python and `-O`; both original-record reanalyses were byte-identical and printed the same four-block ratios, conditional sign-flip statistics and descriptive bootstrap. An additional modified-byte SHA-control was correctly rejected; its deliberate traceback is expected negative evidence, not an unsuccessful job. The [full CI record-only result artifact](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45108859889/artifacts/14788243092) contains the summary and controls. [pcc:unverified]

This success qualifies **source-only independent record computation** on the pinned original uploaded public panel. It executes no original Jacobian transfer, no independently verified raw DLP/reveal, no strongest rho, no S3/native 695 source and no signed PCC. Subsequent updates of this report or task log are documentation-only; do not transfer this workflow conclusion to any changed executable code without another exact-head run.

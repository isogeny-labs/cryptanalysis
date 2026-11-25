# CT202 — prospective order-and-binary binding control for complete cold ECDLP comparisons

Frozen 2026-11-18 UTC **before any CT202 native run**. Source/protocol improvement only; all claims [pcc:unverified].

## Motivation and exact failure mode

CT201 PR #1766 independently checks the mathematical reported scalar and compares declared complete process wall, but it groups run rows by block and arm without checking their **recorded execution order**. It also accepts arbitrary valid 64-hex `binary_sha256` values per row, without requiring a fixed executable per arm or the same executable for `rho` and `rho_sham`. Thus a file listing a systematically last-run candidate, or a sham built from unrelated executable bytes, can satisfy CT201 even if the claimed A/A control is not an A/A control. The CT199 carryover result makes order an experimentally material covariate, but does not prove this bias actually occurred in a native ECDLP experiment.

## Fixed prospective run-order contract

CT202 is an additional *strict* gate on CT201's v1 evidence, not a silent revision of CT201's frozen legacy output. Use at least one **whole ten-block cycle**. Within each block, the five algorithm rows must appear contiguously and in the following order. Let the arm numbering be `0=transfer,1=rho,2=rho_sham,3=bsgs,4=ic`. For `j=0..4`, take the sequence `[(0+j)%5,(1+j)%5,(4+j)%5,(2+j)%5,(3+j)%5]`. For `j=0..4`, follow with the **reversal of that corresponding sequence**. The 10 sequences form one immutable cycle; additional blocks, if used, must comprise complete cycles in this same sequence.

In each ten-block cycle, each arm appears **exactly twice at every within-block position**; each of the 20 *ordered distinct immediately preceding/current arm pairs* appears exactly twice. These are verified algebraically and by source regression tests. The deterministic roster is frozen in advance; it is *not* chosen from timings or a synthetic advantage. Balanced scheduling mitigates position and first-order within-block carryover bias; it cannot by itself demonstrate zero carryover, host isolation, or proper coldness. Record chronological rows without retrospectively sorting them.

## Executable binding and controls

All 10+ recorded executions of a given algorithm arm must declare the **same lowercase SHA-256 digest of the executable bytes**, and `rho` and `rho_sham` must declare the same digest. This is a *necessary* condition for same-binary A/A, not a sufficient one: argv, RNG seeds, process state, compiler flags, child processes, host identity, GPU/RAM use, real time, raw receipt bytes, and the executable's actual behavior are still producer assertions. A separately signed independent process verifier must authenticate those properties and verify that the binary hashes correspond to real retained bytes. The CT201 same public target, fresh-process declaration, full external wall, phase accounting and memory cap remain binding.

## Scientific acceptance and rejection

CT202 calls CT201's unchanged mathematical score only after the complete balanced roster and executable-binding checks; it adds no source-derived speedup. Reject missing/partial cycles, reordered rows, route-dependent executable substitution, sham binary substitution and malformed roster. CT201's diagnostic bootstrap and A/A geomean are retained as diagnostics, not promoted to PCC or independent measurement.

No artifact hydration, native CT125/CT192 execution, paid cloud or ECDLP benchmark is authorized. The original 695/701 custody, same-host native C169/C13/N2_actual/D pricing, full cold rho/BSGS/IC comparison, reproducible raw logs and signed PCC remain open.

Sources inspected: merged crypto [#3877](https://github.com/isogeny-labs/crypto/pull/3877), cryptanalysis [#1748](https://github.com/isogeny-labs/cryptanalysis/pull/1748), [#1756](https://github.com/isogeny-labs/cryptanalysis/pull/1756), [#1761](https://github.com/isogeny-labs/cryptanalysis/pull/1761), [#1766](https://github.com/isogeny-labs/cryptanalysis/pull/1766), root `AGENTS.md`, `docs/ACTIVE.md`, session log 2026-11-18 and [queue #3904](https://github.com/isogeny-labs/crypto/issues/3904). Shared research-KB service is not available in this runtime; no novelty claim.

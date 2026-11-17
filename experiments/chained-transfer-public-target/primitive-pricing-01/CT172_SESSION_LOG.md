# CT172 session record — 2026-11-16 America/Denver

Standing: [pcc:unverified]. Separate scoped session record to avoid clobbering the active 159-kB shared `docs/session-logs/2026-11-16.md` under concurrent writers.

## What was done

- Read latest root [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877) (merged), live [queue #3904](https://github.com/isogeny-labs/crypto/issues/3904), merged selected cost [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), merged CT171 [#1690](https://github.com/isogeny-labs/cryptanalysis/pull/1690), GPU IC [crypto #4178](https://github.com/isogeny-labs/crypto/pull/4178), CT126 `src/main.rs`, CT141 admission, AGENTS and existing fixed evaluator tests. Avoided concurrent Richelot chart source, original 695/701 producer, and paid-run ownership.
- Created branch `research/ct172-native-selected48-replay-20261116` from cryptanalysis/main. Froze protocol at `6bb280b81052deb1b77ea20f6af0c315fd33ceab` before the new Rust source.
- Added native scalar-blind `ct172-replay` (real literal packets, both directions/four sectors/identity and nonzero, all three maps, complete output/counter equality, separate inverse, eight sabotage controls). Added isolated Cargo manifest and source-only GitHub workflow.
- Opened [cryptanalysis PR #1692](https://github.com/isogeny-labs/cryptanalysis/pull/1692), and posted cross-repo checkpoint on [crypto queue #3904](https://github.com/isogeny-labs/crypto/issues/3904#issuecomment-6935360682).
- Exact-head source CI [run 43998336097](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43998336097) completed **success** on `a330cc72060b61c68c7489d72d2d30695434bb33`. This job checked CT171's real 48 fixture in normal and optimized Python, Rust syntax, and Cargo manifest; it did not typecheck or run native CT172.

## Decisions made

- Use original CT125 Rust runtime to avoid a fresh arithmetic implementation. Use the original frozen 48 literal keys instead of regenerating inputs from a known scalar.
- Keep native parity unexecuted while existing owner/budget STOP and materialization rules remain; do not run the CT141 gated benchmark or launch EKS/Spot/GPU.
- Keep CT126's five-public-point benchmark and CT171's guard untouched. New source is in its own Cargo package and feature branch; no protected merge, auto-merge or signed PCC assumption.
- Not a new mathematical ECDLP transfer lead or performance claim. Reused known earlier published constructions/obstructions rather than claiming novelty.

## Open threads

- Actual restored-source Rust typecheck, compile/link, source-tag readback and admitted bounded 48-public-input native replay.
- Independently authenticated 695/701 raw population; same-host paired C169/C13a/C13b/D with setup, counter controls and memory; cold complete source-prime rho/BSGS/IC, signed PCC.
- Review inherited broad PR checks and preserve a failing gate rather than bypass; root queue is coordination.

## Errors

- `crypto-autoresearcher` AGENTS and shared `docs/lab-contract.md` connector reads failed with UTF-8 decoding errors. Repo metadata was available but not the shared contract; no claims about its unseen contents.
- This session's runner has no local Rust compiler, no directly mounted full sibling dependency tree or restored original authenticated raw corpus. Exact-head source CI passed but is explicitly not a native compilation.
- Initial GitHub workflow template escaped an Actions `${{ ... }}` expression literally; corrected it before creating the PR, and the exact-head source CI passed.

---

## CT174 continuation — 2026-11-16 20:42 America/Denver / 2026-11-17 UTC

### What was done
- Re-inspected the latest crypto #3877 (merged), live crypto #3904 research queue, cryptanalysis #1692 current branch, merged crypto #4215, cryptanalysis #1523 and crypto #4178, AGENTS.md, the CT125 original `Runtime`, CT126 original five-point timing path, all 48 frozen public packets, and exact-head workflow status; did not edit concurrent Richelot #4485.
- Checked original GHS Weil-descent literature before the cost-path change; no new attack/novelty claim. Research-KB MCP and its wrapper unavailable in this connector-only environment.
- Froze prospective route-pricing protocol at commit `a60fd902cccf51dfd25d1be80231307ad2dac837` **before implementation** in `CT174_PAIRED_NATIVE_PRICE_PROTOCOL.md`.
- Implemented opt-in `ct172-replay --paired-price` at `113d92ddf1f7d0617ca97849d1dff72372216fe1`: the exact 48 public packets, native CT125 direct/retained A-B-B-A plus direct A/A, separate inverse, setup nanoseconds, raw per-call nanoseconds as decimal strings, full 19-word outputs, all 21 original counters, and Linux VmHWM if present. The numeric scalar remains a diagnostic label only; the runtime sees public class packets, not a known logarithm.
- Exact-head [CT172 source-only workflow 44012486122](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44012486122) passed: pinned original dataset and Rust source checked, Python normal/-O mutation controls passed and `rustfmt`/Cargo manifest parsed. **No Rust typechecking, linkage, or native timing took place.** [pcc:unverified]

### Decisions made (and why)
- Extend the existing actual public-input CT125 harness rather than alter the immutable original CT125 or CT126 code or duplicate original 695/701-corpus ownership. Require a special CLI flag so unchanged parity runs remain unchanged.
- Pair ABBA and A/A within each of 48 cohorts and keep every raw sample, not a falsely precise speedup ratio. Time admission, actual CT125 transfer/corrections and final check, but not JSON serialization. Price one actual inverse per cohort separately because its use is attack-dependent.
- This is deliberately a **warm route-price instrument**, not an individual `C169/C13a/C13b/N2_actual/D_padd` microprice and not a cold complete ECDLP solver. Setup and VmHWM are recorded independently; authorized repeated cold rho/BSGS/IC/transfer costs and signed PCC remain required.

### Open threads (unfinished)
- Owner-admitted restored-source native typecheck/link and bounded 48-case arithmetic replay; then opt-in paired sample execution on same host with host/optimizer evidence and variance/CI. Independent 695/701 custody remains required.
- Instrument the **actual** CT125 `pmul(2)+descend_point` and matched `D_padd`, `C169`, both `C13` operations through the existing authorized owner instead of interpreting full-route prices as primitives.
- Complete verified cold public-target prime-field rho/BSGS/IC/transfer, counting all phases, inverse if needed, startup and memory; maintain artifact, ledger, owner STOP and signed PCC gates.

### Errors (what went wrong, how it was handled)
- The container lacks Rust/Cargo and cannot reach GitHub, so new source was not typechecked or run locally. The scoped GitHub workflow parses Rust successfully but is explicitly source-only.
- No authenticated 695/701 raw object-store corpus or independent signed verification available. No EKS, Spot, GPU, protected merge, or paid workload attempted.

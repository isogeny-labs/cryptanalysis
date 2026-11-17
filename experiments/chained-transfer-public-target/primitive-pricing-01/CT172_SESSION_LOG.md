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

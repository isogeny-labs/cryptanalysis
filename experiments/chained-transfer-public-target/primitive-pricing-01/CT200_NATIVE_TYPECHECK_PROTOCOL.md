# CT200 — bounded native release typecheck for the CT192 all-48 public norm arm

2026-11-18 UTC. Source/compilation engineering only. **[pcc:unverified]**.
[Draft PR #1761](https://github.com/isogeny-labs/cryptanalysis/pull/1761).

## Why this is the next discriminating gate

CT137's [source-pinned compile record](CT137_COMPILE_REPLAY_01.md) documents
successful Rust 1.99.1 `cargo check --release` for the *earlier* CT126
original and CT125-reuse crates on exact hosted job 132836897774
([run 43722363285](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43722363285)).
It does **not** cover CT192's separate, later scalar-blind all-48 Rust driver
and derivative, which adds pre-norm class binding, actual/neutral norm arms,
compiler input barriers, 21-field live counter checks and two 4,608-slot
timing panels. The CT192–CT198 source workflows parse Rust with rustfmt,
but do not typecheck/link/execute it.

CT198's frozen selected 48 × 21-counter audit on
[source fixture 9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3](ct192-public48-norm/CT198_ROUTE_COST_REPORT.md)
shows identical common-stage counters for direct 169 versus strongest retained
13×13: the decisive *counted* difference is `C13a+C13b-C169`, not norm
reuse. The first executable compiler gate should remove type errors before
any authorized same-host price or full-cold comparison.

## Frozen dependencies and fail-closed operations

- GitHub Actions workflow `.github/workflows/ct200-public48-native-typecheck.yml`;
  Ubuntu 24.04, max 15 minutes, Rust 1.99.1; **only `cargo check --release`**.
  It does not run Rust binaries, native parity tests, ECDLP solves, timing
  loops or paid EKS/Spot/GPU jobs.
- Require exact PR HEAD, original CT125 Rust blob
  `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc` and original public-48
  blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`.
- Checkout the previously used pinned sibling
  `isogeny-labs/crypto@4de29a113dfc1b9d32c1809820b8caa2975042a8`
  via credential-free checkout. Stage the unchanged sibling path; no mutation.
- Reuse exact CT137 immutable artifact tool and current identical config.
  Hydrate only original `nondual-models-18` required for predecessor source
  materialization, with 180-second timeout and SHA-256 and byte-length checks:
  second 217960 B/`22225094b7e3727332a761593b47ac44a2efd2f04bbdb1b1865abf3c35ba7267`;
  third 326200 B/`1a7c90c81310a9d1a329b830c9c7b9f52a6c4504152c26162fb46f7fc5184787`.
- Run original unchanged `paired-fourth-preflight`,
  `fixed-jacobian-chain-01` and `fixed-jacobian-chain-evaluator-01`
  materializers, then CT192 `source_contract.py` and `--materialize`.
  Use `rustfmt` only for a parse check before actual Cargo semantic checking.
- Retain source identities, materialization output, rustc/cargo versions and
  full compiler stderr/stdout as `ct200-evidence/` workflow artifact, even
  if the first prerequisite fails. Never label a toolchain or syntax pass
  as a native arithmetic, timing or independent PCC result.

## Exact intended outcome and failure decisions

**Pass:** original authenticated *dependency* inputs restored with the declared
hashes and Rust 1.99.1 reports exit 0 from the exact CT192 release Cargo graph.
This establishes source semantic/typecheck status only; linking, true arithmetic
replay and performance remain unproved.

**Failure:** retain the earliest actual nonzero stage, full diagnostic and exact
head. Classify 403 artifact access, unavailable original model, missing
generated predecessor or Rust interface error separately. Do not use fake
model fixtures or weaken blob checks to get a green result.

**Next after native compile:** owner/provider admission for bounded native
all-48 arithmetic and complete counter replay, independently authenticated
695/701-record custody, physically randomized paired same-host
`C169,C13a,C13b,N2_actual,D` timing plus A/A and memory/clock controls;
then complete cold *single-target* source vs transferred solve against
best matched rho/BSGS/IC with all setup, transfer, linear algebra,
individual logarithm recovery, verification, and peak memory included.
No performance advantage exists by this source artifact. Require independent
PCC-signed replay for any promoted ratio.

## Concurrent work and sources checked

- [Producer crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877)
  is merged and its queue [#3904](https://github.com/isogeny-labs/crypto/issues/3904)
  has a separate active cubic inverse/map lane, including
  [crypto #4544](https://github.com/isogeny-labs/crypto/pull/4544).
  This CT200 change does not edit or duplicate that work.
- [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215),
  [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523),
  [CT192 #1735](https://github.com/isogeny-labs/cryptanalysis/pull/1735),
  [CT198 #1748](https://github.com/isogeny-labs/cryptanalysis/pull/1748),
  [CT199 #1756](https://github.com/isogeny-labs/cryptanalysis/pull/1756),
  [GPU index calculus crypto #4178](https://github.com/isogeny-labs/crypto/pull/4178).
- `AGENTS.md`, original CT137 manifest/CI and CT192 source-contract/driver
  were checked. Research-KB MCP and lab wrapper are not available in this
  environment; no novel attack or unsearched prior-art claim follows.

This protocol is not compute admission, a scientific result, a signed
execution-proof or an authorization to bypass repository gates. **[pcc:unverified]**.

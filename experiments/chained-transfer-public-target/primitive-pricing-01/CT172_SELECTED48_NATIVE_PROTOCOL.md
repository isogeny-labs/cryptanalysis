# CT172 — prospective 48-record native public-input replay protocol

Date: 2026-11-16. Standing **[pcc:unverified]**. Frozen BEFORE implementing CT172's new Rust binary. Root [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877) is merged; coordination is [crypto issue #3904](https://github.com/isogeny-labs/crypto/issues/3904). Continuation of CT171 [cryptanalysis #1690](https://github.com/isogeny-labs/cryptanalysis/pull/1690), not a second owner of CT141 native timing or the 695/701 raw corpus.

## Exact hypothesis and inputs

The CT125 derivative `chained-n4-fixed-jacobian-chain-norm-reuse` can accept **each actual frozen public class** from [CT125's 48-record fixture](../evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json) without reconstructing it from a known secret scalar, evaluate all three original candidate routes and return their original complete canonical target class. This is the same pinned `p=223` fixed N4 geometry and 2,771,711 subgroup, not a substitute field or curve. The scalar label is diagnostic metadata **outside the runtime** and must never be passed to the evaluator.

Pinned fixture Git blob: `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`. CT171's independent source gate must confirm 2 directions x 4 cofactor sectors x 6 scalars, 8 identity and 40 generic rows. Original CT126 five-point forward-only benchmark remains unchanged at blob `ac4146577f5019fc17674deb342eb5d9fc749715`.

## Required exact native comparison (not yet executed)

1. Construct the actual `CheckedInstance` and CT125 `Runtime` once. Parse every 19-word literal public input `key` from the pinned fixture with the actual `prime.field_tag` and `prime.model_tag`. Do **not** construct any point by multiplying with the fixture's known scalar.
2. For every original input, independently admit the same literal public packet for **direct composite**, **literal sequential**, and **retained lift**. Run each route, `check_final` for actual target norm/order, and require its complete 19-word canonical output to equal the frozen `whole_outputs_equal` for that row.
3. Reset native counters before each arm; require the **entire serialized Calls object** to equal the frozen route dictionary (no omitted counters, no numeric coercion). Require all 48 distinct (from,to,sector,scalar-label) combinations, exactly 8 identity rows and 40 nonzero rows, including reverse direction and all sectors. Fail before success if any record is missing or duplicated.
4. Exercise the public inverse after the route replays, requiring round-trip equality to the original 19-word input. Do not price inverse recovery using forward-only primitive counts.
5. Emit deterministic JSON with every observed comparison and a summary, with explicit `[pcc:unverified]` standing. A nonzero exit is mandatory on any field/schema/packet/equality/counter/round-trip discrepancy. Add in-memory sabotage controls (wrong expected output, altered counter, repeated cohort, wrong typed scalar) and require explicit failures under `--self-test`.
6. Preserve all output bytes, exit status, SHA-256, exact checked Git head/fixture/derived binaries, Rust version and memory receipt in the **later admitted execution**. Do not claim compiled, run, independent, or signed evidence from a code-only commit.

## Separation from actual pricing and complete ECDLP

CT172 is a **parity/counter coverage** implementation. It must not time primitives, launch cluster compute, use EKS/Spot/GPU, modify the native CT141 admission contract, mint a verified PCC verdict, or treat a 48-row replay as the complete original 695/701 population. Native execution needs existing owner/admission and budget STOP resolution; GitHub Actions PR triggers remain source-only.

Next, conditional on admission and successful independent replay, price same-host paired `C169, C13a, C13b, D` with identical public points, setup/corrections, A/A and memory. Follow with complete **cold** single-target source-prime ECDLP solving against strongest optimized rho, BSGS and IC including setup, mapping, linear algebra, recovery and verification, and require signed independent PCC. A symbolic saving is not a complete-solve advantage. [pcc:unverified]

Obstruction names: **COHORT-UNEXECUTED** (no CT172 native replay), **RAW-695/701-CUSTODY** (original whole raw corpus not independently signed), **NATIVE-ADMISSION-STOP**, **MATCHED-COLD-ECDLP**, **SIGNED-PCC**.
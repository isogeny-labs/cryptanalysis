# Correctness and validation assessment — crypto and cryptanalysis

Date: 2026-11-15. Sources assessed: `isogeny-labs/crypto` at `e0e3725bac`,
`isogeny-labs/cryptanalysis` at `c021359c`. The same document is committed in
both repositories.

This is an assessment, not a research result. It changes no code, no evidence
and no claim standing. Nothing in it is a pcc claim; every statement about a
research number is `[pcc:unverified]`.

## 1. Summary

1. **No wrong answer was found.** Every solver read in the C library checks
   `k·G = Q` before reporting success. An independent Python re-implementation
   re-checked `[k]G = Q` on 80,999 committed ecbench records marked `verified`
   and all of them hold. The leaderboard's three renderings agree with each
   other, and no published row was found whose number differs from the record
   it cites.
2. **The validation gates do not yet establish what they are described as
   establishing.** Both pcc keyrings are empty and neither ledger contains a
   signed verdict, so all 796 claims stand `unverified` and none can become
   `verified`. Separately, each gate that was tested accepted fabricated
   evidence on a scratch copy: a pull request can add its own signing key, one
   hand-written line validates a leaderboard row, and a benchmark record of a
   run that never happened passes `benchrec check`.
3. **In crypto, the unit tests are not run on pull requests.** About 6,600
   library tests exist; PR workflows run filtered subsets only. The tests that
   guard cost accounting additionally depend on evidence files that are not in
   a normal checkout.
4. **The code defects found are mostly availability and accounting, not
   soundness:** three non-terminating paths in the C library on valid inputs,
   one BSGS operation counter that over-reports by about 1.5×, unvalidated
   explicit-curve specs in ecbench, and a Serpent implementation that is not
   Serpent.

Recommended order of work is in section 8.

## 2. How this was done, and its limits

| Area | Method |
|---|---|
| Repository gates | Ran `pcc canary`, `ledger verify`, `verify-all`, `standing-by-type`, `validation_gate.py check`, `benchrec gate`, parity checkers, tool test suites |
| Gate logic | Read the tools; for each suspected hole built a minimal bad input on a scratch copy and ran the tool on it |
| C library (cryptanalysis `src/`) | Release, ASan+UBSan and TSan builds with `ctest`; differential and exhaustive small-field tests; reproducers for each finding |
| Rust (crypto `src/`) | Reading prioritised on ecbench and cost accounting; independent re-verification of committed records; targeted test runs |
| Published evidence | Cross-checked leaderboard JSON, Markdown and HTML; hash checks of pinned files; `benchrec` and `validation_gate.py evidence` |
| CI | Mechanical scan of all 792 workflow files (triggers, paths, exit-status handling, pinning, secrets) |

Each finding below is tagged:

- **[D]** demonstrated: a reproducer or a bad input was run and the wrong
  behaviour observed.
- **[O]** observed in the repositories as committed.
- **[R]** by reading the code only.

Limits that apply throughout:

- **No S3.** Raw evidence lives in the artifact store; 7,212 of 8,091
  artifact-managed files (50.3 GB) are absent from the checkout. Leaderboard
  values were not recomputed from raw session records, and
  `build_ic_leaderboard.py --check` could not run.
- **No GitHub settings.** Which checks are required, whether retired workflows
  are disabled, and whether review rules protect `pcc/keyring.json` are not
  visible from the tree.
- **No knowledge-base, ecdb or sheriff.** `research-kb` and the canonical
  `sheriff` tool live in `crypto-autoresearcher`, which is outside this
  session's repository scope. No novelty or literature statement is made here.
- **Partial code coverage.** The Rust crate is about one million lines; the
  files not reached are listed in section 7.
- **Full Rust unit suite:** see section 3.

## 3. Baseline results

| Check | crypto | cryptanalysis |
|---|---|---|
| `pcc canary` | 62/62 | 62/62 |
| `pcc ledger verify` | 1,087 entries, chain ok | 68 entries, chain ok |
| `pcc verify-all` | exit 2: 742/742 not covered | exit 2: 54/54 not covered |
| Claim standings | 742 unverified (344 data, 5 literature, 393 interpretive) | 54 unverified |
| Signed verdicts in ledger | 0 | 0 |
| Keyring keys | 0 | 0 |
| Ledger bypass entries | 335 of 1,087 | 13 of 68 |
| `benchrec gate` | **fails**, 2 of 203 records | ok, 18 records |
| `validation_gate.py check` | 19 rows fail here (raw data not hydrated) | no such gate |
| Lab and skills parity | ok | ok |
| C build and `ctest` | n/a | 20/20 in Release and ASan+UBSan; 18/18 TSan; 0 warnings |
| Python tool tests | pcc 25, benchrec 54, task_card 12, loss_ledger 6, validation-JSON 4: all pass. `test_validation_gate.py`: 63/64. `test_result_switches.py`: see V-19 | identical copies |

Rust library unit tests (`cargo test --lib`, debug build, 6,595 tests):
**not completed.** Two runs were made. The first was killed by the container's
memory limit after 1,074 passes and no failures. The second, run alone, was
stopped after 1,226 passes and 5 failures, having reached about 11 GB in the
`ecbench::challenge` and `ecbench::db` tests; a debug build of the suite does
not finish in this container in reasonable time. The 5 failures are exactly
the five tests of R-5 (missing `records.jsonl`). About 5,360 tests were not
reached.

Previously recorded state of the same suite (session log 2026-11-15, source
`2fd16de7ca`): 6,406 passed, 48 failed, 139 ignored. The list of the 48 is not
in the checkout; a committed partial snapshot lists 39. Of those 39, 33 pass
here, 5 fail on a non-hydrated `records.jsonl` (R-5), and 1 did not finish.

## 4. Validation machinery

`tools/pcc/pcc.py`, `tools/benchrec.py` and `tools/task_card.py` are
byte-identical in the two repositories, so findings on them apply to both.

### 4.1 Critical

**V-1. The verdict keyring is read from the pull request's own tree. [D]**
`tools/pcc/pcc.py:1920` loads `pcc/keyring.json` from the working tree with no
comparison to the base branch. On a scratch copy: generate a key, append its
public half to the keyring, sign two fabricated artefacts, run `pcc verdict`.
Result: the claim stands `verified`; `ledger verify --base` and `canary` still
pass; `lint-prose` accepts a sentence citing it. crypto has no CODEOWNERS
file. Fix: read the keyring from the base ref or an out-of-repository pin,
fail when it differs from base, and add a canary class for it.

**V-2. No claim is verified, and CI reports that as passing. [O]**
Both keyrings are empty, both ledgers hold zero verdicts, and
`pcc-gate.yml` accepts `verify-all` exit 2 and exits 0 when
`PCC_SIGNING_KEY` is unset. 92 crypto claims have no proof at all; 52 of 54
cryptanalysis claims are of kind `statement`, which can never verify. The
labelling in prose is consistent with this (every citation found is
`[pcc:unverified]`), so nothing is overstated; the tier is simply not
operating. Fix: provision the CI key through an anchored keyring (V-1 first),
then make the gate report or fail on zero signed standings.

**V-3. One line in a sweep `verdicts.jsonl` validates a row with no artefacts. [D]**
`scripts/validation_gate.py:317-340`: a passing verdict needs the three
artefact keys only to be truthy. The line
`{"row":"…","verdict":"ok","replay_certificate":"-","validator_report":"-","rho_reference":"-"}`
made a leaderboard row and a benchmarks row `validated`. Verdict files are not
compared with base, so lines can be added or failing lines removed. Fix:
resolve each named artefact through `check_evidence_dir`; make verdict files
append-only against base and signed.

**V-4. `VALIDATION.json` accepts self-attested and self-inconsistent evidence. [D]**
`validation_gate.py:149-217`. A three-file directory passed with a headline
of claimed 0.01 against recomputed 5.47, because the tolerance `rel_tol` is
read from the report itself and `NaN` disables the comparison (line 188; the
same code is at `pcc.py:879`). `independent`, `matches_protocol` and
`order_holds_across_band` are producer-written booleans; band values need
only be positive; nothing binds the row text to the evidence. Fix: fixed
tolerance, derive `order_holds_across_band` from the band, bind the row
digest and headline into the manifest, require signatures on both artefacts.

### 4.2 High

| Id | Finding | Tag | Where |
|---|---|---|---|
| V-5 | A claim's statement is not bound to its proof: a `solve` claim worded as an ECC2K-130 solve passed with a certificate for a 5-element group over GF(97) | D | `pcc.py:488-503`, `1063-1119` |
| V-6 | `lint-prose` is evaded by a heading glued to the paragraph, a table row, a blockquote, HTML, synonyms ("outperforms", "confirmed"), a Cyrillic letter, or one `[pcc:unverified]` anywhere in the paragraph | D | `pcc.py:1233-1255` |
| V-7 | Standing does not go stale when evidence changes: after deleting the certificate, `standing` printed `verified` while `verify` printed `fail` | D | `pcc.py:996-999`, `1202-1226` |
| V-8 | `benchrec check` passes a hand-written record of a run that never happened (all-zero SHA-256, `"uploaded": true`, arbitrary `s3://` URI, 0-byte PDF); PROGRESS.md then shows its metric | D | `tools/benchrec.py:743-850` |
| V-9 | Closed-record immutability is bypassed by pointing `.benchrec.json` `records_dir` at a new directory in the same commit | D | `benchrec.py:158-166`, `965-979` |
| V-10 | The ledger has no anchor outside the file. A copy cut from 72 to 7 entries and rechained passes `ledger verify`; `--base` with an unresolvable ref exits 0 | D | `pcc.py:130-136`, `2009-2016` |
| V-11 | `task_card.py` accepts a card with no commit, an unapproved id, `bash -c "<string>"`, an overridden `PATH`, and writes outside `write_scope`; it ran and reported `succeeded` | D | `tools/task_card.py:251-262`, `302-305`, `345-351` |
| V-12 | A `benchmarks/README.md` row not in the one exact expected shape (no backticks, bold date, no link) is never judged by the gate | D | `validation_gate.py:428` |

### 4.3 Medium and low

| Id | Finding | Tag |
|---|---|---|
| V-13 | Claim files can change after registration: `ledger verify` does not compare a file with its registered digest. As committed, cryptanalysis `PCC-20261108-0876eb` matches no registered digest, and 9 crypto claim files have no ledger entry (`PCC-20261104-2de7a3`, `-56667f`, `-94a6f4`, `-a6ca5a`, `-bbda0f`, `-c455d0`, `PCC-20261105-9d5a6d`, `-ac1e93`, `-aca921`) | D, O |
| V-14 | `BENCHREC_SKIP` is matched as a substring anywhere in the command (a trailing shell comment suffices), is not recorded, and `BENCHREC=README.md` satisfies the hook | D |
| V-15 | `CHECKPOINT_SKIP` prints "bypass recorded" when the ledger append failed (`checkpoint-hook.sh:63-78`) | D |
| V-16 | Recorded bypass reasons are cut to their first word (`"reason": "not"` for `CHECKPOINT_SKIP="not an experiment run: …"`), so the 335 entries cannot be audited by reason | O |
| V-17 | `checkpoint.sh gate` passes with no upload once `.resume/.last-push` holds the current state hash | D |
| V-18 | Validation-gate base checks are skipped when the base ref does not resolve; neither `PRE_GATE.json` carries an `expires`, so the freeze (15 leaderboard keys, 116 benchmark rows) never lapses | D, O |
| V-19 | `tools/test_result_switches.py` runs zero tests as a script and is in no workflow. Called by hand, `test_every_rust_env_switch_is_recorded_or_exempt` fails with a list of unrecorded switches | O |
| V-20 | `tools/validate_validation_json.py` checks schema `validation/v1`; all 71 gate files are `validation-gate/v1`, so it reports "OK (0 records)". It also accepts `status: validated` with certificate kind `none` | D, O |
| V-21 | Leaderboard `leaders` take the minimum point estimate with no standing filter and no §5a band; the committed `koblitz_batch` leader is a pre-gate row. `progress_metrics.py` exports leader ratios without standing | R, O |
| V-22 | The canary does not cover V-1, V-5, V-7, V-10 or the paragraph-prefix skips of V-6, and lives in the file it tests | R |
| V-23 | Lean hole scan is regex-based (`sorryAx`, macro-emitted axioms pass); the kernel gate `tools/lean/proof-gate.sh` was not audited | D at regex level |
| V-24 | Key revocation needs a JSON boolean; `"revoked": "true"` leaves the key valid | D |
| V-25 | cryptanalysis has no validation gate, `VALIDATION.json` validator, `result_switches.py` or `loss_ledger.py`; only pcc and benchrec guard results there | O |

## 5. Published evidence as committed

**Leaderboard gate status (crypto, 28 board rows).**

| Table | Rows | Evidence | Status rendered | Finding |
|---|---|---|---|---|
| B, prime and random-binary ladder | 13 | `docs/ic/runs`, `VALIDATION.json` valid | validated | consistent |
| A, Koblitz one-target, rule v9 | 6 | `research/ic_tool_program/rule/v9`, both pinned hashes match | validated | consistent |
| C, Koblitz 32-target descent | 9 | `research/ic_descent_20260930`, no `VALIDATION.json` | unvalidated (pre-gate) | correctly labelled |

All 28 rows agree across `leaderboard.json`, `LEADERBOARD.md` and the HTML.
Spot-checked gap arithmetic is right, and every row reports IC above matched
rho as distance remaining. `[pcc:unverified]`

| Id | Finding | Tag |
|---|---|---|
| E-1 | Closed record `benchmarks/records/20261105T1826Z-ic-aimed-gather-registry-binding-20261105.json` pins `docs/curves/registry.json` at SHA-256 `1edbd0d…`; the committed file is now `33a16da…` (regenerated 2026-11-13). `benchrec gate` fails on it offline. Corrected after the first CI run: the `records` job has the original bytes in the S3 archive and passes this record, so this is a limit of an offline checkout, not a failing record | O |
| E-2 | `benchmarks/records/20261115T0609Z-genus-ladder-sge-scale.json` is on main with `status: open` and empty content. `benchrec gate` fails on it; it would fail the `bench-records` check on every PR | O |
| E-3 | `reproduction.lock.json` is stale: of 115 pinned files, 1 is missing and 9 mismatch, including `tools/backend-leaderboard/src/{main,evidence,reproduction}.rs` and `src/cryptanalysis/ecbench/{band,canonical,methods,stats}.rs`. Root `LEADERBOARD.md` cites this lock as its reproduction basis | O |
| E-4 | Rows rendered `validated` whose recorded sweep verdict is `validated_with_caveats`, `pricing_ok=False` (Table A also `rho_reference_ok=partial`). By design and shown in the cell, but the headline word and the caveat disagree (`docs/ic/LEADERBOARD.md:240-269`) | O |
| E-5 | `pcc lint-prose` over the repositories reports 212 uncited strong statements in crypto and 27 in cryptanalysis, mostly in root `RESEARCH_*.md`; example `RESEARCH_SEMAEV_ROOTFIND_VS_GROEBNER.md:286`. None is a leaderboard or benchmarks row | O |
| E-7 | `docs/session-logs/2026-11-15.md` on main contains stray conflict-marker lines (`=======` and `>>>>>>> origin/main`) left by an earlier merge; they make later merges of that file error-prone | O |
| E-6 | Stale references: `docs/VALIDATION_GATE.md:181` names rule `v7` where the board cites `v9`; `benchmarks/README.md:29-30` gives 2026-10-24 counts | O |

## 6. Continuous integration

| Id | Finding | Tag |
|---|---|---|
| C-1 | crypto: no PR-triggered workflow runs the root `cargo test --lib`. PR Rust jobs are fmt, clippy, `cargo check`, and filtered tests (`--lib ecbench`, `f4_fp`, and similar). 22 of 32 `tests/*.rs` integration tests are named by no workflow | O |
| C-2 | crypto: of 119 Python and shell test scripts, 12 run on every PR, 20 on path-filtered PRs, 57 only on push or dispatch, 26 in no workflow (among them `tools/test_task_card.py`, `test_loss_ledger.py`, `test_result_switches.py`, and `scripts/test-check-large-files.sh`, the test of the size gate) | O |
| C-3 | Guards that AGENTS.md describes as PR or scheduled checks and are not: `lean-proof-gate.yml` (push to main only, so a `sorry` is caught after merge), `ic-leaderboard.yml` (AGENTS.md:1509 says matching PRs), `curve-names.yml` (its PR step can never run), `audit-runs-daily.yml` (dispatch only), `codeql.yml` (no schedule; Rust CodeQL only by hand) | O |
| C-4 | Exit status lost through `\| tee` without `pipefail` in PR test steps, cryptanalysis: `groebner-f6-{affine,bitplane,compact,message,packed-target,packed,prepared}.yml` and `groebner-field-obstruction.yml`. Same pattern in 13 non-PR steps across both repositories | O |
| C-5 | `if rg 'sorry…'; then exit 1` with no step installing ripgrep: passes if `rg` is absent. cryptanalysis `binary-genus2-cover.yml:125` (PR); crypto `n83-indexed5-id30.yml:50`, `n83-online-range.yml:114`, `n83-online-finegrid-proof.yml:32`, `n83-root11-dynamic.yml:120` | O, effect inferred |
| C-6 | Long-lived `ARTIFACTS_AWS_*` keys are given to steps that run code from the PR checkout in 140 PR-triggered workflows (119 cryptanalysis, 21 crypto). `bench-records.yml` uploads with the same key, so it can write to the evidence store. Only 8 workflows use OIDC | O, key scope inferred |
| C-7 | `disable-retired-workflows.yml` lists workflows still documented as guards: `ic-measurement.yml`, `ic-e2e-benchmark.yml`, `n53-target-cyclic-rank.yml`, and five cryptanalysis workflows that are still PR-triggered | O |
| C-8 | Two crypto PR jobs are both named `gate` (`validation-gate.yml`, `pcc-gate.yml`); a required context `gate` is ambiguous | O, risk inferred |
| C-9 | 12 cryptanalysis jobs carry `if: false`, 11 of them in PR workflows, so they report as skipped checks | O |
| C-10 | 2,471 action references are pinned to a tag or branch and 50 to a commit; 35 use `dtolnay/rust-toolchain@master`; 33 installs fetch `elan-init.sh` from `master` | O |
| C-11 | The `large-file-ok` label turns the size and artifacts failure into a pass; the autofix queue's "never weaken a test" rule is enforced only in its prompt | O |
| C-12 | Fleet hygiene: 344 of 546 crypto workflows and 104 of 246 cryptanalysis workflows never fire on a PR or on main; 95 dead path patterns; `fb-archive-offsite.yml` runs a script that does not exist on a weekly schedule; 198 workflows have no `concurrency`; 20 jobs have no timeout | O |
| C-13 | Parity checks are self-referential: each repository checks its files against its own lock, so a PR editing a shared file and the lock together passes. 35 same-path files outside the lock already differ, including `tools/lean/proof-gate.sh` and `scripts/checkpoint.sh` | R, O |

cryptanalysis is in better shape on tests: `ctest`, `cargo test`, the
bindings and all 24 Python tests run on PRs.

## 7. Source code

### 7.1 cryptanalysis C library

No path returning a wrong logarithm was found. Under test, with zero
failures: 3 million differential cases of modular arithmetic including moduli
near 2^64; the group law exhaustively on 16,308 curves with p < 60; point
counting on 2,999 curves; 39,856 curve solves over every divisor order; 1,800
mutated checkpoints under ASan.

| Id | Sev | Finding | Tag |
|---|---|---|---|
| S-1 | High | `ca_curve_group` and `ca_curve_detect` hang on a composite subgroup order: `curve.c:130,137` call `ca_sqrtmod_prime` on a non-prime, and `modarith.c:250` loops until a non-residue that does not exist. Input p=89, a=9, b=0, order 25. Reachable from the FFI and `solve --alg glv` | D |
| S-2 | High | `ca_rho_solve` never terminates when the target is not in the subgroup generated by the base (`rho.c:1072`: the membership check tests only `n·P = O`; default `max_ops` is 0). Input Z_p*, p=1000003, base g², target g | D |
| S-3 | Medium | `ca_kangaroo_solve` never terminates when the logarithm lies outside the interval (`kangaroo.c:490-501`) | D |
| S-4 | Medium | `ca_bsgs_solve_checkpointed` double-counts baby steps (`bsgs.c:466` and `:506`): reported 395,418 against 264,382 performed (1.50×; 1.66× on a second instance). Affects the durable CLI `bsgs` and checkpointed Pohlig-Hellman; `ca_bench` uses the plain path and is not affected | D |
| S-5 | Medium | SIGFPE on a zero modulus in `ca_powmod`, `ca_legendre`, `ca_mult_order`; `powmod` is exposed unguarded in the Python, Rust and Go bindings | D |
| S-6 | Low | `ca_htab_init` loops forever for sizes above 2^62 (`util.c:70,162`) | D |
| S-7 | Low | `ca_dense_solve_mod_prime` returns `CA_OK` with a wrong solution for a composite modulus (unchecked `ca_invmod` result). Internal; current callers pass primes | D |
| S-8 | Low | Plain solver counters omit fixed set-up work: reported/performed 0.90 (Pohlig-Hellman) to 0.99. The gap is O(log n) and matters only at small n | D |
| S-9 | Low | Several charges are modelled, not measured (`pohlig.c:512`, `curve.c:698`, `group_common.c:16`); on the GLV path the per-step class reduction is not in `group_ops`, so operation ratios overstate wall-clock gains. Documented in comments | R |
| S-10 | Low | Minor: inconsistent error code for a damaged checkpoint, `st->seconds` overwritten in `pohlig.c:555`, `ca_cheon_best_divisor(0)`, NULL context dereference, `[0,0]` meaning whole group | D |

Test gaps: 26 of 193 public functions have no test; no test uses a composite
order, an unsolvable rho instance without a cap, or compares checkpointed and
plain BSGS counts; `test_rho.c:92,212` and `test_kangaroo.c:116,130,144`
accept `OK`, `LIMIT` or `NOT_FOUND`, so only a crash fails them; checkpoint
corruption is tested only for index calculus.

Not reviewed: `ec_tau.c`, `precomp.c`, `grumpy.c`, `sixclass.c`,
`gpu_emulate.c`, `cuda/`, `gpu/`, Lanczos internals, coordinator lease logic.
Suspected but not reproduced, so not counted as findings: a status overwrite
on the NOMEM path in `rho.c:653,758,976`; the same non-termination as S-2 in
`gpu_rho.c`; `(peer, seq)` marked seen before the points are checked in
`coord.c:1236-1245`, with unauthenticated peer names; a truncated chunked
reply returned as `CA_OK` in `coord_net.c:828-854`; `ca_sieve_primes`
overflow above 2^32.

### 7.2 crypto Rust crate

The ecbench runner verification, audit and replay, censoring in `compare`,
seed derivation, word-sized modular arithmetic, `IncrementalGauss`, the binary
and prime group laws and Vélu read as correct.

Independent re-check of committed records marked `verified`, by a separate
Python implementation of the curve arithmetic: 70,051 `prime_explicit`, 5,616
`binary_explicit`, 3,501 `prime_public_fixture` (all present records) and
1,831 `koblitz` (1-in-20 sample): every `[k]G = Q` holds. This covers only
the 888 `records.jsonl` files present locally; 903 more are in the artifact
store. `[pcc:unverified]`

| Id | Sev | Finding | Tag |
|---|---|---|---|
| R-1 | Medium | Explicit curve specs are not validated: `ecbench/workload.rs:524-538` does not check that p or r is prime, that `group_order` is #E, or that G has exact order r. The fixture curve p=113 is accepted with r=28 where the subgroup has 7 elements; a `public` target then grades `verified` against a floor from √28. No committed `prime_explicit` record is affected | R, data check run |
| R-2 | Medium | Legacy accounting is admitted on a binary digest the session declares about itself (`audit.rs:533-541`, `legacy.rs:397-442`). For four rho variants the phases-sum-to-total check is then skipped. 928 committed records have total below the phase sum, all from five listed binaries; S is understated by the class set-up, 4–5% at toy sizes | R, data scan run |
| R-3 | Medium | `fit_exponents` in the `ic boundary` ledger averages cost over every run without reading `verified` (`ic_boundary.rs:16204-16243`); runs that hit `trial_budget` enter at truncated cost and bias the fitted exponent downward. `matched_rho_s_mean` returns 0.0 on an empty match, giving an infinite "vs rho" with no error | R |
| R-4 | Medium | `symmetric/serpent.rs` applies IP and FP around bit-sliced rounds, so it is not Serpent; its three `#[ignore]`d known-answer tests compare one encryption with 10,000-iteration Monte Carlo vectors and could never pass. With IP/FP removed, the 10,000-iteration values match the tests' expected values exactly. No research result depends on it | D |
| R-5 | Medium | Accounting regression tests depend on evidence not in the checkout: five `ecbench::band` and `ecbench::compare` tests fail on a missing `records.jsonl`; the five `audit::committed_replays` tests return silently when their session is absent | D |
| R-6 | Low | The planted-scalar law `1 + derive % (r-1)` is biased near word size and divides by zero at r = 1 (`workload.rs:1808-1831`); negligible for committed sizes | R |
| R-7 | Low | The runner's external check uses the same instance arithmetic that built the target (`runner.rs:1728`), so a group-law bug would be common-mode. The Python re-check found none for prime, binary and sampled Koblitz records; extension-field, Jacobian and hyperelliptic instances were not independently checked | R |
| R-8 | Low | `compare` drops crashed and wrong-answer runs, labelling the comparison inadmissible; the printed ratio is survivorship-biased | R |
| R-9 | Low | `IncrementalGauss` preconditions are `debug_assert` only, and release builds set no `overflow-checks`, so tests and recorded runs trap different things | R |
| R-10 | Low | `Uint::from_biguint` (`ct_bignum.rs:70-84`) exits early on length despite the module's constant-time statement; elimination op counts differ by one `modr_add` per row between the BigUint and u64 paths | R |

Test quality: 161 `#[ignore]` in `src` (the Serpent three are the only ones
ignored because they fail); about 50 default-run tests assert nothing;
no tests in `cheon_counted.rs`, `ecbench/fp4.rs`, `isogeny_walk/walk.rs`,
`bin/ecbench.rs`, `bin/ic_validate.rs`, `bin/replay_check.rs`.

Not reviewed in depth: `koblitz_index_calculus.rs` (26k lines), sparse linear
algebra and Wiedemann, `ic_framework/*`, `bounds.rs`, `claim.rs`,
`challenge.rs`, `band.rs`, `hyper_ic.rs`, `binary_ecc/f2m.rs` reduction and
SIMD paths, hyperelliptic and isogeny class-group code, `crates/*`, and all of
`hash`, `kdf`, `pqc`, `tls13`, `zk` apart from Serpent.

## 8. Recommended order of work

1. **Anchor the pcc trust root (V-1, V-10), then provision the CI key (V-2).**
   Until the keyring is read from base, provisioning a key adds little.
2. **Close the two row-validation holes (V-3, V-4)** and bind claim statements
   to proofs (V-5). These decide whether "validated" on the leaderboard means
   an independent check happened.
3. **Run the Rust unit suite on PRs (C-1)** with a hydrated fixture set in Git
   so the accounting tests cannot pass or fail on absent data (R-5), and
   resolve the recorded 48 failures.
4. **Repair current red state:** close or remove the open record (E-2), decide
   the registry-hash record (E-1), regenerate `reproduction.lock.json` (E-3),
   register or remove the unregistered claim files (V-13), fix
   `test_result_switches.py` and put it in CI (V-19).
5. **benchrec and task-card hardening (V-8, V-9, V-11)** and the hook
   bypasses (V-14 to V-17).
6. **CI exit-status and trigger fixes (C-3, C-4, C-5, C-7)**; move artifact
   access to OIDC with read-only scope on PRs (C-6).
7. **Solver fixes:** default operation caps and primality checks (S-1 to S-3,
   R-1), the BSGS counter (S-4), zero-modulus guards (S-5), the exponent fit
   (R-3), sealed ids for legacy admission (R-2), Serpent (R-4).
8. **Extend the canary** with one class per hole closed above (V-22), kept
   outside the file under test.

## 8a. Repair status

Updated as repairs land; the finding text above is left as first written.

| Item | Status |
|---|---|
| V-1 keyring read from the PR tree | Repaired: the gate reads the base branch's keyring (`--keyring-ref`), fails a keyring that differs from base unless it matches the owner's pin `PCC_KEYRING_SHA256`, and has canary classes for it. Owner action left: set the repository variable when a key is added |
| V-10 unresolvable base ref exits 0 | Repaired: `ledger verify --base` fails on a ref that is not a commit; pushes to main are checked against the previous tip. An anchor outside the repository (signed tag or store object) is not done |
| V-3 sweep verdict line validates with no artefacts | Repaired: a passing verdict validates only when each named artefact is a repository file that passes the same checks as a `VALIDATION.json` artefact; verdict files are append-only against the base |
| V-4 self-attested `VALIDATION.json` | Partly repaired: NaN, infinite, negative and non-numeric tolerances are refused; `order_holds_across_band` is recomputed from the band; an optional `row_digest` binding is checked when present; a pinned artefact must be a JSON object. **Open, owner decision:** a cap of 1e-6 on a report's own tolerance is implemented but switched off, because enforcing it fails 22 admitted benchmarks rows whose headlines were rounded for display (three state 5e299) |
| V-18 unresolvable base in the validation gate | Repaired: `check --base` exits non-zero when the ref is not a commit. The freeze still has no expiry |
| C-4 exit status lost through `tee` | Repaired in the 20 workflows the audit listed (13 cryptanalysis, 7 crypto): `set -o pipefail` on each step that pipes into `tee` |
| C-5 `rg` not installed | Repaired: the five Lean hole checks use `grep -E` |
| S-1 to S-7 C library | Repaired in cryptanalysis: composite order falls back to the negation-only path and `ca_sqrtmod_prime` terminates on a non-prime; rho, GPU rho and kangaroo stop at a built-in runaway guard with `CA_ERR_NOT_FOUND` when the caller set no `max_ops`; checkpointed BSGS no longer counts baby steps twice (reported/performed 1.50 before, 1.00 after); zero modulus returns 0; oversized hash tables and singular pivots return errors. New `tests/test_robustness.c` (nine cases, each failing on the old library). `tests/test_bsgs.c:66` had a limit tuned to the double count and was retuned. S-8 to S-10 are not done |
| V-19 result-switch test | Repaired: the 18 unrecorded environment switches are now recorded (two credentials are exempt and never recorded), the test runs as a script, and it runs on every PR in `lab-parity.yml` together with the task-card and loss-ledger tests (part of C-2) |
| R-4 Serpent | Repaired: IP/FP removed from the bit-sliced rounds; the three ignored tests are replaced by real 10,000-iteration Monte Carlo tests that pass for 128, 192 and 256-bit zero keys. Output differs from the earlier version by design |
| V-2 no signing key | Owner action: generate the CI key, add it to `pcc/keyring.json`, set `PCC_KEYRING_SHA256` and `PCC_SIGNING_KEY` |
| V-8, V-9, V-11, V-14 | Not started here: `tools/benchrec.py`, `tools/task_card.py` and `benchrec-hook.sh` are owned by `crypto-autoresearcher` under the shared-code lock, and that repository is not in this session's scope |
| pcc copy in `crypto-autoresearcher` | Needs the same `tools/pcc/pcc.py`, `test_pcc.py`, `docs/SABOTAGE_RESISTANCE.md` and lock digests; until then its copy differs from the owner copy in crypto |

## 9. Reproducing this assessment

Read-only commands, run from each repository root:

```sh
python3 tools/pcc/pcc.py canary
python3 tools/pcc/pcc.py ledger verify
python3 tools/pcc/pcc.py verify-all          # exit 2 = not covered
python3 tools/pcc/pcc.py standing-by-type
python3 tools/benchrec.py gate
python3 scripts/validation_gate.py check     # crypto; needs hydrated raw data
python3 tools/check_lab_parity.py --siblings
cmake -S . -B build -DCA_SANITIZE=address,undefined -DCA_BUILD_SHARED=OFF && ctest --test-dir build   # cryptanalysis
cargo test --lib -- --test-threads=3         # crypto; needs more than 8 GB
```

The scratch reproducers for the [D] findings were written outside both
repositories and are not committed; each finding gives the input needed to
rebuild its reproducer.

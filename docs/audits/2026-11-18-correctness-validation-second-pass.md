# Correctness and validation assessment, second pass

Date: 2026-11-18. Sources: `isogeny-labs/crypto` at `833a35d21e`, `isogeny-labs/cryptanalysis` at `cfc03a37e`. Follows
`docs/audits/2026-11-15-correctness-validation-assessment.md` (the first pass); finding ids from that report are reused.
The same document is committed in both repositories.

This is an assessment, not a research result. Nothing in it is a pcc claim; every statement about a research number is
`[pcc:unverified]`. Tags: **[D]** demonstrated (a reproducer or bad input was run), **[O]** observed in the repository
as committed, **[R]** read only.

## 1. Summary

1. **The repairs work as tools, but crypto's CI no longer runs most of them.**
   - **pcc gate deleted.** crypto's `pcc-gate.yml` was deleted on 2026-11-16, so no pcc check (canary, ledger, keyring
     trust root, verify-all, prose lint, signing) runs on any crypto PR. **[O]**
   - **Tolerance cap reverted.** The cap merged on 11-15 was undone by hotfix #4394 the same evening:
     `HEADLINE_REL_TOL_ENFORCE_MAX = False` and no pre-cap list on main. **[O]**
   - **Sweep verdicts out of Git.** The sweep verdict files were moved into the artifact store, so the validation gate
     cannot see them and its append-only check is empty. **[D]**
2. **No check is enforced.**
   - `.github/CI.md` itself records that main has no branch protection or required status contexts.
   - Since 2026-11-16, PRs have merged with `validation-gate`, `bench-records`, `agent-learning`, `artifacts`, `names`
     and `corpus` red. **[O]**
   - The artifact store has returned 403 since 2026-11-16. As a result `validation-gate` is red on every PR, so the
     check cannot separate a new violation from the background. **[O]**
3. **crypto main fails its own integrity checks.**
   - `pcc.py ledger verify` is BROKEN: 151 claims have no `claim_type` and no ledger entry.
   - `verify-all` reports 301 failing claims out of 3,544. My first count of 582 counted output lines, not claims.
   - 2,554 claim files have no ledger registration.
   - `benchrec.py gate` crashes on a malformed record.
   - `test_pcc.py` and `lessons.py verify` both fail.
   - The causes are listed in section 3. **[D]**
4. **Still no wrong answer.**
   - No reviewed path returns a wrong logarithm. Every solver checked verifies `k·G = Q` before reporting success.
   - f2m reduction (13 field polynomials), word-size Cantor arithmetic, Shoup multiplication and the tau-adic paths
     passed differential tests with zero mismatches. **[D]**
   - The new defects are a false "no logarithm" or a hang, cost under-counting, and gaming surfaces in the comparison
     machinery.
5. **One of the first pass's own repairs was incomplete.** The S-2 runaway guard in `rho.c` is defeated by a
   caller-chosen `dp_bits` (C-F1 below). **[D]**

## 2. Status of the first pass's repairs on current main

| Item | Landed | On main now | Notes |
|---|---|---|---|
| V-1 keyring trust root | 2026-11-15 | **Tool holds; crypto workflow gone** | Bypasses that still work: a PR that edits `tools/pcc/pcc.py` in the same change passes `ledger verify --base` **[D]**; once a keyring change merges unpinned, later pushes and the sign job trust it **[D]**. cryptanalysis runs the gate and its keyring holds `ci-main`; crypto runs nothing |
| V-10 unresolvable base | 2026-11-15 | Holds | Fails open when the base commit resolves but its ledger blob cannot be read (`pcc.py:149`) **[D]** |
| V-3 sweep verdict artefacts | 2026-11-15 | **Bypassed** | A verdict line may name a real, unrelated row's passing artefacts and validates **[D]**; the verdict files are store-backed and unseen in CI |
| V-4 self-attested evidence | 2026-11-15 (NaN, band); cap 2026-11-15 | **Cap reverted** | `rel_tol` 1e300 validates again **[D]**; `row_digest` optional; `raw_data` without a hash accepted |
| V-18 validation-gate base | 2026-11-15 | Holds | Same fail-open on an unreadable base blob (`validation_gate.py:639`) **[D]**; push and dispatch runs pass no base |
| V-19 result switches | 2026-11-15 | Holds | Runs on PRs in `lab-parity.yml` |
| C-4, C-5 | 2026-11-15 | Hold for the 20 + 5 listed | One PR instance was missed in crypto: `binary-genus2-cover.yml:92-93` has both `\| tee` without pipefail and `if rg` with no ripgrep install |
| E-2 empty open record | 2026-11-15 | Holds | Record removed; 13 new `status: open` records were merged on 2026-11-17 |
| S-1..S-7 C library | 2026-11-15 | Hold for default parameters | S-2 bypassed by explicit `dp_bits` (C-F1); `ca_crt2` with a zero modulus still raises SIGFPE (C-F9) |
| R-4 Serpent | 2026-11-15 | Holds | |
| `getrandom` floor | 2026-11-15 | Holds | |
| V-2 signing key | keyring 2026-11-15 (cryptanalysis) | cryptanalysis: key present, 0 signed verdicts; crypto: PR #4634 open, and no workflow would use the key | |

Not re-tested in this pass: V-5 to V-9, V-11 onwards.

## 3. Why main is red, and the smallest fixes

None of these fixes weakens a check.

| Check | Root cause | Fix |
|---|---|---|
| crypto `ledger verify` | 151 claim files (125 theorem, 22 statement, 4 measurement; created 2026-11-12 to 11-16; producer mostly `Codex`) were written by hand without `claim_type` and never registered. `claim new` has refused this since 2026-11-10, and the deleted pcc gate would have failed these PRs | Add the correct `claim_type`, register each claim; make `ledger verify` fail on any claim file without a matching ledger entry (2,554 files have none, 174 of them lost when merge conflicts were resolved by taking main's ledger) |
| crypto `verify-all` (301 failing) | 151 = the above. 84 point a proof kind at the wrong kind of file (logs or `.md` as validator reports; non-certificate JSON as `certificate`). 30 legacy-format execution proofs. 24 have subjects missing from Git and every manifest, or absolute `/workspace/...` paths. 35 are store-backed subjects absent from this checkout (not genuine) | Run each proof kind's structural check in `pcc claim new` and refuse a structural failure; re-kind the 30 legacy execution claims as attestations; repair or retract the 24 |
| crypto `test_pcc.py` | Test bug: `test_execution_creation_rejects_incomplete_inputs_before_writes` calls `claim new` without `--claim-type` (`test_pcc.py:180`) | Add `--claim-type data` |
| crypto `bench-records` | `tools/benchrec.py:845` passes a dict to `stored_ok`, which crashes at `:830`. The record `benchmarks/records/20261117T0334Z-hec-multi-production-cold.json` (via #4480) is malformed throughout. 13 records merged 2026-11-17 are still `open` | Reject a non-string `validation` with an error; replace the record under a new id (closed records are immutable); producers close their open records |
| crypto `learning` | Commit 4658f1ee5e (#4574) hand-edited three lessons entries after creation (`pull/4557` → `pull/4574`), so their content ids no longer match | Restore the three files byte for byte from `2b5e92dabf`. The repair PR fails the append-only comparison once, by design |
| crypto `names`, `corpus`, `artifacts` | Store outage plus #4520's Git-history fallback: `artifacts.py pull` dies on store-only files. `names` and `corpus` pull files they never read, because `wire_workflows.needed()` treats a `paths:` trigger filter as a data read. `artifacts`: 36 workflows' generated pull steps are stale | Skip `on.paths` in `needed()` and regenerate; keep `claims.tsv` in Git. Workflows that need store-only data stay red until the store returns, which is correct |
| crypto `validation-gate` | 37 rows' evidence is store-only; 42 rows added since 11-15 have no `VALIDATION.json` and are not frozen (38 re-added by a batch of stale PRs merged on 2026-11-16); 6 `ARCHIVE.json` records name rows that are still admitted | Restore the store; give the new rows evidence or remove them; reconcile `ARCHIVE.json` |
| cryptanalysis `verify-all` (52 failing) | 25 subjects missing from Git and every manifest; 15 measurement or execution claims with no qualifying proof; 1 attested workflow edited after attestation; 4 store-backed `experiments/` subjects that `claim_inputs.py` never pulls; 7 offline-only | Same claim-creation check; extend `claim_inputs.py` to `experiments/` |
| cryptanalysis `bench-records` | Progress SVG and PDF became store-backed; `progress_stale` counts a missing file as stale. The rendered bytes match the manifest digests | Keep progress files in Git, or compare the rendered hash with the manifest digest |

## 4. New findings

### 4.1 Validation machinery

| Id | Sev | Finding | Tag |
|---|---|---|---|
| G-1 | Critical | crypto has no pcc gate (`pcc-gate.yml` deleted 2026-11-16); `AGENTS.md:309`, `.github/CI.md:299`, `docs/SABOTAGE_RESISTANCE.md` and `draft_tier_gate.py:41` still describe it | O |
| G-2 | Critical | No required status checks on either repository's main (`.github/CI.md:223`); red PRs merge, so every gate is advisory | O, inferred |
| G-3 | Critical | The tolerance cap was reverted by #4394 the evening it landed, with its tests | O |
| G-4 | Critical | Sweep verdict files are store-backed; `validation-gate.yml` does not pull them, so `load_verdicts` sees none and the append-only check compares nothing. #1850 moved the A file out of Git; its 55 lines include `contradicted` | D |
| G-5 | High | A sweep verdict may borrow another row's passing artefacts (V-3 variation) | D |
| G-6 | High | The gate code and workflows run from the PR head; crypto has no CODEOWNERS. A PR can weaken the checker and pass it | R |
| G-7 | High | Keyring trust can be laundered after one unpinned keyring merge (V-1 variations B, C); the sign job should refuse to run without a pin | D |
| G-8 | Medium | 2,554 of 3,544 crypto claim files have no ledger registration (V-13 grew from 9) | D |
| G-9 | Medium | `pcc claim new` pins any file under any proof kind without a structural check | D |
| G-10 | Medium | Unreadable base blobs fail open in `pcc.py:149` and `validation_gate.py:639` | D |
| G-11 | Medium | Shared files have drifted although each repository's own parity check passes: `tools/pcc/pcc.py`, `tools/pcc/test_pcc.py` and `tools/artifacts/artifacts.py` differ between crypto (owner) and cryptanalysis, and the two lock files differ (first pass C-13) | O |
| G-12 | Low | Neither `PRE_GATE.json` has `expires`; session logs have grown to 1.7M lines (`docs/session-logs/2026-11-17.md`) with repeated entries | O |

### 4.2 CI

| Id | Status | Detail |
|---|---|---|
| C-1 | Worse | No PR job runs root `cargo test --lib`; 31 of 42 `tests/*.rs` are named by no workflow |
| C-2 | Partly fixed | 27 test scripts run in no workflow, including `tools/pcc/test_pcc.py` (now that the pcc gate is gone) |
| C-3 | Unchanged | lean-proof-gate, ic-leaderboard, audit-runs-daily and codeql still do not run on PRs; codeql has no schedule |
| C-6 | Worse | Long-lived `ARTIFACTS_AWS_*` keys reach steps in 31 crypto and 138 cryptanalysis PR-triggered workflows; OIDC in 11 and 0 |
| C-7 | Unchanged | Retired workflows still PR-triggered and documented as guards |
| C-10 | Worse | 2,738 action references pinned to a tag or branch, 315 to a SHA |
| C-12 | Worse | 365 of 685 crypto workflows and 103 of 332 cryptanalysis workflows never fire on a PR, main or a schedule |
| C-13 | Worse | See G-11 |

### 4.3 Rust (crypto)

R-1, R-2, R-3, R-5..R-10 are all still present (R-5 now panics instead of skipping silently).

| Id | Sev | Finding | Tag |
|---|---|---|---|
| RS-1 | High | The bitop/v1 and v2 work blocks charge zero group operations for the search walk and internal verification of the `_v2`+ rho ids (`rho.negation_v2..v6`, `rho.plain_v3..v6`, `rho.signed_frobenius_v2..v5`, `_v2` quartic/cubic, `rho.multitarget_pooled`). `rho_report_v2` (`ecbench/methods.rs:2500-2526`) sets `gae` but leaves `adds`/`doubles` at 0, and `gae_carries_group_ops` (`ecbench/work.rs:823`) lists only the original eight ids. No committed bitop bound uses these ids yet; any future one would show a nearly free rho reference | R, data |
| RS-2 | Medium | The challenge epoch beacon is never checked as a commit containing the commitment (`ecbench/challenge.rs:323-353`), so the epoch, and with it the targets, can be ground | R |
| RS-3 | Medium | Target-dependent rho set-up (G+Q, jumps from Q) is classed as reusable (`work.rs:116-127`); amortised per-target cost is understated, and `ecbench amortize` trusts the stored split | R |
| RS-4 | Medium | `vs_rho` claims use one chosen round; the paired aggregate drops failed and timed-out rounds without counting them (`claim.rs:961-1118`). Committed single-round `online_speedup` values range from 0.105 to 12.19 for the same configurations | R, data |
| RS-5 | Medium-low | "Order holds across the band" uses point ratios only (`compare.rs:953-962`); progress summaries print "band-robust" next to an interval computed only at weight 0. `challenge.rs` itself uses per-weight intervals | R |
| RS-6 | Low-medium | rho.plain and rho.negation references declare no unpriced table work, so their distinguished-point probes are never priced in the band (0.4–7% of GAE at 4–32 bits) | R, data |
| RS-7 | Low | A verdict's "exponent" level is decided from weight-0 fits even when unpriced work is present (`challenge.rs:1199-1210`) | R |
| RS-8 | Low | Version-1 bounds stay "admissible" with interrupted sessions (`bounds.rs:1828-1854`) | R |

### 4.4 C library (cryptanalysis)

Release and ASan+UBSan: 22/22 tests pass. Every finding below was run with a reproducer.

| Id | Sev | Finding |
|---|---|---|
| C-F1 | High | `rho.c:1151` clamps `dp_bits` only to 58, and the S-2 guard grows by `2^dp`. A solvable instance (n = 500001) with `dp_bits = 16` returns NOT_FOUND with "target is not a power of the base"; with 30 it runs past 60 s; `gpu_rho.c` likewise. Fix: clamp to about log2(n)/2 − 2 |
| C-F2 | Medium | `kangaroo.c:259-333` does not clamp the interval to the group order; [0, 2^64−1] with n ≈ 10^6 hangs with default parameters |
| C-F3 | Medium | Grumpy giants (`grumpy.c:382`) runs O(n) time and memory on an unsolvable target (1.15 GB at n = 2^24); it has no membership check and no square-root guard |
| C-F4 | Medium | `linalg.c:1372-1390`: the dense fallback solves the normal equations and returns CA_OK with x that does not satisfy A·x = b on an inconsistent system. Index calculus verifies logs downstream |
| C-F5 | Medium | GLV batch start-up modes return CA_ERR_INTERNAL for n ≥ 2^39 (`curve.c:860` allows 128 points, `ec_tau.c:3435` refuses more than 32) |
| C-F6 | Medium | `coord.c:1236-1245`: a forged empty check-in under the victim's (peer, seq) makes the real one be dropped; peer names are unauthenticated |
| C-F7 | Medium | Sequence numbers overflow: a forged `UINT64_MAX` wraps the victim's next seq; `strtoull` accepts "-1" |
| C-F8 | Medium | `coord.c:1257` sums unverified step claims; one peer can wrap `progress.steps` |
| C-F9..F12 | Low | `ca_crt2` SIGFPE on a zero modulus; a forged `walkers_done` marks units complete; `ca_bench` divides the complexity table by all runs but sums only successful ones; coordinator walker start-up is not counted in `steps` |

No defect was found in `ec_tau.c`: 810,820 differential checks on 71 j=0 curves, 0 failures.

## 5. Recommended order

1. **Make checks binding.** Restore crypto's `pcc-gate.yml` (with the keyring trust root), then turn on required
   status checks for both repositories' `main`. Have the gates run their code from the base revision, not the PR head.
2. **Restore the artifact store.** Until it is back, every evidence check is red for everyone and carries no signal.
3. **Repair main's data.**
   - The 151 untyped claims, then a registration check that fails on any unregistered claim file.
   - The malformed bench record and the crash it causes.
   - The three edited lessons entries.
   - The `test_pcc.py` call.
   - `claim new` structural checks.
4. **Re-land the tolerance cap** with the pre-cap list keyed by path and digest, and keep sweep verdict files in Git.
5. **Fix C-F1** (my incomplete S-2 repair) together with C-F2 to C-F5. Fix RS-1 before any bitop bound of a `_v2`+ rho
   id is published.
6. **Re-sync the shared files**, and make the parity check compare across repositories, not each against its own lock.

## 6. Limits

- Both clones are shallow (history from 2026-11-16). The commit that deleted `pcc-gate.yml` and the origin of the
  151 claims are beyond the boundary.
- No view of GitHub settings: "not required" is inferred from merges and from `.github/CI.md`.
- No artifact store access (it returns 403 for CI as well).
- `crypto-autoresearcher` is stored encrypted in this session, so three-way parity was not checked.
- The root Rust crate was not built (disk and memory). Rust findings rest on reading the code, small standalone
  reproducers and committed records.
- Not reviewed in this pass: most of `koblitz_index_calculus.rs`, Wiedemann/Lanczos internals, the rest of
  `ic_framework`, `coord_net.c`, `cuda/` and `gpu/`, and V-5 to V-9 and V-11 onwards.

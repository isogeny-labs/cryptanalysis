# J3 integration review — TASK-20261029-9058ad

**Verdict: holds within the declared trusted-tool and stable-workspace boundaries. Native proof validity: `not_verified`.** The final Python admission route enforces exactly four audited theorems and the four required qualified names. The integration retains the prior source and project-byte protections, persistent-mutation refusals, workflow lockfile routes, and the main-origin refusal controls present in the final test suite. I found no new admission bypass within those boundaries. The deliberately inconsistent-output and transient-change probes below remain accepted and limit the verdict.

This is an independent J3 software/verifier review of producer `5b20d2a705601327877f708655f37b92bc762da8`, under the supplied prospective review commit `1aa4e3e26`. It is not a native Lean proof review or an independent mathematical derivation. The producer and commit identifiers are supplied provenance; I did not read Git history or remote state. The identities independently checked here are the allowlisted file hashes.

The ten producer hashes in `inputs-v3.json` matched. All fifteen allowed source files, including the handoff, plans, archived diff, and expressly permitted prior J3 report, were hashed before and after controls and were unchanged. The complete paths and hashes are in `source-ledger.json`. The final gate SHA-256 is `bb5410ceb8c90d27bf1ff373c0ff4036d0f4542abc0b41c14088895a73bb5d26`; the fixed Algebra source SHA-256 is `d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d`.

The bounded existing suite passed **26 tests**, exit zero. My new diagnostic completed **46 mock cases**, with **40 refusals and 6 acceptances**, all matching the stated expectations. The six accepted cases were the valid direct baseline, valid exact-path dispatch, and four explicit trust-boundary probes. A separate real Python child exiting 7 was refused by the unmodified generic subprocess adapter. No Lean compiler or auditor process ran.

| Admission property | Independent control result | Interpretation |
| --- | --- | --- |
| Audit cardinality 3 / 4 / 5 with matching row counts | Refused / accepted / refused | Exactly four is enforced at `current-corpus-gate.py:422–425`. |
| Three or five `ok` rows paired with summary count four | Both refused | Summary and row-count consistency survives integration. |
| Correct short names in the wrong compiler namespace | Refused | Fully qualified compiler names must match the fixed set. |
| Wrong auditor namespace, missing compiler name, duplicate audit name | All refused | Count alone cannot substitute for the required names. |
| Empty, zero-theorem, duplicate-summary, failed-summary, trusted-summary audits | All refused | Applicable refusal cases remain active. |
| Nonstandard axiom in compiler output | Refused | The Python compiler-output allowlist remains enforced. |
| Nonzero compiler or auditor exit | Both refused | The real `run` adapter was exercised with mocked subprocess results. |
| Changed, missing, or symlinked fixed source | All refused | Source identity and final-component symlink checks remain active. |
| Persistent source change during either compile or audit | Both refused | Final source hashing still prevents admission. |
| Changed, missing, or symlinked project inputs | All nine refused | All three required files remain bound before commands. |
| Persistent project-input mutation during compile and audit | All six refused | Both command phases and all three bound files were covered. |
| Exact known-label dispatch / another documentation path / unknown bare Hecke path | Accepted / refused / refused | The added dispatch remains confined to the declared source path. |
| Changed toolchain or Mathlib revision on dispatch | Both refused | Upstream dispatch pin checks still fail before compilation. |
| Lockfile-only workflow routing | Matches `**/lake-manifest.json` in both `pull_request` and `push` | Static event-filter coverage holds; no hosted event was exercised. |

The six persistent project mutations each appended a newline to a scratch copy at one mocked native-command boundary. The source retained its correct hash. Every case failed with `known-label project input changed: <filename>`.

| Input | During compile | During audit |
| --- | --- | --- |
| `lean-toolchain` | Refused | Refused |
| `lakefile.toml` | Refused | Refused |
| `lake-manifest.json` | Refused | Refused |

To check the source-aware integration without reading Git history, I reversed the allowlisted archived diff against the current files in scratch. Both current and reconstructed prior Git blob identities match the diff's stated prefixes. The current gate blob is `12c0b546a2478ae5594d0146b546fa478eeba4a6`; reconstructed prior is `1d35123047cb23aba03140a58de3394cc3b8a01f`. The corresponding test blobs are `b51c45716c54268ac1ed317e801848bb70b36dd5` and `5b4d4a79c5831c76cf86c7e2870079de2711d8ea`. Full reconstruction details are in `integration-diff-check.json`. This verifies the content relationship expressed by that archived diff; it does not independently establish branch ancestry.

That diff adds the `expected_theorems=4` argument and the associated requested/audited count check while retaining the pre/post `check_known_label_project_inputs` calls, source hashing, exact compiler-name set, auditor-name inclusion, allowed compiler axioms, and failure propagation. The final suite retains the six prior quartic-registration controls, the prior known-label controls including all six persistent mutation subcases, the imported main-origin known-label controls, and the new five-theorem refusal control. All passed. The new fixed count plus four distinct required names also makes the previous audit-name inclusion check exact for this path: four `ok` rows cannot contain all four required names and an additional distinct name.

The final route is `main` → tracked Lean additions → `check_new_hecke` → exact known-label dispatch → project checks → source-bound compilation and module audit → source and project rechecks. Relevant locations are `current-corpus-gate.py:359–375`, `:378–433`, `:436–456`, and `:543–574`. I inspected `main` statically; executing it would exceed the allowlist and launch native work. The direct and dispatch mock controls exercise the same known-label functions. They record the original source compile argument, isolated `.olean` output, exact module name, project working directory, and auditor `LEAN_PATH` in `control-results.json`. Mocks do not establish that any `.olean` was emitted or loaded.

`AuditHeckeAxioms.lean:16–40` imports requested modules, enumerates their non-internal `.thmInfo` declarations, collects transitive axioms, and permits only `propext`, `Classical.choice`, and `Quot.sound`. Empty modules and any bad axiom return failure. The workflow's corpus gate step is unconditional and has no `continue-on-error` or success-forcing suffix (`lean-proof-gate.yml:92–96`). A success-looking printed audit line can precede a later source/project failure; process or job success must determine admission. The native positive, assumed-false, empty, and ill-typed controls remain defined in `hecke-audit-selftest.py:21–40`; their source was read but they were not executed.

Four accepted adversarial probes describe retained limits:

1. **Contradictory auditor transcript:** four good rows and a zero-failure summary, followed by a fabricated `FAIL` row, with process exit zero, is accepted. This repeats the prior J3 output-protocol boundary. The declared auditor increments its failure count and returns nonzero when it produces a real bad-axiom row.
2. **Forged auditor `ok` axioms:** replacing the standard axiom list in all `ok` rows with `ClaimAsAxiom`, while preserving names, count, zero-failure summary, and exit zero, is accepted by Python. The Python layer validates the compiler's axiom lists but trusts the native auditor's interpretation of its own `ok` rows. The unmodified auditor's source cannot normally emit such an `ok` row for a collected nonstandard axiom. This is a protocol-trust demonstration, not a native bad-axiom acceptance.
3. **Transient source change:** a mock compile boundary changes the fixed source, then the mock audit boundary restores it before final hashing. The wrapper accepts. No actual compilation of altered bytes occurred in this probe.
4. **Transient project change:** the same change-and-restore sequence for `lakefile.toml` is accepted. Pre/post hashes establish endpoint identity and detect persistent changes; they do not provide an atomic snapshot against a concurrent writer.

Installed Lean/Lake executables, the dependency cache, imported binaries, executable lookup, and the inherited environment remain trusted. The project pins are Lean `leanprover/lean4:v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`; this route does not hash installed tools, force an `ELAN_TOOLCHAIN` override, or independently certify the cache. `trustLevel := 0` is not a separate proof-replay receipt. The workflow's Hecke detector still recognizes `experiments/hecke-*/formal/*`; the known-label documentation file alone would not enable conditional cache setup or native selftests. Actual tracked inventory, hosted routing, branch protection, and CI results were outside this review. The gate also does not require the known-label addition to remain present in the tracked inventory if removed; no global manifest-completeness claim is made here.

The parent supplied a procedural clarification after dispatch: v3 plan bookkeeping inherited stale round/prior-plan/reuse prose; the new J3 handoff, manifest, and diff are the intended inputs. The parent stated that two README files changed upstream, while Algebra and CHECKS stayed exact, and that original J2 evidence certifies only historical source statements. I did not read the README files, CHECKS, J1/J2 evidence, or the promised additive correction, and do not independently validate those supplied facts. The handoff and explicit `prior_j3_access` permission govern access to the one archived J3 report despite the inherited blind-mathematics forbidden-list entry. This reviewer did not perform a blind mathematical derivation or claim new J1/J2 evidence.

All review writes were confined to `/home/ec2-user/scratch/known-label-review-20261028/TASK-20261029-9058ad/`. No repository file was edited. No memory, sibling J1/J2 report, blind brief, coordinator report, unlisted repository path, native CI output, or Git history was read. No additional agent, native build, experiment, benchmark, external job, cloud action, or PR action was launched. Python bytecode generation was disabled and temporary fixtures were confined to this scratch directory. **Execution deviations: none.** The post-dispatch plan clarification is recorded as supplied procedural context rather than as a broadened authorization.

Reproduction commands, from the review worktree:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/ec2-user/scratch/known-label-review-20261028/TASK-20261029-9058ad/tmp python3 -B tools/lean/test_current_corpus_gate.py -v
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/ec2-user/scratch/known-label-review-20261028/TASK-20261029-9058ad/tmp python3 -B /home/ec2-user/scratch/known-label-review-20261028/TASK-20261029-9058ad/independent-controls.py
```

`existing-tests.txt` captures the full existing-suite output. `controls-output.txt` captures the full independent diagnostic output, including all mocked transcripts and command arguments. `control-results.json` records machine-readable case results. `source-ledger.json`, `integration-diff-check.json`, and `artifact-hashes.json` provide the input and output bindings. `attestation.json` carries the `review_attestation` wrapper and complete source path strings.

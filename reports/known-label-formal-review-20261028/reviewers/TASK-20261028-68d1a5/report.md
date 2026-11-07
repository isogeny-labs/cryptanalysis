# J3 affected-joint re-review — TASK-20261028-68d1a5

**Verdict: holds within the declared trusted-tool boundary and the stable-workspace assumption described below.** The revised producer repairs both original J3 findings. The six persistent project-mutation probes now refuse admission, and a manifest-only change matches both automatic workflow event filters. The other applicable refusal controls still hold. **Actual native proof validity remains `not_verified`**; no Lean invocation or native CI result was used in this review.

This review covers **J3 only**, producer `0b353c9bf78e9340c3c100b71175127bb7d91d44`, under the prospective plan supplied as commit `35ed5772e98fb3c8754b7fb6367d7ae1ebd83188`. Archive owner: `TASK-20261028-871ca0`; Conductor task: `T-765`. The reviewer continued its isolated J3 review session with expressly authorized access to its own prior report and diagnostic. This is an affected-joint re-review by the same reviewer, not a claimed additional independent opinion. No J1/J2 report or blind brief was read.

The allowed producer inputs were bound directly against `inputs-v2.json`: all eleven applicable SHA-256 values matched initially and at close. Git commit ancestry and remote PR/CI state were not read under the declared-input-only restriction. The producer and plan commit identifiers above are supplied provenance; the independently checked source identities are recorded in `source-ledger.json`.

## Disposition of the original findings

| Original finding | Revised evidence | Disposition |
| --- | --- | --- |
| J3-F1: project inputs changed during native commands could still return the accepted digest | `check_known_label_algebra` invokes `check_known_label_project_inputs()` both before and after `check_pinned_mathlib_source` (`tools/lean/current-corpus-gate.py:359–374`). All six original mutation cases now raise `ValueError` naming the changed project file. | Repaired for persistent changes to each bound file during either command. |
| J3-F2: manifest-only change matched neither automatic event filter | `.github/workflows/lean-proof-gate.yml:11` and `:28` contain `**/lake-manifest.json`; the known project manifest matches that pattern in both `pull_request` and `push`. | Repaired at the static workflow routing level. |

For F1, I copied the **unchanged original independent diagnostic** from its authorized archived location into this new task's scratch directory. Its SHA-256 remains `016885c16cf3e07cf5427f79ab3485fc273602bad8c131413e64a1e0b7080632`. The diagnostic loads the revised gate from the review worktree, copies only permitted source/project files into new scratch fixtures, and mocks the compiler and auditor subprocess outputs. At each selected native-command boundary it appends a newline to one project file. The revised wrapper rejects all six cases:

| Input changed | During compilation | During module audit |
| --- | --- | --- |
| `lean-toolchain` | Refused | Refused |
| `lakefile.toml` | Refused | Refused |
| `lake-manifest.json` | Refused | Refused |

The exact error is `known-label project input changed: <filename>`. In each case, the source hash remains correct and the fixture's changed project hash remains incorrect. This directly closes the prior false acceptance without changing the diagnostic or producer files. The revised test suite also has a six-subcase regression control at `test_current_corpus_gate.py:209–226`.

For F2, the diagnostic independently extracts each event's path list and matches the actual project manifest path. Both results are exactly `["**/lake-manifest.json"]`. This establishes coverage by the declared filters; it does not claim that a hosted event was dispatched or completed. Branch protection and merge policy were outside the permitted inputs.

## Executed results

The revised existing suite passed **19 tests**: 13 known-label tests and 6 quartic-registration tests. Its new test includes the six mutation subcases. Full stdout/stderr is in `existing-tests.txt`; process exit status was zero.

The independent diagnostic completed **21 cases**, with **19 refusals and 2 acceptances**. The refused cases cover the six repaired mutations, prechanged project files, a wrong source path, changed source hash, wrong fully qualified theorem namespaces in each output stream, empty and zero-theorem audits, a nonstandard printed axiom, a nonzero native-auditor result, persistent source mutation during audit, and a real trivial Python subprocess exiting 7. The two acceptances were:

- The expected valid mock baseline.
- The original deliberately contradictory mock auditor output, discussed below as a trusted-output boundary rather than a demonstrated bypass of the declared auditor.

No unexpected test failure occurred. `diagnostic-output.json` retains every case, including the contradictory-output acceptance. `review-results.json` records the summary and assertions confirming all six repaired refusals and both lockfile routes.

Reproduction from the review worktree:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/ec2-user/scratch/known-label-review-20261028/TASK-20261028-68d1a5/tmp python3 -B tools/lean/test_current_corpus_gate.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B /home/ec2-user/scratch/known-label-review-20261028/TASK-20261028-68d1a5/diagnostic.py
```

These commands exercise Python admission behavior. Their compiler/auditor outputs are mocked and provide no Lean proof evidence. The diagnostic's only real child-program refusal control is a trivial Python process returning exit code 7.

## Regression trace of the J3 path

The reviewed route remains `main` → tracked Lean additions → `check_new_hecke` → exact known-label dispatch → `check_known_label_algebra` → fixed-source compilation and module audit → final project checks. `main` uses tracked paths and does not require this particular addition to exist if it is removed from the inventory (`current-corpus-gate.py:537–568`). I inspected that route statically and did not execute `main`, which would read undeclared historical artifacts and launch builds.

The source is still restricted to `docs/known-label-next-leads-20261028/Algebra.lean` with SHA-256 `d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d`. The four required names remain the exact `KnownLabelLeads.triangle_identity`, `KnownLabelLeads.signed_second_moment`, `KnownLabelLeads.signed_third_moment`, and `KnownLabelLeads.positive_pair_product`. The source path must resolve inside the repository, its final component must not be a symlink, and its hash is checked before and after the native-command sequence. Persistent source mutation is still rejected.

The gate still constructs a private output `TEMP/docs/known-label-next-leads-20261028/Algebra.olean`, compiles the original source using `lake env lean -R ROOT`, and audits module `docs.known-label-next-leads-20261028.Algebra`. The temporary root leads the auditor's `LEAN_PATH`. The existing command-shape test and independent baseline confirm these arguments. Neither mock proves an `.olean` was emitted or loaded.

`AuditHeckeAxioms.lean` retains its original hash. It enumerates non-internal `.thmInfo` declarations belonging to the requested module, applies transitive `collectAxioms`, and allows only `propext`, `Classical.choice`, and `Quot.sound`. Zero theorems and bad axioms return failure. The Python layer requires complete exact-name printouts, a positive audit count, one zero-failing/zero-trusted summary, matching `ok` line count, and inclusion of the four required theorem names. It permits additional non-internal theorems if audited successfully; it does not enumerate every imported or unreferenced internal declaration.

The subprocess wrapper still raises on nonzero exit codes. Exceptions propagate through the gate; the workflow gate step has neither `continue-on-error` nor a success-forcing suffix. Audit output may already be printed before the new final project check fails, so admission must use the overall process/job outcome rather than the presence of a success-looking log line. The new post-check does not erase an earlier failure.

## Retained trust boundaries and limits

1. **Before/after hashing is not an atomic snapshot.** The repair detects changes that persist until the final project check. It does not exclude a project or source change that is restored before return, or guarantee that every byte consumed while commands ran came from an immutable snapshot. The same static limitation was disclosed in the original report. The verdict assumes a stable workspace during trusted command execution; it is not an authentication guarantee against an adversarial concurrent writer. No transient-restore native attack was run.
2. **Installed tools and dependencies remain trusted.** The checked project text specifies Lean `leanprover/lean4:v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. Installed executable identities and dependency binaries are not independently hashed or rechecked by this gate. The auditor's `trustLevel := 0` import is not an independent `lean4checker` receipt. The inherited environment and executable lookup must resolve the intended trusted toolchain; this route does not force `ELAN_TOOLCHAIN` or record runtime Lean version output.
3. **The auditor output protocol is trusted.** The preserved diagnostic supplies a fabricated `FAIL` line alongside four good lines, a zero-failure summary, and process exit zero; Python still accepts it. The declared native auditor increments its bad count and exits nonzero for an actual bad axiom, so this inconsistent output is not produced by its normal success path. The probe identifies dependence on that trusted process; it is not evidence that the unmodified auditor accepts a nonstandard axiom.
4. **The Hecke detector still depends on the broader inventory.** It only tests `experiments/hecke-*/formal/*` (`lean-proof-gate.yml:70–72`); the known-label file alone would not enable conditional cache preparation or native Hecke controls. The allowed quartic manifest lists numerous Hecke formal sources, while the corpus gate itself is unconditional. This is a retained inventory coupling, not a demonstrated skip in this producer. Actual tracked inventory outside the declared files was not inspected.
5. **Native evidence remains separate.** `hecke-audit-selftest.py` still defines native positive, assumed-false, empty-module, and ill-typed controls. Its source was inspected, but it was not executed. No old CI result was reused for the new head, and no new CI result was read. Exact-head compilation, native theorem/axiom outputs, and those native controls remain coordinator-owned evidence requirements.

## Provenance and procedure

`sources_read` in the new attestation is a complete list of **16 path strings**. Rich hashes and access details are separate. The list consists of the new handoff, its declared inputs, and the two explicitly allowed archived artifacts from the reviewer's own prior task. The archived report and diagnostic match their original hashes. Original task outputs were never edited or executed in place.

The prescribed plan contains coordinator summaries of the existing program; those were encountered while reading the required plan. No J1/J2 report, underlying finding artifact, or blind brief was opened or used for a J3 judgment. No memory, unrelated repository source, or linked document outside the allowed inputs was read.

**Current-review deviations: none.** All writes were confined to `/home/ec2-user/scratch/known-label-review-20261028/TASK-20261028-68d1a5/`. All eleven permitted producer hashes and both prior archived artifact hashes remained unchanged at close. No Lean/Mathlib build, experiment, benchmark, external job, cloud action, source edit, PR mutation, or agent spawning occurred. The original findings remain preserved as historical findings on the original producer; their repaired disposition applies only to the revised source bytes reviewed here.

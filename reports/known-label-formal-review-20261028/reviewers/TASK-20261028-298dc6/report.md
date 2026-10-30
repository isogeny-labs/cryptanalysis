# Independent J3 review — TASK-20261028-298dc6

**Verdict: breaks, scoped to the complete project-pin and CI-routing guarantee.** The fixed-source selector, theorem-name checks, nonempty audit requirement, and subprocess failure propagation held in the permitted lightweight probes. Two narrower defects remain: project inputs are checked only before native execution, and a change confined to `lake-manifest.json` matches neither automatic workflow event filter. These findings do **not** demonstrate acceptance of an invalid Lean theorem. Native proof validity remains **not_verified** in this review.

Reviewed producer: `ffeacb44b6a151aebc84619f30a70591eb44e0f6`. Prospective review-plan commit supplied at dispatch: `dcebcd1842d112ebc3d985f02245cf0a8b7a8391`. Owned joint: **J3 only**. Archive owner: `TASK-20261028-871ca0`; Conductor task: `T-765`. Repository: `/var/tmp/cryptanalysis-known-label-review-20261028`. Commit ancestry and remote CI were not independently read because this review was restricted to declared input files; the eleven permitted producer files with declared hashes all matched `inputs.json` both initially and at close.

## Concrete findings

### J3-F1 — Project inputs can change after admission and still return the accepted source digest

`check_known_label_algebra` hashes `lean-toolchain`, `lakefile.toml`, and `lake-manifest.json` at `tools/lean/current-corpus-gate.py:359–367`. It then returns the result of `check_pinned_mathlib_source`. That routine runs compilation and the module audit, then rehashes **only the Lean source** at lines 419–420. No project-input check follows either subprocess.

The independent `diagnostic.py` copies the fixed source and the three project inputs into scratch. Its mocked subprocess boundary appends one newline to a project input while the build or auditor is running, then supplies the same successful theorem printouts as the baseline. In each of six cases—three files times two stages—the unchanged producer gate returns:

```text
d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d
```

At return, the source hash still matches, while the modified project file's hash does not. The paired control changing the same file before entry is rejected before compilation. Thus the discrepancy concerns the timing of input binding, independently of the mocked output format. A newline is sufficient because the documented policy binds exact project bytes; this probe does not claim a changed effective dependency was actually loaded by Lean.

The practical precondition is a mutable shared workspace or a subprocess that changes these files after admission. Ordinary unchanged CI execution may never hit this case. The current implementation consequently needs an explicit stable-workspace assumption for its pin guarantee. Recheck all three inputs after native execution, and preferably execute from a fixed project snapshot if protection against transient changes during execution is required. An end check alone will not detect a change that is restored before return.

Evidence: `diagnostic-output.json`, cases `lean-toolchain_mutated_during_build`, `lean-toolchain_mutated_during_audit`, `lakefile.toml_mutated_during_build`, `lakefile.toml_mutated_during_audit`, `lake-manifest.json_mutated_during_build`, and `lake-manifest.json_mutated_during_audit`. All six have `decision: accepted`, `source_hash_matches: true`, and one false `project_hashes_match` value. Producer repository files were never mutated.

### J3-F2 — A manifest-only change has no automatic workflow route

`.github/workflows/lean-proof-gate.yml:6–19` and `:22–35` filter `pull_request` and `push` events. Both include `**/lean-toolchain`, `**/lakefile.toml`, and `**/lakefile.lean`; neither includes `**/lake-manifest.json`. No other listed path matches `experiments/hecke-432-formal-ci-20261025/lake-manifest.json`.

The gate correctly rejects changed manifest bytes **when invoked**, as demonstrated by the existing tests and the independent `prechanged_lake-manifest.json` probe. The automatic routing does not cover a PR or push whose only relevant changed file is that manifest. Add `**/lake-manifest.json` to both event path lists. A manually dispatched workflow or a change to another covered file can still run the gate. This finding does not establish a merge bypass: branch-protection settings were not among the permitted inputs and were not inspected.

Evidence: `diagnostic-output.json` → `workflow_event_pattern_matches`; both event entries have an empty list for `lake-manifest.json` and a matching pattern for each of the other two bound project files. This is a local inspection of the declared filters, not a hosted event execution.

## Admission path and checks that held

1. **Discovery and exact selection.** `main` lists tracked `*.lean`, excludes `tools/lean/`, subtracts the frozen corpus, and passes remaining additions to `check_new_hecke` (`current-corpus-gate.py:530–560`). The exact known-label path is handled at lines 438–440 before the generic Hecke fallback. An adjacent `Other.lean` path is rejected. The main routine does not assert that this particular addition must exist forever; its checked set follows tracked inventory. I did not run `main`, which would access undeclared historical artifacts and launch native builds.
2. **Initial source and project binding.** The three project-file hashes are fixed independently of the quartic manifest. The original source path must resolve inside the repository, its final component cannot be a symlink, and its SHA-256 must match. Existing matching-byte symlink controls pass. The fixed source is checked again after execution; persistent source mutation during audit is rejected. Ancestor project-directory symlinks and concurrent restoration attacks are not independently excluded by these checks.
3. **Private module output.** Compilation uses `lake env lean -R ROOT -o TEMP/docs/known-label-next-leads-20261028/Algebra.olean ORIGINAL_SOURCE`, with the pinned project as working directory. The auditor's `LEAN_PATH` starts with the unique temporary root, followed by the dependency path obtained from `lake env printenv LEAN_PATH`. The module argument is exactly `docs.known-label-next-leads-20261028.Algebra`. Both the existing test and the independent baseline inspect this command construction. Mocked commands do not establish that Lean actually emitted or loaded that module.
4. **Printed declarations.** The fixed source contains four `#print axioms` requests. The Python gate requires complete printout count, matching short names, the four exact fully qualified `KnownLabelLeads.*` names, and only `propext`, `Classical.choice`, or `Quot.sound`. Independent wrong namespace and `sorryAx` printouts are rejected. Pinning the whole source prevents a newly introduced source-level print-spoofing command from entering through this admission without a hash change.
5. **Native auditor design.** `AuditHeckeAxioms.lean:14–26` constructs hierarchical module names component by component, imports the requested root, and collects `.thmInfo` entries whose owning module is a root and whose name is non-internal. For each it calls `collectAxioms` and allows only the three standard axioms. It returns failure for any bad axiom or zero theorems (`:27–40`). This is an audit of all **non-internal theorems in the selected module**, with transitive axiom collection for those theorems. It is not enumeration of all imported declarations or all unreferenced internal declarations. Internal helpers reached from an audited theorem remain inside that theorem's transitive dependency question.
6. **Audit result checks.** The Python layer requires one positive-size, zero-failing, zero-trusted summary, the matching number of `ok` lines, and inclusion of all four required theorem names. Independent empty, zero, and wrong-name audit output is rejected. Extra legitimate non-internal theorems are permitted if the native auditor checks them; the gate does not insist the module contain exactly four theorems.
7. **Failure propagation.** The subprocess wrapper rejects nonzero return codes. The independent probe exercised this both through the auditor stub with exit 1 and through a real trivial Python subprocess exiting 7. Exceptions escape the gate entry point; the workflow has no `continue-on-error` or success-forcing suffix on its gate step. The native selftest follows the gate, so a previous failing step prevents a successful job rather than being erased by later success.

## Trust boundaries and remaining limits

- The declared trust boundary includes the installed Lean/Lake executables and imported dependency binaries. The project text pins Lean `leanprover/lean4:v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. The gate does not independently hash or recheck those installed binaries. `importModules ... (trustLevel := 0)` in the auditor is not an independent `lean4checker` receipt. Neither executable identities nor package cache contents were inspected here.
- Compilation and auditing inherit the process environment and executable resolution. The gate does not set a fixed `ELAN_TOOLCHAIN` for this route or record the runtime Lean version. The pin guarantee therefore assumes the resolved trusted tools honor the checked workspace configuration and are not overridden by the environment. No native override attack was attempted.
- The Python audit parser trusts the auditor's exit code and summary consistency. A deliberately contradictory mocked stdout containing a `FAIL` line plus four good `ok` lines and a zero-failure summary is accepted if the mocked process exits zero. The declared native auditor increments its failure count and exits nonzero for a real bad axiom, so this synthetic case is **not** evidence of a bypass using that auditor. It identifies the trusted-output boundary; the Python wrapper does not independently re-derive audit truth from arbitrary text.
- The workflow's Hecke detector looks only for `experiments/hecke-*/formal/*` (`lean-proof-gate.yml:68–70`). The known-label path alone would not trigger Mathlib-cache preparation or the Hecke native control step. The declared quartic inventory contains numerous Hecke formal paths, so this is a latent coupling to the broader repository inventory, not a demonstrated skip at the reviewed producer. The corpus gate itself is unconditional and would still try its known-label route if the file were listed.
- `hecke-audit-selftest.py` statically defines four native controls: a valid reflexivity theorem, an assumed false theorem requiring a custom axiom, an empty theorem module, and an ill-typed false theorem. I read its implementation but did not run it, as native Lean execution/builds were prohibited. The plan's expected CI run `40739043598`, job `122995320061`, was pending at dispatch; no terminal result was accessed or inferred.

## Executed evidence and reproduction

The existing suite completed with **18 tests passed**. It includes 12 known-label and 6 quartic registration controls. All compiler/auditor behavior in that suite is mocked; it establishes Python admission behavior only. Full stdout/stderr is retained in `existing-tests.txt`.

The independent diagnostic completed **21 cases**: 13 refusals, one accepted valid mock baseline, six accepted post-admission project mutations, and one accepted contradictory untrusted-output boundary probe. One of the 13 refusals used the real trivial Python subprocess. No Lean, Lake, Mathlib build, experiment, benchmark, cloud action, PR action, or delegated agent ran.

```sh
cd /var/tmp/cryptanalysis-known-label-review-20261028
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/ec2-user/scratch/known-label-review-20261028/TASK-20261028-298dc6/tmp python3 -B tools/lean/test_current_corpus_gate.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B /home/ec2-user/scratch/known-label-review-20261028/TASK-20261028-298dc6/diagnostic.py
```

The diagnostic writes only into its assigned output directory and removes temporary copied fixtures. Its complete generated decisions are in `diagnostic-output.json`; the initial/closing producer bindings and the complete read inventory are in `source-ledger.json`. All fourteen read paths are declared handoff inputs, the handoff itself, or the explicitly permitted `Algebra.lean` extension needed by existing tests. No linked README/CHECKS, sibling review, blind brief, memory file, or other repository source was opened.

**Procedure deviations: none.** Reading the exact `Algebra.lean` was the explicitly authorized test dependency and is recorded in the attestation. Producer bytes remained unchanged; all eleven hash-bound permitted files matched the declared producer hashes after testing. Overall J3 is not accepted without qualifying or repairing F1/F2, while actual proof validity is reserved for exact-head native CI evidence owned by the coordinator.

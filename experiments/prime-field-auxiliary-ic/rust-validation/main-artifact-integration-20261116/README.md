# Current-main artifact integration

PR #1536 acquired a merge conflict after main advanced to
`df5156fc93413ce4d48b0c300549e0b5db3575c6`. Merge source
`57573c770630e088c54246e3ff67de8ba930cc97` retains both parents: previous
head `33cad1b4fdbb391a1a7ca20ec3cf26c0c417bd98` and that main revision.
This is an integration correction, with no solver or timing change.
Claim `PCC-20261116-85a533` is unsigned/unverified. [pcc:unverified]

The incoming artifact utility refuses offloading while the Git index has
unmerged entries. Its regression checks file, directory and dry-run calls,
and asserts that index stages, worktree contents and manifests remain intact.
All 30 artifact tests pass on the merge source. Workflow wiring, ledger-prefix,
artifact and benchmark-record gates exit zero. The wiring tool retains its
existing `sage-compatibility.yml` path-checkout diagnostic. Exact commands,
exits and complete outputs are pinned by [validator.json](validator.json).
These are producer development checks, not independent execution proof.
[pcc:unverified]

[The reconciliation receipt](main-merge-df5156fc.json) records the byte-exact
172-entry canonical main prefix, followed by all 30 unmerged unsigned branch
claim and note bodies, appended with the PCC writer. It maps each original
event hash to its new wrapper; both original Git histories remain available.
The resulting merge-source ledger has 202 entries, before the new integration
claim. No signed verdict is replayed or promoted, and no correction or adoption
note is dropped. The active `PCC-20261115-8d2645` metadata matches reviewed main;
its intermediate repair and original records remain. [pcc:unverified]

[Git-object controls](source-scope.json) retain the core, CLI, comparison
checker, native curve source, prior timing evidence and 2,473-file frozen
snapshot unchanged. The imported artifact utility matches its canonical
[shared-code digest](shared-artifact-pin.json); the artifact policy is unchanged
and keeps the exact live ledger once. Existing source-scoped test receipts,
failures and timeouts are not relabeled. [pcc:unverified]

Current-head hosted CI must run again after this merge. Existing corpus
source-binding and CodeQL classification blockers remain open; no check or
review condition is bypassed. The matched ordinary-random IC versus special
auxiliary IC comparison, exact-special-base direct control and supplementary
rho still require admitted resources and a compliant frozen measurement
protocol. No benchmark or runtime advantage is established here.
[pcc:unverified]

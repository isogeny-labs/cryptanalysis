# Remove unrelated S3 prerequisites from validation

Following the user's S3-free instruction, the first correction made the N83
analysis unit job source-only. The next head, `77c4a311`, exposed eight more
failures at generated artifact restoration, before actual checks. Their
[complete provider logs and URLs](failed-ci-index.json) remain intact.
Source `ad063e04e14d721ae1263a63c7c2ed5e07c2932e` removes those unnecessary
prerequisites from the analysis, artifact-validation and binary-genus-two
workflows. Claim `PCC-20261116-f96d0c` is unsigned/unverified. [pcc:unverified]

Job-scoped inference now distinguishes event path selectors from runtime
inputs. A PR path filter controls when a job runs; it does not request a
download. Workflow environments and dispatch defaults remain conservative
inputs, including a control where a dispatch default really names archived
data. Actual data-consuming jobs keep their restoration requirements.
Unmarked workflows retain legacy behavior. [pcc:unverified]

The formatting checker previously embedded historical source paths in an
exclusion expression, which looked like artifact reads. The exact expression
now lives in `.clang-format-exclusions`; the command uses `grep -Ev -f`.
Actual GNU grep output is byte-identical on all 70,624 tracked paths plus
twelve explicit positive/negative examples. No formatting exclusion is added
or removed. [pcc:unverified]

[Preservation controls](preservation-controls.json) compare all remaining
non-bootstrap configuration, including triggers, conditions, timeouts and
check commands. They are unchanged apart from that equivalent configuration
file reference. The native check's expected `map_identity.json` is a tracked
Git blob; native/Lean source, IC core/CLI/timing sources and frozen evidence
are unchanged. Actual test, lint, native proof and coverage checks are kept;
none is waived. [pcc:unverified]

On `ad063e04`, all 38 artifact regressions and global workflow wiring pass.
The existing wiring diagnostic for the Sage workflow's separate checkout
path remains. [Validator](validator.json) pins commands, exits, full outputs,
provider failures and exact source scopes. The earlier eight analysis tests
and four refusal controls retain their own source and
[receipt](../no-s3-analysis-20261116/README.md), claim
`PCC-20261116-c91136`. They are not relabeled as fresh native or Lean runs.
[pcc:unverified]

Hosted checks still need to execute on the pushed head. No successful native,
Lean, full static-analysis or coverage execution is claimed by these local
controls. All merge/review conditions remain, as do the inherited source/proof
binding and CodeQL classification obligations. S3 upload is no longer a
continuation prerequisite for this user's task; Git/PR retain the source and
small evidence. No fresh research benchmark or runtime gain is established.
[pcc:unverified]

Reproduce local development checks from the repository root:

```sh
python3 -m unittest tools/artifacts/test_artifacts.py -v
python3 tools/artifacts/wire_workflows.py --check
```

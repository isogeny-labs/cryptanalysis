# PR 1104 CI follow-up, 2026-10-25

The requested task is to track [PR 1104](https://github.com/aburan28/cryptanalysis/pull/1104)
through merge, fix actionable failures, preserve scientific evidence, and never
merge with failed required checks. This record concerns CI maintenance only.
It makes no new mathematical, attack, timing or publication-novelty claim.

## Observed head and checks

The connector returned head `099e8c53e1d98781270a451c1228859d48ea66fb`,
base `c5aa7b39bfa30e8cdbd46a158c7cbadaa8be3503`, and synthetic test merge
`6d6cbe802a3b7d7f4fd8d1b04193937d613181fc`. The PR was open, ready and
mergeable, with no reviews or review threads. The six current-head runs were:

| Workflow | Run | Result |
|---|---:|---|
| ci | 40165001449 | success |
| Rust GHS sweeper | 40165001439 | success |
| Lean source evidence audit | 40165001428 | success |
| Lean corpus evidence bridge | 40165001434 | success |
| artifacts | 40165001421 | failure |
| analysis | 40165001420 | failure |

The initial snapshot and five failed-job text logs are retained here.
They are the complete decoded textual logs returned by the GitHub connector,
with GitHub's original credential masking. They are not recomputed summaries.
The CI workflow URLs are
`https://github.com/aburan28/cryptanalysis/actions/runs/<run>` and each job
URL appends `/job/<job>`. The initial query is an observation of this head,
not a separate CI execution on the base branch.

## Reproduced artifact-pull defect and fix

The artifact job failed during `artifacts.py pull --jobs 16 docs`, before
its unit tests or policy checks. Its sparse checkout omitted
`docs/ecdlp-surfaces/`; the puller read the tracked manifest but copied into
a nonexistent destination parent. Both `cp` and the `shutil.copyfile`
fallback failed. The error was not a rejected artifact-policy exemption.

The new regression uses the real file-backed store in a temporary Git repo:
push an object, commit its manifest, remove the hydrated file, sparsely
exclude its entire parent tree, then pull the object and compare its bytes.
The old implementation fails with FileNotFoundError. The first retained
attempt exposed the outer subprocess exception; the second adds its stderr
to the assertion and records the underlying missing-directory failure.

`place_copy` now creates the destination parent, including missing ancestors,
before copying. No policy threshold, digest check, CI assertion, scientific
source, frozen manifest or report is changed. All ten artifact-tool unit
tests pass after the fix, including corruption and source-store round-trip
controls. Commands, source hashes and raw output are in the adjacent receipts.
The tests use local temporary files and an emulated file store, not S3 or
paid compute. Their elapsed times are execution receipts, not benchmarks.

## Remaining inherited analysis failures

Four analysis jobs failed:

| Job | ID | Representative finding |
|---|---:|---|
| shellcheck + actionlint | 121084137435 | SC2016 on intentionally literal `$HOME` in `scripts/cli_smoke.sh:566`; actionlint did not run |
| clang-tidy | 121084137463 | warnings as errors in existing C sources/tests, including checkpoint representation comparisons and insecure-API diagnostics |
| cppcheck | 121084137506 | existing C/test style and possible null-pointer diagnostics |
| gcc -fanalyzer | 121084137645 | uninitialized-value diagnostic through `src/ca_internal.h:39` |

The analysis workflow also passed coverage and changed-line clang-format.
`inherited-inputs.json` compares the exact Git blobs for all 33 diagnostic
paths and relevant build/configuration inputs: they are identical on the
observed PR head and base. The PR has no C or shell changes causing these
findings. This is source-identity evidence; a separate base-branch CI run
was not observed, and no claim that every analyzer finding is a true bug is
made. The artifact puller was also unchanged at the observed head; its
missing-parent defect was reproduced locally and is fixed here.

The inherited C/shell analysis findings need their own reviewed fixes or a
base update containing those fixes, followed by successful checks on the
actual final PR head. No diagnostic is suppressed and no failing check is
treated as optional. The exact remaining merge blocker is recorded in
[the problem record](../../problems/ghs-pr-1104-inherited-ci-failures.md).
The PR remains unmerged while these failures persist. Subsequent checks
follow the requested minimum 50-minute cadence unless a new head or activity
provides a reason for a new check.

### Downstream workflow-wiring check

Once the artifact setup failure was fixed locally, its later workflow-wiring
check exposed two missing hydration steps: the newly introduced
`ghs-sweeper.yml` and the unchanged `suite.yml`. The GHS workflow now has the
standard hydration step scoped to `experiments/ghs-sweeper`. Its direct pull
returns zero files, without S3 access, because this subtree currently has no
store-backed inputs; the conservative scanner had climbed to the broader
`experiments` ancestor. Future store inputs in this subtree will be hydrated.
The scoped GHS wiring check passes. The global check still fails for
`suite.yml`, whose exact base/head workflow and checker inputs match. The
separate `sage-compatibility.yml` checkout-path note is advisory. The failed
and corrected wiring outputs are retained, with explicit exit statuses.
The inherited suite wiring defect is an additional artifact-workflow blocker;
it is not suppressed or misreported as a passing global check.

## Frozen evidence

The original scientific manifests are not regenerated. Their raw data,
arithmetic proofs and reports stay unchanged. Adding the CI problem to the
active problem index changes `problems/README.md`, which is bound in the
84-entry scientific manifest; the CI manifest records its old/new hashes
and the original byte-verified commit explicitly. The earlier four gate/
problem transitions remain documented separately. This is a versioned
index addition, not a change to any scientific result.

The initial CI manifest remains byte-identical at commit `0cd35127`.
The wiring supplement records new files and the newer report/problem versions
with explicit old/new hashes rather than rewriting that manifest.

# Partial-clone artifact policy lookup, 2026-10-25

The follow-up read at 07:11 UTC observes head
`c5838032b6bb0934cba1bed5bf988ffdc9f3404e` against unchanged base
`c5aa7b39bfa30e8cdbd46a158c7cbadaa8be3503`. The PR remains open, ready,
mergeable and without reviews or review threads. Rust and both Lean workflows
pass on this head; ordinary CI and analysis remain queued. This is a new
head-specific observation, not a claim that the earlier analysis failures
have cleared. See `snapshot.json`.

Artifact run 40168603888, job 121094664349, now successfully hydrates the
three docs artifacts and passes all ten unit tests. This verifies the prior
missing-parent fix in hosted CI. The job then fails its policy step:

```
artifacts: git cat-file -s fc2393a: fatal: Not a valid object name fc2393a
```

The complete decoded GitHub job text is retained as
`job-121094664349.txt`. Its source URL is
https://github.com/aburan28/cryptanalysis/actions/runs/40168603888/job/121094664349.
The workflow-wiring step was skipped after this failure, so no hosted
wiring success is inferred.

## Reproduction and correction

`cmd_check` consumed abbreviated object IDs from `git diff --raw`. In the
workflow's blob-filtered partial clone, an absent blob cannot be resolved
from an abbreviation. A full object ID lets Git retrieve the missing blob
from its configured promisor remote.

The new regression makes a real local Git remote with object filtering,
commits a 90,000-byte JSONL file, clones with `--filter=blob:none` and
`--no-checkout`, and verifies with `--missing=print` that the offending
blob is absent. Running the policy check before the fix fails with the same
abbreviated-ID lookup error and exits 2. The test expects the normal policy
rejection: exit 1, the exact offender path on stdout, and the data-file policy
diagnostic. Thus it checks both missing-object retrieval and continued policy
enforcement, rather than accepting an unconditional success.

The correction adds `--no-abbrev` to the raw diff command. No policy rule,
threshold, exemption, assertion or workflow gate is relaxed. All eleven
artifact-tool tests pass after the fix. Source hashes, tool versions,
commands, execution receipts and failing/passing raw outputs are adjacent.
The test uses a local file URL and temporary repositories, without S3,
external GitHub fetches or paid compute. Its elapsed time is not a benchmark.

The scientific Rust/Lean sources, reports and frozen manifests are unchanged.
The active CI problem/index and artifact-tool source versions receive
explicit old/new hashes from c5838032 in this directory's manifest. Earlier
CI manifests and reports remain historical evidence, not regenerated records.

## Remaining merge gates

Hosted verification of the full-object-ID fix is pending. The inherited
suite workflow hydration omission remains a known downstream wiring blocker.
Earlier inherited C/shell findings remain recorded separately; this head's
analysis has not yet run. No current-head CI check is bypassed or presumed
optional. The PR stays open while checks fail or remain pending.

No mathematical, vulnerability, publication-novelty or attack-cost conclusion
changes. The [active merge problem](../../../problems/ghs-pr-1104-inherited-ci-failures.md)
and the separate curve-transfer/priority problem remain open. Checks retain
the requested spacing; no CI rerun is requested without a substantive fix.

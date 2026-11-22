# Hosted confirmation of artifact fixes, 2026-10-25

At 08:14 UTC, PR 1104 is open, ready and mergeable, with no reviews or review
threads. Head `8ffc01a1ca3419da97c6142caa70c153d6cdada6` and base
`c5aa7b39bfa30e8cdbd46a158c7cbadaa8be3503` are unchanged since the last push.
All six PR workflow runs completed. The exact snapshot and all five failed
job logs returned by the GitHub connector are preserved here.

| Workflow | Run | Result |
|---|---:|---|
| ordinary ci | 40172185621 | success |
| Rust GHS sweeper | 40172185694 | success |
| Lean source evidence audit | 40172185671 | success |
| Lean corpus evidence bridge | 40172185628 | success |
| artifacts | 40172185678 | failure at inherited suite wiring |
| analysis | 40172185776 | four inherited analyzer jobs fail |

## Both artifact-tool fixes are verified on GitHub

Artifact job 121105184822 hydrates three files, passes all eleven unit tests,
and passes the full PR artifact-policy check. This verifies the missing-parent
and full-object-ID fixes in the hosted sparse/partial checkout. No threshold,
exemption, assertion or gate was relaxed. The job then fails its final
workflow-wiring check solely for the unchanged `suite.yml`:

```
suite.yml: needs `Pull store data this workflow reads (tools/artifacts)` for ecc2k130
```

The GHS workflow is no longer flagged. The separate checkout-path note for
`sage-compatibility.yml` remains advisory. This is not a successful artifacts
workflow; the final step still fails. The log's native URL is
https://github.com/aburan28/cryptanalysis/actions/runs/40172185678/job/121105184822.

## Analysis failures match the retained earlier diagnostics

The comparison removes only UTC timestamps and the fixed GitHub workspace
prefix. Exact diagnostic paths, line numbers, severities and text are kept;
sorted multisets are identical to the earlier retained jobs:

| Analyzer | Current job | Matching diagnostic count |
|---|---:|---:|
| shellcheck | 121105253002 | 1 |
| clang-tidy | 121105252883 | 38 |
| cppcheck | 121105252860 | 34 |
| gcc -fanalyzer | 121105253013 | 1 |

`diagnostic-comparison.json` preserves all comparisons, including empty
added/removed lists. These counts are diagnostics, not confirmed defects.
Coverage and changed-line clang-format passed. Actionlint was skipped after
shellcheck failed, so no actionlint success is claimed.

Of the previous 33-path source/build inventory, 32 remain byte-identical to
the base. Only the intentionally fixed artifact tool differs; all C/shell
diagnostic and analyzer inputs match. `inherited-inputs.json` records the
full Git blob identities. A separate base CI execution was not observed.

The remaining gates are reviewed fixes to inherited suite hydration and
C/shell analyzer findings, then successful required/applicable checks on
the final head. The user excludes broad unrelated C cleanup. No gate is
suppressed and the PR is not merged while these failures persist. The
[active problem](../../../problems/ghs-pr-1104-inherited-ci-failures.md)
records this hosted confirmation and the remaining acceptance conditions.

## Scope and preservation

This is CI evidence and active problem maintenance only. No implementation,
scientific arithmetic, mathematical statement, Rust/Lean source, prior report
or frozen manifest changes. The new manifest binds these logs and the two
active problem/index versions, with explicit transitions from 8ffc01a1.
No experiment, benchmark, paid compute or repeated local test suite is run.

Following this confirmation, unchanged inherited failures need spaced status
checks and PR conversation updates, not additional status-only commits or
CI reruns. New code, a changed diagnostic or a relevant base update would
justify new work. The scientific transfer/priority gaps remain separate and
open; a PR merge would not settle them.

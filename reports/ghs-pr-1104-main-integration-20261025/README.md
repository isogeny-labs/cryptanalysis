# Integrate main's reviewed CI repairs, 2026-10-25

The 15:06 UTC check found a new merge conflict on PR 1104. Head fd03d2f9
and its six completed CI outcomes were unchanged, but main had advanced to
`d90192b50b13f25d2f8356bf40133a05554285a2` through
[PR 1114](https://github.com/aburan28/cryptanalysis/pull/1114), merged at
14:04:36 UTC. Its repairs cover the previously inherited C/shell analysis
findings, precise workflow artifact-path matching, and live GLV source
binding. This is relevant base activity; the no-change count resets.

The GitHub connector still returned the former c5aa7b39 base SHA in this
observation. `gh` confirmed CONFLICTING/DIRTY, and an authenticated Git fetch
identified the actual new main revision. No conclusion about conflicts was
drawn from the connector's Boolean alone.

## Merge and source binding

Merge a74d5404 combines the reviewed main changes with this PR. Its only
textual conflict was in artifact-policy object-ID formatting: main used
`--abbrev=40`, while this branch used `--no-abbrev`. We retain complete
object IDs and both real sparse/partial-clone regressions. All other main
repairs are imported unchanged, including C and shell sources. No unrelated
C cleanup is authored here.

Main updates the GLV validator/live receipt to source 8bf648dc with C hash
60796724ef7d7c5b3b7dfd89c29db85d5e188deb247b5d9d0bd69b84551afe20.
The 96-source gate now validates that main live receipt and exact C bytes.
The previous validator and live receipt are copied byte-for-byte from
fd03d2f9 into this directory as historical evidence; the archived validator
is a source snapshot, not a relocated executable. The gate replays the old
pinned C selector and both negative controls against the frozen old live
receipt. Its exact hash, selector guards, divisor, loop cap and negative
control assertions remain enforced. Historical corpus receipts are untouched.

The new corpus receipt lives at
`reports/lean-current-corpus-20261025-main-update/receipt.json`. Its workflow
and documentation point to that version. The same 96 Lean research sources
remain: 91 archive-bound and five rebuilt. Theorems, quantifiers, axiom
expectations and formalization gaps are unchanged.

## Local verification

The prospective `CHECKS.md`, merge resolution and source-binding code were
committed before replay. At that exact revision:

| Check | Result |
|---|---|
| Artifact-tool unit tests | all 11 pass |
| Global workflow wiring | passes; checkout-path advisory only |
| 96-source Lean corpus | passes; new receipt generated |

Commands, source revision, raw stdout/stderr, digests and execution receipts
are adjacent. A receipt comparison, artifact policy and whitespace check
are required before push. Hosted final-head checks, including analysis,
remain required before merge. Local wiring success verifies the reviewed
scanner correction; no test or workflow is suppressed.

The setup needed exact-index rehydration after Git's sparse merge omitted
`src/curve.c` and 129 Lean sources/pins from the worktree. They were restored
without changing the sparse-checkout definition or any indexed byte. Two
initial read/diff commands attempted a lazy Git fetch without the per-command
network grant and failed at the proxy. Repeating with that grant succeeded.
An initial source read raised FileNotFoundError for the omitted C file;
exact-index restoration fixed it. These were environment/setup failures,
not failed mathematical checks, and generated no scientific conclusion.

## Preservation and remaining scope

The old 125 scientific entries and 15-entry overlap supplement remain
byte-identical. All frozen scientific/CI manifests remain unchanged. Mutable
gate/problem paths receive explicit version transitions in this phase;
older manifests continue to verify at their historical commits. Main's live
GLV binding receives a separate version rather than replacing historical
evidence. Imported C inputs match main exactly, and gluing theorem sources
match fd03d2f9 exactly.

No census, curve equation, subgroup map, proof statement, novelty claim or
attack cost is changed. The scientific target/priority problem remains open.
The CI [problem record](../../problems/ghs-pr-1104-inherited-ci-failures.md)
tracks hosted verification of this integration. The PR stays ready with
auto-merge enabled; it is not merged while any required/applicable check
fails or is pending. Repeated unchanged statuses will not trigger further
receipt-only commits or CI reruns.

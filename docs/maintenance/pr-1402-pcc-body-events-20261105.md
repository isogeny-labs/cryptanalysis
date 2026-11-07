# PR 1402: validate edited PR descriptions

## What was done

The failing PCC job linted the PR description captured in its original event. The author can correct the description without changing the code head, but GitHub's default pull_request activities omit edited. Explicitly keep opened/synchronize/reopened and add edited/ready_for_review. All gate commands, ledger checks, canaries and signature requirements remain unchanged.

## Decisions made

PR prose is a gate input. Validate changes to that input through a real event, without an empty commit, a stale-event retry or a claim-standing exception. Official event semantics: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request . Sources checked: AGENTS.md, docs/SABOTAGE_RESISTANCE.md, tools/pcc/pcc.py and the exact failing job log.

## Open threads

Fresh checks on the published head, content review and guarded merge.

## Errors

The old workflow did not subscribe to body edits. Local prose lint reports no findings after precise descriptive wording; this is an ordinary tool observation, not a signed PCC claim verdict. [pcc:unverified]

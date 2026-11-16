# Plain logs used as JSON recompute proofs

- **Status:** resolved for proof format; independent verification remains open
- **Kind:** inherited proof-input format mismatch
- **Affected work:** PCC gate for PR #1536; claim `PCC-20261115-8d2645`
- **Next action owner:** PR follow-up and original claim-maintenance lane
- **Last updated:** 2026-11-16

## Problem

The original claim points `recompute` proofs at `native-binary-tests.txt` and
`build-before.txt`, which are plain Cargo text rather than admitted JSON
validator reports. The PCC gate fails parsing both; this is separate from
whether their producer-reported outcomes are true. [pcc:unverified]

## Evidence and uncertainty

The claim, both logs and actual PCC checker have identical bytes on main
`66890bbe` and PR head `b85bca1e`. Isolated base/head snapshots reproduce both
non-JSON refusals. The hosted failure is run `43785058006`, job
`133030734988`. Inputs, hashes, full hosted log and scoped reproduction logs
are retained in
[the follow-up](../experiments/prime-field-auxiliary-ic/random-vs-special/pcc-format-followup/).
These reproductions are not a full rerun of main's CI. [pcc:unverified]

The two original text logs do not supply complete process-exit or compile/run
source attestations. The correction preserves those uncertainties and the
earlier compiler error. It extracts only the reported five selected binary
tests, zero failed/ignored/measured, and 59 filtered out; it does not relabel
them as a complete suite or independent execution. [pcc:unverified]

## What would unblock it

- Preserve the raw text, original claim and failed validation.
- Reference a format-admitted unsigned validator with the same reported scope,
  leaving the original claim/ledger history intact and standing unverified.
- Pass the exact-head hosted PCC gate without skipping or weakening it.

This fixes a representation obstruction, not independent proof or any other
CI, mathematical or measurement requirement.

## Next discriminating step

The exact-head PCC run on `df6d8afb` accepts the retained-data report. This
format obstruction is resolved; retain any newly exposed failure with its
own source scope. Do not infer a
signed verdict, rewrite earlier ledger events, suppress failures or skip CI.

## Resolution and history

2026-11-16: the active claim references an admitted JSON report; its statement,
scope and producer are unchanged. The original claim and raw logs remain,
and only new claim/correction-note events were appended. Local verification
returns `not_covered` and standing remains unverified. Hosted qualification
was pending at that initial local correction. See
[the correction note](../reports/courtois-getrandom-compat-20261115/FORMAT_REPAIR.md).
[pcc:unverified]

2026-11-16: [PCC job 133043742308](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43789263534/job/133043742308)
succeeds on exact source `df6d8afb`. The
[captured provider receipt](../experiments/prime-field-auxiliary-ic/random-vs-special/pcc-format-followup/hosted-status-df6d8afb.json),
claim `PCC-20261116-537de4` (unverified), meets the format acceptance criterion.
The claim itself remains unverified, and the separate GLV/other-CI and
measurement requirements remain open. [pcc:unverified]

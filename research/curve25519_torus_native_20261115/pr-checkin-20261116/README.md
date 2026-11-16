# Initial PR closure coverage

`closure-1570.json` retains the GitHub snapshot; `facts-1570.json` records its
hash, immutable head/merge commits and the publication-to-merge window.
Episode E-607115f50881 and outcome O-d824c83d8fcf cover that limited window.
They are [pcc:unverified] administrative records, not an autonomy success or
scientific validation.

PR #1570 merged at 2026-11-15T22:53:45Z. Its final head was committed only eight
seconds earlier. The retained final-head gate/store checks completed after
merge, with failure conclusions; those later results cannot establish green
CI at merge. The episode deliberately leaves `ci_green_at_merge` false.

The original prompt and subsequent human-message timestamps are unavailable.
The episode start is explicitly PR publication, not a reconstructed session
start. No intervention rows or recovery classifications are fabricated; empty
lists do not mean there were no interventions or incidents. Token/cost fields
remain null. The 14-day revert check is due after 2026-11-29T22:53:45Z and has
not been recorded early.

The maintained writer used was crypto's `tools/autonomy_report.py` at
f8a7dbc5f7f2d82c3c2f9209d3dd7a1d025a9fb8, with its explicit `--dir` option;
this repository has no local copy. The same applies to `tools/lessons.py`.

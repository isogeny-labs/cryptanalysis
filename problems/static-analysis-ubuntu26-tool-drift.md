# Ubuntu 26 static-analysis runner drift

- **Status:** `investigating`
- **Kind:** tool environment drift and untriaged code-validation findings
- **Affected work:** [modular arithmetic assay PR #1109](https://github.com/isogeny-labs/cryptanalysis/pull/1109), the repository-wide `analysis` gate, and claims that the current C tree is clean under that gate
- **Next action owner:** C implementation and validation lane; Conductor T-373 records this audit
- **Last updated:** 2026-10-25

## Problem

The current-head modular arithmetic proof PR cannot pass the repository-wide static-analysis gate because `ubuntu-latest` changed hosted images and newer clang-tidy and cppcheck versions report 36 candidate findings in C files untouched by that PR. Those findings have not been adjudicated, so neither a clean-code verdict nor an exact-head merge gate pass is established.

## Evidence and uncertainty

- **Observed:** The passing base-main [analysis run 40211290956](https://github.com/isogeny-labs/cryptanalysis/actions/runs/40211290956) at commit `379faa0f1e38facd9c8fdfc527f0b89518cf2e70` used `ubuntu-24.04` image `ubuntu24/20261012.334`, clang-tidy `1:18.0-59~exp2`, and cppcheck `2.13.0-2ubuntu3`. The exact-head PR [rerun 40228437729](https://github.com/isogeny-labs/cryptanalysis/actions/runs/40228437729) at commit `1d3023db770cd51de10f31c32bf990a564c59c48` used `ubuntu-26.04` image `ubuntu26/20261012.163`, clang-tidy `1:21.1.6-71`, and cppcheck `2.19.0-3`. Both tool jobs failed on the PR; its other analysis jobs passed. The PR diff does not alter the reported C files or `analysis.yml`.
- **Observed candidate groups:** clang-tidy reports 12 warnings as errors: potential null `fopen` (`src/grumpy.c`), tainted bounds/allocation (`src/indexcalc.c`, `src/precomp.c`, `tools/ca_cli.c`), invalid `bind` (`tests/test_coord.c`), and stream state (`tools/ca_bench.c`). Cppcheck reports 24: possible uninitialized values (`src/bsgs.c`, `src/pohlig.c`, `tools/ca_bench.c`) and allocation-failure dereferences (`src/linalg.c`, `tests/test_linalg.c`). The linked job logs give exact lines and diagnostic names.
- **Derived or proved:** The image and tool versions differ across the two runs, and the candidate locations are outside this PR's source diff. This explains a reproducibility gap in the prior clean baseline; it does not prove each warning is a false positive.
- **Suspected explanation:** The new analyzer versions detect paths missed by the old versions. A run of the unchanged base SHA on the new image would distinguish version drift from any PR-merge checkout effect.
- **Missing capability:** A reviewed source-to-sink triage for the 36 candidates, with fixes or precise justified suppressions where appropriate, plus a green exact-head analysis gate.
- **What this evidence does not establish:** It does not invalidate the separate Lean theorem or SAW C-to-Cryptol checks. It also does not establish that the C tree is free of the reported defects or that pinning the old image resolves them.

## What would unblock it

- [ ] Reproduce the two analyzer jobs on an unchanged base commit under a named runner image and archive versions and diagnostics.
- [ ] Triage every new diagnostic against the exact source path; fix valid findings or document why a narrowly scoped finding is false, with controls that keep the analyzer effective.
- [ ] Obtain passing exact-head required checks for PR #1109 after any workflow or source correction, preserving a merge commit and review gates.

These conditions restore the validation gate for this PR. They do not expand the Lean proof from its reduced-input two-function scope to other arithmetic, callers, or side channels.

## Next discriminating step

- **Action or proof obligation:** Run clang-tidy 21 and cppcheck 2.19 on unchanged base `379faa0f...`, or a byte-identical checkout, then begin with the tainted bounds and allocation reports.
- **Inputs and controls:** Compare the same base commit under Ubuntu 24.04 and 26.04 with recorded package versions; hold C source and analyzer flags fixed.
- **Execution limits and stop condition:** A bounded analyzer replay of the existing tree only; no scientific experiment or benchmark. Stop after diagnostics are archived and categorized for review.
- **Outcomes and next actions:** The same warnings on base identify toolchain drift; PR-only warnings require a checkout/configuration investigation. Valid paths get patches and tests; false positives get narrow documented suppressions; runner failure is recorded as infrastructure and retried only to answer that question.
- **Recheck trigger:** A reviewed diagnostic triage, source patch, or exact-head analysis workflow change.

## Resolution and history

- 2026-10-25: Opened after the first PR rerun completed with 21 successful check contexts, 16 older canceled contexts, and two failed new static-analysis contexts. No warning was suppressed or declared false. Unresolved.

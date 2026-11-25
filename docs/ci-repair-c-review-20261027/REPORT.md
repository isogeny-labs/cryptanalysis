# C review integration — 2026-10-27

Preserve PR #1224's author history on top of the shared CI repair #1214. Its overlapping ownership/bounds and analyzer repairs are already addressed by the parent: retain that tested implementation and its line-specific callback annotations, including the owned journal bitmap, file-derived allocations and explicit manifest capacity. Do not replace them with broader suppressions or introduce an unrelated URL-length limit.

The new behavior is limited to three files: reject null matrix/right-hand-side/output/known pointers in `ca_linsolve_mod_prime`, test all four positions, and clean up the coordinator test server on mutex/socket/option/bind/listen/name/thread failures. Other library and benchmark source remains byte-identical to the parent. Frozen inputs, run evidence, costs and thresholds are unchanged.

Validation: all 19 Address/UndefinedSanitizer CTests pass with warnings as errors. Clang-tidy 21.1.8 and Cppcheck 2.19.0 pass over all three changed files with the existing analysis policy. Changed-line formatting reports no changes. Logs, exact source hashes and the retained author head are recorded alongside this report. The parent separately passed its complete hosted C analysis gates.

Sources reviewed: the exact #1224 patches and hosted-check report, current C interfaces and coordinator test setup/callers, and the parent repair's successful native/analyzer/format receipts. Current-head hosted CI and review remain required before merging this follow-up. The user’s all-PR/all-green-main goal remains open.

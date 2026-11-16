# CT157 — type-preserving native parity audit protocol

2026-11-16 · [pcc:unverified]. Planned amendment of CT125 PR #1533. Not an ECDLP speedup or native replay.

## Observed defect

The original `compare_norm_reuse.py` at Git blob `d8e1b8a6c9615310439411831df847739682eb5d` checks ordered 695-record original/reuse logs (672 exceptional records, 48 selected rows, 3 routes). Its Python equality checks accept `0 == False`, `1 == True` and `1 == 1.0`; the alleged unchanged public mathematical values can be silently substituted with different JSON types. Existing six negative controls do not probe these aliases. CT128's earlier Python -O defect in another pricing auditor is distinct.

## Preregistered change and acceptance

Create a recursive type-preserving finite-JSON comparator covering all unchanged public, exceptional and route fields, enforce actual integer source-call counter types, and reject nonstandard NaN/Infinity parsed constants. Retain all original 695/672/48 strict schema checks, original route transformations, original six sabotage controls and the frozen source blobs. Add at least five adversarial controls accepted by the legacy equality: exceptional int→bool, public-input int→bool, modified counter int→bool/int→float and unchanged counter int→bool. Add nonfinite parser controls and run both Python normal and -O. The positive synthetic 695-record control remains accepted. All modifications on CT125 feature branch only.

## Evidentiary limits

Reviewed latest crypto #3877/#4215, cryptanalysis #1523/#1533/#1562/#1589, CT156 original source, repo AGENTS and current dated logs. Shared research-KB/Conductor unavailable in connector-only runtime; use original code and known prior art, no novelty assertion. No independent actual native whole-695/701 replay, no admitted C169/C13a/C13b/D, no complete transferred public-Q cold solve, no strongest matched rho/BSGS/IC full-cost comparison, no signed PCC. Budget exhausted in contemporaneous root LP status, so no paid compute.

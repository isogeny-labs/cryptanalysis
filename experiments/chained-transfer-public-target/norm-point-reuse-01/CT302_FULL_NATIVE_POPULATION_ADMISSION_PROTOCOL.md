# CT302 — pair full native population before pricing norm reuse

**Preregistered 2026-11-21 America/Los_Angeles, before implementation; [pcc:unverified].** Draft [#1912](https://github.com/isogeny-labs/cryptanalysis/pull/1912), stacked on CT301 [#1905](https://github.com/isogeny-labs/cryptanalysis/pull/1905) and its CT300/299 ancestors; owning primitive producer [#1871](https://github.com/isogeny-labs/cryptanalysis/pull/1871). No changed original Rust, instrumented sibling, immutable 695/701 input, or model/credential.

## Observed defect and limits

CT301's `ct248_scoped_sample_audit.py --log --fixture` binds the single 48-vector selected event to a Git-blob-pinned original and reconciles 144 local primitive epochs to one lifetime record. It does **not** demand the other 694 full native population events or a paired unmodified, pre-reuse native run. A selected-event-only synthetic transcript with mock clocks can satisfy this source-level gate, and does not establish native execution, complete mathematical output equality or full-population custody.

Reuse existing `compare_norm_reuse.py` rather than rebuilding its full-history logic. That implementation already demands two **ordered 695-event** original/optimized transcripts, 672 exceptional descriptors, identical non-selected events, 48 selected vectors and only 144 preregistered counter changes, with strict type comparison. It is an internal two-producer-log equality check, not independent arithmetic verification.

## Prospective joint admission

1. Add an **additive** `ct302_full_native_gate.py` CLI requiring `--original`, `--optimized`, and `--fixture`; the immutable 48-vector fixture is Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`. Do not quietly accept a missing baseline or a single source event.
2. Parse full original and optimized records using `compare_norm_reuse.events/check` without weakening its strict 695/672/48/144, order, exceptional descriptor and matched-counter checks. Require precisely one selected source event on each side.
3. Parse all CT248/CT244 tagged **primitive events** using a duplicate-key-rejecting, NaN/Infinity-rejecting decoder; use existing CT248/249 auditor to require 144 scoped arm epochs, strict directed physical/producer counts and lifetime reconciliation. Compare all optimized selected keys and counters with CT301's frozen-value binding.
4. Report only *producer-transcript internal consistency*, separately exposing full population and scoped-clock status. Do not label the result independent execution, signed PCC, calibrated operation time or cold ECDLP solving. No synthetic elapsed value may be labeled a native measurement.
5. Synthetic local/hosted tests in Python normal and `-O -S`: genuine **frozen 48 selected input rows** combined with explicitly **synthetic** 694 other-record controls and 144 zero-ns clock samples accepted as a structural positive; mutated exceptional, missing full row, missing original log, changed selected input, wrong counter, omitted lifetime, duplicate primitive JSON key and unexpected non-JSON constants rejected. A positive synthetic transcript must remain explicitly non-evidentiary.
6. Preserve previous source CI and native producer, original original-model/fixed-chain data, source bytes, LFD proof, ledger and EKS/Spot budget STOP. New source-only workflow must checkout exact head and not run Rust/model hydration or paid jobs.

## Follow-through

Restore approved six-object source custody through valid AWS STS (no workaround), compile bounded pinned Rust, freeze entire original/CT125 native 695/701 logs, run this admission and original source comparator; independently check actual Jacobian mathematics. Then perform paired same-host A/A ABBA cold `C169,C13a,C13b,D,N2_actual` with all setup/transfer/recovery/LA/RSS, matched optimized rho/BSGS/frontier IC and independent signed PCC. The decision threshold is independently reproduced complete cold single-target baseline/candidate >1, not isolated `C169- C13a - C13b` alone.

**References:** original CT125 [#1533](https://github.com/isogeny-labs/cryptanalysis/pull/1533); CT198 [#1748](https://github.com/isogeny-labs/cryptanalysis/pull/1748); CT244/248 [#1871](https://github.com/isogeny-labs/cryptanalysis/pull/1871); CT300 [#1904](https://github.com/isogeny-labs/cryptanalysis/pull/1904); CT301 [#1905](https://github.com/isogeny-labs/cryptanalysis/pull/1905); crypto [#3877](https://github.com/isogeny-labs/crypto/pull/3877) and [#4215](https://github.com/isogeny-labs/crypto/pull/4215); CT243 cold negative [#4715](https://github.com/isogeny-labs/crypto/pull/4715). Shared research-KB MCP unavailable; no novelty/absence inference. [pcc:unverified]

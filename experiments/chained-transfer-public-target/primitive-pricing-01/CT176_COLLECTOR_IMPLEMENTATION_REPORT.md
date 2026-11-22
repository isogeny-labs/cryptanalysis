# CT176 — bounded external cold-process collector implementation

Date: 2026-11-17 UTC. Scientific standing: **[pcc:unverified]**. No new transfer timing or complete ECDLP result.

## What changed

The prior CT175 instrument outputs one native public-packet transfer per new subprocess but had **no outside-process paired timing collector**. CT176 freezes a protocol first (`99ff7fff`), then adds `ct176_cold_process_collector.py` (`e81d156`, corrected `61679d1`), negative-control tests (`22c2277`), and source-only CI coverage (`895bf9e`) to the existing cryptanalysis PR #1700. The native CT125 evaluator and frozen fixture are unchanged.

**Exact planned roster:** 48 original public packets, eight predetermined blocks, six fresh processes per packet in A/B/B/A/A/A order = **2,304 subprocesses**. A is direct degree-169; B is retained two-stage degree-13. The two final A/A samples explicitly monitor same-arm time drift. Every row is paired by identical public input and runs sequentially on one host under fixed process/cpu-affinity metadata. A seed of 20261117 fixes packet shuffles independently of measurements.

The collector verifies the actual Git blob of the 48-row fixture, requires a user-supplied exact SHA-256 of a built native binary, validates all cohort fields, canonical 19-word targets and 21 counters, rejects malformed numeric evidence (including integer-like floats/booleans), stores every raw process stdout/stderr in both human-readable and lossless base64 forms, process exit/timeout, externally timed wall, reported RSS, setup/route timers and errors. Outputs are streamed to an exclusively created JSONL; failures are retained as refusals, not rerun/trimmed. No shell or `cargo run` enters timed samples.

The command is **plan-only by default**. Native execution requires `--execute --admission-approved` but even these flags **do not constitute** permission to use EKS, Spot, cloud or a blocked budget. The separate owner authorization and original artifact custody requirements still apply.

## Prospective reproduction (no native run performed here)

```sh
root=experiments/chained-transfer-public-target/primitive-pricing-01
fixture=experiments/chained-transfer-public-target/evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json

# Safe plan-only and negative-control checks:
python3 -S "$root/ct176_cold_process_collector.py" --fixture "$fixture"
python3 -S -m unittest discover -s "$root" -p 'test_ct176_cold_process_collector.py' -v

# AFTER CT172 exact native parity, independent custody and owner admission:
# built=ABSOLUTE_PATH_TO_PINNED_RELEASE_ct172-replay
# python3 -S "$root/ct176_cold_process_collector.py" \
#   --fixture "$fixture" --executable "$built" \
#   --executable-sha256 "$(sha256sum "$built" | cut -d' ' -f1)" \
#   --output new-unmodified-ct176-raw.jsonl \
#   --execute --admission-approved
```

The new CI step is **only** a Python syntax/negative-control/plan check on the actual pinned 48-record input. It does not compile or execute the original CT125 native arithmetic; all independently signed PCC and provider artifact checks remain outside this step. Hosted CI status must be read on the final PR head before asserting even this source gate passed.

## What remains unresolved

- CT172/CT175 must be natively typechecked and full 48-case output/counter parity established on restored pinned source.
- No fresh-process timing is available, and this 48-operand cohort is **not** the independently held 695/701 corpus. A fresh OS process is not a controlled cold cache or a complete source-field ECDLP.
- The actual primitives `C169,C13a,C13b,N2_actual,D_padd` must still be individually timed, in addition to complete route wall and all correction/inverse costs.
- Most importantly, a **complete scalar-blind single-target prime-field ECDLP** must be run and answer-verified versus matched strongest source rho, BSGS and IC, with setup, transfer, linear algebra, recovery, verification, memory, confidence intervals, independent replay and signed PCC. Only an independently reproduced full cost ratio >1 can support an advantage.
- Existing EKS/Spot paid STOP and #3904 coordination apply. Richelot PR #4514 is concurrent and untouched. Crypto-autoresearcher VLT1 is locked and untouched. Authenticated raw artifact restoration and KB service are unavailable in this runtime.

An improvement to evidence collection is **engineering, not algorithmic speedup**. No timings, new curve map, cross-characteristic construction, paid run, manual merge, or verified numerical advantage are claimed. [pcc:unverified]

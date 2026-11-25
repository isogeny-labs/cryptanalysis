# CT201 — independent complete-cold ECDLP evidence scoring, source-only

2026-11-18 UTC. [pcc:unverified]. Tracked in [draft PR #1766](https://github.com/isogeny-labs/cryptanalysis/pull/1766).

## Implemented

- A separate independent **prime-field affine group law** for short Weierstrass curves, not a call to the producer transfer or solver; independent verification of each reported solution `[k]G=Q` for a fixed same-target input. Prime field and subgroup order must be independently shown prime under the deterministic 64-bit Miller–Rabin domain; reject unsupported larger claims.
- Fixed complete source-to-answer comparison of transfer versus **the fastest actual complete rho, BSGS or IC process per matched block**. All seven serial phase fields are required, but wall time includes unattributed portions. Independent reported resident-memory cap is enforced and per-block memory is exposed; no memory-to-time pricing is invented.
- Mandatory fresh-process flag, eight or more contiguous complete five-arm blocks, consistent host and public-input digest, A/A same-method sham, malformed receipt rejection and a deterministic **diagnostic** 4096-resample interval.
- Fail-closed labels: even a synthetic 1.5× ratio is merely `candidate_needs_external_signed_verifier`; untrusted records cannot satisfy independent execution proof, signed PCC or the ultimate complete-ECDLP success gate.

## Source tests

In the isolated local Python 3.13 container:

```sh
D=experiments/chained-transfer-public-target/primitive-pricing-01/ct201-complete-solve
python3 -S -m unittest discover -s "$D" -p 'test_ct201_complete_solve_gate.py' -v
python3 -O -S -m unittest discover -s "$D" -p 'test_ct201_complete_solve_gate.py' -v
```

20/20 normal and 20/20 optimized unit tests passed locally; these are **synthetic mathematical/adversarial controls**, not native timing or independent PCC. Tests cover correct curve arithmetic and false outputs, false primality, omitted reference arms, mixed input and host, warm claims, absent phase, Boolean timings, bad hash format, RAM limit, phase overcount, bad A/A and a slower arm. The original frozen Jacobian fixture is not touched. Exact-HEAD GitHub workflow is `.github/workflows/ct201-complete-solve-source.yml`; inspect its result at the final head before asserting it passed.

The deliberately programmed `p=97, E:y²=x³+x+1, G=(0,1), r=97, Q=[7]G=(75,1)` control reproduces an arithmetic scalar and a **synthetic** `12000/8000 = 1.5` wall ratio. This number is **not** a solver measurement and must never enter an ECDLP benchmark table.

## Evidence limitation and blocker

The reader does not verify that any binary ran, or that stdout, process times, host identity, cached state, SHA strings, exit logs or claimed memory were truly observed. It checks *logical consistency* of producer-supplied records; a compromised producer can fabricate a consistent record. The exact same public target is verified mathematically from the declared data, but raw bytes must later be inspected by a separate independent validator with a signed PCC verdict.

Original source-to-target CT125 parity, CT200's original S3 model hydration (HTTP 403 at [run #44247758448](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44247758448)), 695/701-record custody, native paired same-host `C169`, `C13a`, `C13b`, actual norm and doubling prices, fresh complete ECDLP logs, calibrated uncertainty/CI and signed verification remain **not performed here**. CT198 already showed norm reuse cancels in direct-vs-retained counter differences. No paid cloud, data substitution, protected merge or advertised performance speedup.

## Decision

Use CT201 only as a *pre-adjudication* blocker for future real paired results. Do not construct a new cost claim from CT159/CT198 synthetic primitive prices or compare a transfer-only path to a rho end-to-end path. Recover the genuine model bytes, typecheck exact Rust CT192 driver, independently authenticate original corpus, and physically measure complete cold source/transfer solves. The scientific target is still an independently reproduced total ratio >1 against the strongest matched reference, with setup, transfer, relation collection, LA, individual log, verification and memory counted.

Research-KB MCP unavailable; repo AGENTS, CT125/CT192/CT198/CT199/CT200 and merged crypto #3877, #4215 plus GPU IC #4178 were reviewed for overlap. This is an engineering/verifier increment, **not** a new index calculus algorithm. [pcc:unverified]

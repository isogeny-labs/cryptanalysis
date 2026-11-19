# Xedni natural-run authorization and requirement ledger

Recorded: 2026-11-19T05:34:20Z

User authorization received in the active session: `Authorized to run`.
This authorizes execution of the previously requested frozen natural
rank-decay experiment. It does not waive the repository checkpoint rule,
change the statistical acceptance criteria, supply licensed software, or
turn a missing certificate into a negative outcome. [pcc:unverified]

No natural source, lift, rank, relation, calibration, sentinel, discovery, or
replication row existed when this authorization was recorded.
[pcc:unverified]

## Requirement-to-evidence ledger

| Requested requirement | Frozen scope | Evidence required | Initial status |
| --- | --- | --- | --- |
| Prime range | Three deterministic primes at every even size from 16 through 32 bits | Freeze-bound row and raw transcript for every planned trial | Authorized, not launched |
| Independent lifting control | Balanced, wide, optimized, and frozen mechanism-panel selectors | Exact lift/incidence/congruence certificate and charged candidate-bank work | Implemented for controls; natural executor absent |
| Independent `r` control | `r=2..9`, with `r=7..9` retained rather than silently omitted | Selected-point map and exact replay on every admitted row | `r=2..6` implemented; `r=7..9` map blocked |
| Independent local-condition control | No-local, compatible reverse-Mestre, neutral matched CRT, and incompatible diagnostics | Exact local/quotient compatibility certificate | Implemented for controls; not naturally executed |
| Modern rank tools | PARI `ellrank`, staged Magma `RankBounds`/2-descent | Pinned transcripts and agreement under the frozen cascade | PARI available; licensed Magma absent |
| Decay decision | Separate rank-deficiency and useful-recovery slopes, cutoff 20 bits, replication, familywise control | Frozen analyzer over complete roster with rigorous mixed unresolved allocation | Analyzer implemented; production optimizer/provenance incomplete |
| Non-circular public selectors | Selector cannot read source scalars, target scalar, rank, or relation output | Hash-linked redacted object and OS-enforced separate evaluator process | Designed; process boundary absent |
| Useful negative labels | No bounded no-hit promoted to independence | Complete relation lattice or selected-point independence certificate | Absent |
| Reproducibility and durability | Preserve failures, timeouts, commands, hashes, costs, environment, and raw evidence | Successful checkpoint on the exact pushed run head before launch | Previous gate failed; retry required |
| Power | Preserve the requested effect-size/exposure rather than silently downscale | Committed powered calibration/discovery/replication allocation | Not allocated |

## Launch rule

The first allowed natural stage remains the frozen, excluded 16/18-bit
two-row-per-cell calibration. It may launch only after a new authorizing
freeze binds the completed executor and validators, the exact pushed head has
passed `scripts/checkpoint.sh gate` without bypass, and all tool/certificate
gates required by the frozen protocol are satisfied. Authorization alone is
not recorded as experimental completion. [pcc:unverified]

## Authorization preflight

The exact frozen runner preflight was attempted after authorization. It exited
2 with `natural_rows_not_authorized` and reported
`natural_rows_started=0`; the structured record is
[`AUTHORIZED_PREFLIGHT_20261119.json`](AUTHORIZED_PREFLIGHT_20261119.json).
[pcc:unverified]

Independent environment checks found the pinned PARI 2.17.2 container and
frozen `ca-icx` binary available, but no licensed Magma executable/image and
no checkpoint upload token, token file, AWS credential, or AWS profile. The
runner has only `plan` and `preflight-natural`; even a truthful future
authorizing freeze reaches an intentional `BLOCKED_NO_NATURAL_EXECUTOR`
terminal until an executor is implemented. [pcc:unverified]

The calibration roster remains exactly 1,080 executable `r=2..6` rows plus
648 blocked `r=7..9` rows. It is a feasibility/cost calibration, not a decay
classification. The worst-case rank-tool timeout ceiling alone is 2,460
seconds per executable row, or 738 serial hours for 1,080 rows, before source,
construction, invariant, relation, and verification work. No smaller workload
is substituted for the requested experiment. [pcc:unverified]

## Anti-circularity preflight

An adversarial M3 check supplied the values `314159` and `271828` under the
innocuous public-feature key `proxy_curvature`. The current name-filtering and
selector-hash logic accepted the values and selected the second candidate.
This demonstrates that the present interface does not prove feature
provenance; it does not establish that any existing selector intentionally
used actual source scalars. [pcc:unverified]

The exact reproducer at head `e8a6ee3ad` was:

```python
import sys
sys.path.insert(0, "research/xedni_rank_decay_20261118")
import mechanism_panels as m

work = {
    "attempts": 1,
    "rejections": 0,
    "public_group_operations": 0,
    "cpu_ns": 1,
    "retained_bytes": 1,
}
rows = [
    {
        "candidate_id": "c0",
        "q_isomorphism_class": "i0",
        "public_features": {"proxy_curvature": 314159, "is_balanced": True},
        "construction_work": work,
    },
    {
        "candidate_id": "c1",
        "q_isomorphism_class": "i1",
        "public_features": {"proxy_curvature": 271828, "is_balanced": False},
        "construction_work": work,
    },
]
bank = m.freeze_candidate_bank("M3", 65521, "audit-bank", rows, 2)
prepared = m.prepare_candidate_bank(bank, 2)
spec = m.freeze_m3_selector("proxy_curvature", "min", "audit-seed")
result = m.select_m3(prepared, spec, spec["selector_hash"])
print(result["selections"]["nonlinear_proxy"])
```

Observed selection: `c1`. A valid natural executor must replace arbitrary
caller-supplied feature maps with a formula-bound implementation digest and an
OS-enforced public-only process before M3 rows can be admitted.
[pcc:unverified]

The authorization/preflight statement is registered as
`PCC-20261119-557206`. Its standing is unverified; the attached attestation is
producer evidence and does not independently verify execution.
[pcc:unverified]

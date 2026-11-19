# Authorized-run implementation and adversarial review

Date: 2026-11-19

Status: user authorization was received, but the mandatory checkpoint retry
failed and zero natural rows were started. The code in this review is
prospective, explicitly non-production scaffolding. It is not part of an
authorizing freeze. [pcc:unverified]

## Requested scope and actual execution

The requested experiment remains the frozen 16--32-bit factorial rank-decay
test with independent lift, `r`, and local-condition controls. After
authorization, the exact runner preflight exited 2 and the pushed-head
checkpoint `push` and `gate` both exited 1 for absent upload transport. The
licensed Magma runtime also remains absent. No substitute natural workload was
run. See [`RUN_AUTHORIZATION_20261119.md`](RUN_AUTHORIZATION_20261119.md) and
[`CHECKPOINT_GATE.md`](CHECKPOINT_GATE.md). [pcc:unverified]

## Locally implemented prerequisites

### Public/private boundary

[`public_boundary.py`](public_boundary.py) now provides strict private/public
schemas, nonce-bound redaction links, formula-bound M3 inputs, exact curve and
source-reduction replay, a nonroot/read-only/networkless isolated process, and
a source-bound direct BSGS baseline. The baseline validator reparses retained
stdout, binds the executed command and stream hashes, and verifies every
recovered coefficient by `[m_i]G=P_i`. Formula input excludes identifiers,
work counters, arbitrary feature maps, source scalars, and outcome data.
[pcc:unverified]

The final adversarial reproducer changed a recovered coefficient, rewrote all
producer-controlled hashes and stdout, and was rejected by exact DLP replay.
The focused suite passed 33 tests. The module deliberately declares
`PRODUCTION_READY=False` because it is not integrated into the runner or an
authorizing freeze. [pcc:unverified]

### Resumable row state machine

[`natural_executor.py`](natural_executor.py) provides immutable atomic row
artifacts, deterministic resume/tamper rejection, checkpoint/tool/public/
provenance gate injection, commitments-only public context, exact PARI/Magma
transcript replay, exact relation-certificate replay, timeout retention,
failure-safe work aggregation, and lock cleanup. Bounded proposal no-hits stay
`UNKNOWN`. Control receipts are marked `UNVERIFIED_CONTROL`. [pcc:unverified]

The focused suite passed 21 tests, including forged recovery, forged rank,
nonfinite JSON, duplicate rows, stale locks, private-value leakage, and
conflicting work-shape failures. Production mode fails before gates or rows
because no signed independent verifier backend is configured, the public
boundary is not freeze-integrated, and the runner has no natural command.
[pcc:unverified]

### Row provenance

[`row_provenance.py`](row_provenance.py) semantically replays roster/prime/seed
bindings, public/private redaction, tool version and transcript structure,
relation inventory, exact relation certificates, work counts, safe evidence
paths, and inode aliasing. The focused suite passed 48 tests. Prior forged-row,
scalar-leak, omitted-candidate, fake-version, hard-link, fake-work, and
arbitrary-absence canaries now reject. [pcc:unverified]

The validator intentionally returns only `HASH_GRAPH_ONLY` with
`production_eligible=false`. It cannot certify `CERT_NO` without a complete
relation-lattice verifier, and it does not yet replay the full freeze/git/tool
identity, lift/local certificates, or required rank cascade. [pcc:unverified]

### Mixed unresolved allocation

[`mixed_censoring.py`](mixed_censoring.py) exhausts bounded integer boxes and
implements the reviewed aggregate conditional-Poisson optimizer. Its focused
suite passed 9 tests. Binomial-cloglog remains state-limited, aggregate data do
not determine within-cluster allocations, and cluster bootstrap therefore
returns `BLOCKED`. See
[`MIXED_CENSORING_REVIEW_20261119.md`](MIXED_CENSORING_REVIEW_20261119.md).
[pcc:unverified]

## Validation

Exact command:

```text
cd research/xedni_rank_decay_20261118
python3 -m unittest discover -v
```

Observed producer result: 271 tests passed in 25.206 seconds, with zero
failures and six expected host-`gp` skips. The previously pinned PARI
container controls are not replaced by this host run. Independent adversarial
reviews were unsigned and are not PCC execution verification.
[pcc:unverified]

## Requirement status after authorization

| Requirement | Status after this work |
| --- | --- |
| Human authorization | Complete for this attempt |
| Checkpoint transport | Blocked: no profile/token/token file |
| Licensed Magma 2-descent | Blocked: no executable/image/license |
| Public/private component | Implemented and control-tested; not runner/freeze integrated |
| Natural executor | State machine implemented; production deliberately fails closed |
| Provenance | Semantic/hash diagnostic implemented; production eligibility deliberately false |
| Mixed censoring | Aggregate conditional-Poisson path implemented; cluster path blocked |
| Complete relation lattice | Not implemented; negative rows remain unknown |
| `r=7..9` selected-point map | Algorithm identified; Sage/Magma runtime and adapter absent |
| Powered discovery/replication | Not allocated |
| Natural calibration rows | Zero started |
| Decay conclusion | Not tested, not defeated, and not reproduced by this attempt |

## Exact remaining launch boundary

No natural row may launch until the pushed head passes the checkpoint gate,
a pinned licensed Magma passes controls, the new modules are wired into
`runner.py`, their implementation and verifier identities are added to a new
clean freeze, the freeze authorizes rows, and the full production preflight
passes. `r=7..9`, complete negative relation labels, cluster-bootstrap
inference, and powered discovery/replication remain separate gates after the
`r=2..6` feasibility calibration. [pcc:unverified]

# Resume: Xedni rank-decay falsification program

## Goal

Test the JKSST/Silverman finite-range Xedni decay heuristic from 16 through 32
bits while independently controlling lift strategy, selected-point count `r`,
and small-prime local conditions. Keep curve rank, selected-point dependence,
and useful target recovery as separate endpoints. A valid positive result needs
replication, exact recovery replay, complete work, and simultaneous signed
slope lower bounds above `-0.8`; controls or bounded relation hits do not count.

## Lead / hypothesis

The two strongest prospective mechanisms are a public constant-size bank that
minimizes normalized minimal discriminant, and quotient-compatible
reverse-Mestre local data matched against neutral CRT cost. Four additional
panels cover a public nonlinear selector, genuine `r=7..9` cubics, small-degree
isogeny neighbors, and nonisomorphic rank-one families. A mechanism signal is
insufficient: only replicated exact target recovery with the frozen decay rule
can defeat the finite-range model.

## Spec

The binding design is in
`research/xedni_rank_decay_20261118/{PROTOCOL.md,AMENDMENT.md,PRIMES.json}`.
The lower event cutoff is 20 bits, the simultaneous profile count is 4,320,
and the hierarchical bootstrap count is 172,800. The blocked `FREEZE.json`
records exact implementation/file/roster/tool hashes but is not authorization.

## State

- Repository: `/workspace/cryptanalysis`
- Branch: `codex/xedni-breakthrough-20261117` [pcc:unverified]
- Open PR: `#1768`
- Current implementation head before this resume update: `0dc4f8981`
- Core implementation commit: `cb8c4cf48bfba1e76f90536a62c029810c45c1a4`
- Blocked freeze/control commit: `e5fb9a69a715ea9ebfce48d0fad873c650443917`
- Control PCC record: `PCC-20261119-f7f325`, standing `unverified`
- Continuation PCC record: `PCC-20261119-0bba90`, standing `unverified`

The prospective design is in
`research/xedni_rank_decay_20261118/PROTOCOL.md` and `AMENDMENT.md`.
`FREEZE.json` binds the implementation, calibration/sentinel rosters, analysis
parameters, PARI image, and release binary, but deliberately sets
`natural_rows_authorized=false`. `runner.py` has a committed-byte
`validate-executor` diagnostic but no natural-row command. No natural
calibration, sentinel, discovery, or replication row exists.

At 2026-11-19T05:34:20Z the user explicitly said `Authorized to run`.
`research/xedni_rank_decay_20261118/RUN_AUTHORIZATION_20261119.md` records the
request-to-evidence ledger. This resolves the human authorization question but
does not waive or satisfy the independently required checkpoint, tool,
executor, certificate, inference, map, or power gates. No natural row was
started in response to the authorization.

The authorization evidence and exact checkpoint retry are committed. The retry
at pushed head `bfefa7c0a2a668643e3aabef5b6796b70a743b93` failed for absent
upload transport and started zero rows. The locally solvable continuation now
also includes a nine-component runner diagnostic, exact bounded nested-cluster
censoring, a supplied cubic-map verifier, a conditional complete relation-
lattice verifier, strict signed-receipt verification, and an exact unallocated
power/cost manifest. The final host suite has 382 passes and six expected
host-`gp` skips. Every module remains outside `FREEZE.json` and declares or
returns non-production state. See `CONTINUATION_RESULTS_20261119.md`; claim
`PCC-20261119-0bba90` is unverified.

At pushed head `cd0e9e91c`, `checkpoint.sh push` and `gate` both exited 1.
The gate reported no `ecc-challenges-new` profile, no
`CHECKPOINT_UPLOAD_TOKEN`, and no token file. No bypass was used. The exact
transcript is in
`research/xedni_rank_decay_20261118/CHECKPOINT_GATE.md`.

## Implemented scope

- Deterministic 27-prime manifest: three primes per even size 16--32.
- Scalable source generation with Miller--Rabin, Tonelli--Shanks, PARI
  `ellcard`, factorization transcript retention, and exact evidence replay.
- Exact no-local, compatible reverse-Mestre, neutral matched-CRT, `+1`, `+2`,
  and incompatible local controls.
- Exact balanced, wide, and optimized short-Weierstrass lifts for `r=2..6`.
  The `r=7..9` supplied-map verifier passes degree-one controls, but the pinned
  natural general-cubic constructor/global exceptional certificate remains
  blocked.
- PARI `ellrank` and Magma `RankBounds` adapters with staged fail-closed
  semantics. Immutable PARI 2.17.2 image:
  `sha256:923e7e41d2fe1716fc3f1a6e06486d469b608baa6d6b4b0fdbb6e43b132049cf`.
  No licensed Magma runtime is present.
- Exact minimal-model/discriminant/conductor maps, numerical height Gram data,
  stable normalized-score selector, and explicit unavailable statuses for a
  rigorous minimum-height lower bound and saturated Mordell--Weil regulator.
- Scalar-free bounded PARI relation proposer plus exact rational/source replay
  certificate for supplied candidates. Bounded no-hit is never an absence or
  independence certificate. A conditional complete-lattice verifier now
  checks a supplied full-basis decomposition, but no trusted full saturated
  Mordell--Weil basis is available.
- Six prospective mechanism-panel selectors/admission gates, strict analyzer,
  exact bounded nested mixed-censoring controls, deterministic roster/preflight
  runner, and four axiom-free Lean rank-decision theorems.
- Strict signed verifier-receipt parsing exists, but repository trust is
  `NOT_COVERED`; no trusted execution-verifier digest exists.
- Exact prospective power/cost arithmetic is retained in
  `POWER_ALLOCATION_20261119.json`; discovery is scale-only and replication and
  resources remain `UNALLOCATED`.
- Source-linked `README.md`, `pipeline.dot/svg/png`, `REPORT.pdf`, and the
  source-linked cubic transfer report/diagram/PDF.

## Producer-side controls actually run

Evidence summary: `research/xedni_rank_decay_20261118/CONTROL_RESULTS.json`.

- Final continuation host suite: 382 passed, 0 failed, 6 expected host-PARI
  skips in 68.540 seconds.
- Focused continuation suites: runner 25, mixed censoring 18, cubic/lattice 54,
  verifier receipts 26, and allocation 15 tests passed.
- Committed-head executor diagnostic at `0dc4f8981` bound nine component
  byte/schema checks and returned `BLOCKED_NON_PRODUCTION`, exit 2,
  `natural_rows_started=0`, while invoking no checkpoint, scientific tool, or
  stage adapter.
- Immutable PARI container invariant/relation suite: 25 passed, 0 failed.
- Rank-tool controls: 18 passed, 0 failed, including 11a1 rank 0 and 37a1
  rank 1.
- Lean 4.34.1: four theorems built and reported no axioms.
- Fixed non-natural `p=101` control: optimized `r=4` construction discriminant
  177 bits versus 495 balanced and 789 wide; normalized ratio about 13.5781
  versus 13.7088 balanced. PARI returned exact ranks through `r=5` and timed
  out at `r=6`. The bounded proposer found no exact relation for `r=2..6`.
- Planted relation controls for every `r=2..6` were proposed and passed exact
  rational/source replay. These controls are not decay evidence.

## Natural-run blockers

1. `scripts/checkpoint.sh push` and `gate` have not succeeded for this head.
2. `FREEZE.json` explicitly refuses natural authorization.
3. No licensed immutable Magma executable/image is available.
4. A non-production natural-executor state machine exists, but no runner
   command or freeze integration exists.
5. A hash-linked redacted public/private module and isolated M3 formula/direct
   baseline exist, but full lift/relation execution is not runner-integrated
   or freeze-authorized.
6. The provenance validator replays many semantics but deliberately remains
   `HASH_GRAPH_ONLY`; no trusted execution-verifier digest or immutable
   producer-independent keyring/base pin exists.
7. Exact bounded mixed and nested-cluster minimizers exist, but they have no
   freeze-bound execution allocation for the natural row set.
8. The conditional relation-lattice verifier has no trusted proof of a full
   saturated Mordell--Weil basis for negative labels.
9. The `r=7..9` verifier has no pinned natural general-cubic constructor or
   global nonlinear exceptional/reduction certificate.
10. Powered discovery/replication exposure, fresh replication primes, workers,
    wall time, and storage are not allocated.

The consolidated problem is
`problems/xedni-rank-decay-tool-map-and-power.md`; checkpoint transport is in
`problems/xedni-affine-cvp-checkpoint-access.md`.

## Runs in flight

None. No natural process or container is running.

## Next steps

1. Keep `natural_rows_authorized=false` while the independently required
   technical gates remain open; do not misrecord user authorization as a
   completed or executable freeze.
2. Restore scoped checkpoint transport and a licensed pinned Magma runtime;
   rerun their controls without `CHECKPOINT_SKIP`.
3. Configure a trusted execution-verifier digest with an immutable
   producer-independent keyring/base pin, then integrate the nine components
   into an actual natural command and a new clean freeze.
4. Pin a natural general-cubic constructor for `r=7..9` and a trusted full
   saturated Mordell--Weil basis route for negative relation labels.
5. Commit workers, wall time, storage, exact mixed-inference ceilings, and a
   fresh replication-prime manifest that meet a prospectively frozen power
   target; the current reference-scale manifest is not enough.
6. The first future allowed natural stage, after every gate is closed and the
   new authorizing freeze is checkpointed, is the excluded two-row-per-cell
   16/18-bit calibration. It is not an inference result.

## Recheck commands

```sh
cd /workspace/cryptanalysis/research/xedni_rank_decay_20261118
python3 -m unittest discover -v
python3 prime_manifest.py check PRIMES.json
python3 allocation_planner.py --check POWER_ALLOCATION_20261119.json
python3 runner.py validate-executor --output /tmp/xedni-executor-validation.json
docker run --rm --network=none \
  -v /workspace/cryptanalysis:/workspace/cryptanalysis:ro \
  -w /workspace/cryptanalysis/research/xedni_rank_decay_20261118 \
  --entrypoint python3 xedni-pari-rank:2.17.2 \
  -m unittest -v test_invariants_pari.py test_relation_pari.py
(cd formal && lake build && lake env lean XedniRankClassification/Decision.lean)
cd /workspace/cryptanalysis
python3 tools/pcc/pcc.py ledger verify --base origin/main
python3 tools/pcc/pcc.py standing PCC-20261119-f7f325 --json
python3 tools/pcc/pcc.py standing PCC-20261119-0bba90 --json
```

The runner diagnostic is expected to exit 2 with `BLOCKED_NON_PRODUCTION`; use
a fresh output path because it refuses to overwrite retained evidence.

## Stop and success conditions

Do not generate a natural source, lift, or outcome row while any blocker above
is open. A checkpoint failure, missing Magma, absent executor, or
`natural_rows_authorized=false` is independently sufficient to stop. Report
the heuristic as **not tested by natural rows**, not defeated and not confirmed.

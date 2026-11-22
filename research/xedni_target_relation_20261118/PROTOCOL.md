# Fresh-seed paired target-bearing Xedni relation protocol

Date: 2026-11-18

Status: prospectively specified; no natural outcome row may be generated
before this protocol, runner, analyzer, source hashes, binary hash, master
seed, and `FREEZE.json` are committed and the resume-checkpoint gate passes.
[pcc:unverified]

## Requested scope and baseline

The owner requested continued work toward a reasonable cryptanalysis
breakthrough.  The frozen baseline is the complete 1,600-row panel in
`research/xedni_plane_group_20261117`, where the minimum-weight selector
certified 67 exact relations but only 23 had an invertible target coefficient.
This successor tests a stage-level recovery improvement; it does not replace
the requested eventual end-to-end ECDLP comparison. [pcc:unverified]

## Question and paired intervention

On a fresh deterministic panel, does ordering auxiliary-field relation
candidates by an invertible coefficient on the designated target before
minimum coefficient weight increase exact target recovery relative to the
frozen minimum-weight ordering? [pcc:unverified]

Every row constructs one source instance and one optimized lifted cubic.  It
generates the bounded auxiliary-field candidate set once.  The baseline arm
orders candidates by `(L1 norm, coefficient vector)`.  The candidate arm
orders by `(target coefficient not invertible modulo subgroup order, L1 norm,
coefficient vector)`.  Each arm independently exact-checks candidates in its
order until the first rational group relation.  The selected candidate arm is
also checked by the frozen runner's exact lifted-cubic certificate and shifted
source recovery.  The wrapper independently replays the source RNG prefix and
checks both arms' shifted source residue and target recovery. [pcc:unverified]

The lift, points, chord origin, coefficient box `|n_i|<=2`, auxiliary primes,
affine optimizer, and all exclusions remain those of the frozen November 17
runner.  Target priority changes relation selection only; it may not change
which lift or candidate set is admitted. [pcc:unverified]

## Fresh panel and budgets

The master seed is `xedni-target-selector-20261118-v1`.  The panel is the
same prospectively fixed grid of primes `{31,67,127,251}`, curve families
`{generic,j0}`, coordinate lifts `{balanced,wide}`, ranks `{6,7,8,9}`, and 25
trials per cell: 1,600 paired rows.  It is sequential with a 1,800-second
external cap.  Every row and failure is retained. [pcc:unverified]

The exact post-freeze command is:

```sh
timeout 1800 python3 research/xedni_target_relation_20261118/runner.py run \
  --binary suite/target/release/ca-icx \
  --output research/xedni_target_relation_20261118/run/rows.jsonl \
  --master xedni-target-selector-20261118-v1 \
  --primes 31,67,127,251 --families generic,j0 --lifts balanced,wide \
  --r-values 6,7,8,9 --trials 25
python3 research/xedni_target_relation_20261118/analyze.py \
  research/xedni_target_relation_20261118/run/rows.jsonl \
  research/xedni_target_relation_20261118/run/summary.json
```

## Estimands, controls, and decision boundary

Primary counts are paired correct target recoveries among `ok` rows, overall,
by rank, and by full cell.  Secondary counts are certified relations and exact
candidate checks per arm.  The frozen positive control must exhibit a
minimum-weight zero-target relation and a distinct exact target-bearing
relation.  Any certificate failure, candidate-set change, loss of a baseline
certified relation, or baseline-only recovery invalidates the affected row
and requires repair before interpretation. [pcc:unverified]

A stage-level algorithmic improvement is observed if the fresh panel has at
least one candidate-only recovery, zero baseline-only recoveries, equal
certified-relation counts, and complete exact-check accounting.  The exact
paired gain and added checks must be reported; no timing or asymptotic claim
is made from this ordinary local host.  An end-to-end breakthrough still
requires a named complete pipeline, all phases, fresh single targets, matched
Pollard rho, independent scalar replay, and the repository measurement gates.
[pcc:unverified]

## Prior evidence and sources checked

- `crypto-autoresearcher:knowledge/leads/ecdlp/ic-prime/LEAD-ICP-char0-lifting-xedni-smoothness.yaml`
  (`LEAD-ICP-char0-lifting-xedni-smoothness`): the closed-known lead explicitly
  permits revisit after a certified bounded dependent lift. [pcc:unverified]
- `crypto-autoresearcher:knowledge/frontiers/ecdlp/index-calculus/KR-IC-cd159a.yaml`
  (`KR-IC-cd159a`): classical negligible-probability obstruction; this panel
  does not claim to remove it. [pcc:unverified]
- `crypto-autoresearcher:analysis/xedni-cheon/20261007-certificates/REPORT.md`:
  earlier prescribed two-point lift baseline and finite bounded-search null.
  [pcc:unverified]
- The shared research-KB CLI was attempted but no executable was available in
  this environment; the lead atlas and its cited primary repository records
  supplied the fallback review. [pcc:unverified]

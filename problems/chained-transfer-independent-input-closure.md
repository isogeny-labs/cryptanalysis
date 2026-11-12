# Independent chained-transfer source and runner input closure

- **Status:** investigating
- **Kind:** implementation gap: complete source and runner inputs
- **Affected work:** [PR1509](https://github.com/isogeny-labs/cryptanalysis/pull/1509),independent0796 replay
- **Next action owner:** continuing research session
- **Last updated:** 2026-11-12

## Problem

The independent32/23/32module job lacks a passing exact-head CI because its
driver assumes ripgrep,absent on the runner;original reference98 is green.
[pcc:unverified]

## Evidence and uncertainty

Local01/56d812 failed on the Git-ignored lockfile;02/d11dfb on a missing
sparse JSONfixture. Exactdd03/0796 repair both;local03/db5e8a and root0796
CI43230599875/bfbd6b pass. Consumer8f CI43232186220 overall fails despite
reference25/98 success:independent32 pass,then driverline48 exits127,rg
missing;algebra/proofs NOT RUN. Full55e8da logs/custody retained.
These are input-closure failures,not mathematical counterexamples.
[pcc:unverified]

Missing implementation:portable parsing,explicit preflight and a no-rg replay.
Existing evidence does not establish that the patched exact-head CI will pass.

## What would unblock it

- [x] Complete no-rg replay of unchanged0796:32/23/two certificates/
  32modules/160written/186compiled/0trusted,unchanged hashes and admissions.
- [ ] New exact consumer-head CI passes both complete98reference and
  independentjobs,with full logs and no weakened criteria.

These close this runner gap;signing,ledger/C merges and costs remain separate.

## Next discriminating step

Apply INDEPENDENT_REPLAY_PROTOCOL_V4.md:equivalent grep parsers and preflight,
20min full04 with an always-failing rg shim. On complete output,publish the
fix on existing1509 and inspect its CI at normal cadence. On failure,retain
all source/raw/status and diagnose the exact missing input. Recheck on newCI.

## Resolution and history

Unresolved. Earlier failed/successful attempts remain separate and immutable;
this record does not close the missing CI gate.

2026-11-12:local04/22ad5d satisfies the no-rg32/23/32module criterion,all695+9
hashes andthree admission controls;one129-file tar.xz55,488bytes retained.
The exact new-head two-job CI is still required;status remains investigating.
[pcc:unverified]

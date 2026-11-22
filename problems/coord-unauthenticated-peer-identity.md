# Distributed-rho coordinator peers are not authenticated

- **Status:** `open`
- **Kind:** implementation gap (protocol design); not a mathematical obstruction
- **Affected work:** audit findings C-F6, C-F7, C-F8 and C-F10 in
  [`docs/audits/2026-11-18-correctness-validation-second-pass.md`](../docs/audits/2026-11-18-correctness-validation-second-pass.md)
  (§4.4); `src/coord.c`, `src/coord_net.c`, `bindings/go/cmd/ca-coordinator`
- **Next action owner:** unassigned
- **Last updated:** 2026-11-18

## Problem

The coordinator cannot tell an honest lane's unit report from a forged one,
because a check-in's peer name is a self-declared string. Every agent and
hub shares one bearer token (`coord_net.c`), so any token holder can write
under any name.

What this blocks: progress figures (`steps`, `dead_trails`,
`units_completed`) that hold against a token holder who lies. Correctness of
the solve does not depend on them: points are checked (`a*G + b*H == point`),
a claimed solution is checked against the target, and a skipped unit is
replaced by a fresh one, which is equally useful to a random walk.

## Evidence and uncertainty

- **Observed:** the audit's reproducers for C-F6, C-F7, C-F8 and C-F10
  (Release and ASan+UBSan, 2026-11-18). The regression tests added with the
  fix, in `tests/test_coord.c` (`test_forged_twin_does_not_drop_the_real_checkin`,
  `test_checkin_numbers_are_strict`, `test_seq_cannot_wrap`,
  `test_impossible_unit_reports_are_refused`), fail 29 checks on unchanged
  `main` and pass with the fix. A fifth test in the same change
  (`test_lane_charges_walker_start`, C-F12) is unrelated to authentication.
- **Derived:** with names unauthenticated, nothing receiver-side can refuse a
  report that is internally consistent. The clearest case is a unit reported
  complete with every walker a dead trail: a dead trail leaves no evidence,
  and under the negation map honest dead trails can be common, so no
  statistical bound on them is safe.
- **What the fix closes:**
  - A different line under a known (peer, seq) is merged, not dropped as a
    resend. Lines under a conflicted pair are sent in every delta.
  - Numeric wire fields are strictly decimal or hexadecimal and must fit in
    64 bits.
  - Sequence numbers are bounded by `CA_COORD_SEQ_MAX`, and a lane whose
    sequence space is spent stops with an error.
  - Impossible unit reports are refused (cursor past the unit, more trails
    than walkers, completion before the last walker, more steps than the
    walkers can take).
  - The fleet step and dead-trail totals saturate instead of wrapping.
- **What remains:**
  - A consistent forged report still inflates progress and can mark a unit
    complete.
  - Lines under a conflicted (peer, seq) are resent on every delta, so a
    token holder can make every sync carry its forgeries.
  - Two replicas that each hold a different line for one (peer, seq), and
    never hold both, do not exchange them through the version vector. The
    real line always reaches the hub its lane sends to, which makes this
    unlikely, but it is not excluded.
- **Missing capability:** per-peer credentials (for example, a per-lane key
  issued with the job and a MAC over each encoded line) that the merge
  checks.
- **What this evidence does not establish:** that the coordinator is safe
  against a token holder. It shows only that the specific failures above no
  longer occur.

## What would unblock it

- [ ] Each check-in line carries an authenticator bound to its peer name that
  `ca_coord_apply` checks before merging, with a test showing that a line
  forged under another peer's name is refused at the hub and at an agent.
- [ ] A line under an authenticated (peer, seq) is then unique, so the
  conflicted-line resend can be removed, with a test that a resend is still
  a no-op.

Both are needed for progress figures to hold against a token holder. Neither
changes the solve's correctness argument.

## Next discriminating step

- **Action:** design note for per-lane keys in the job document (issued by
  the hub at `/v1/job`), covering key distribution to a sharded hub set and
  agent restarts (`ca_coord_node_instanced`).
- **Recheck trigger:** any change to the wire format or to `coord_net.c`
  authentication.

## Resolution and history

- 2026-11-18: opened with the fixes for C-F6, C-F7, C-F8 and C-F10.
  Unresolved.

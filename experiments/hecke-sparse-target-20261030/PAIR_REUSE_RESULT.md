# Pair-index relation reuse strengthens the generic baseline

2026-10-30. Verified finite stage result; **same-total-budget superiority remains
unestablished**. This continues the existing Hecke/index-calculus goal and
follows merged PR1317. The four original field/point/target fixtures are unchanged.

## Measured information

The signed pair index required for the original target oracle is now built
before solving base logs. When P_i+P_j=P_k+P_l, its collision gives a valid
linear relation. Known negation/zero identities are removed after coefficient
folding. Retaining these collisions uses exactly the original curve sums;
coefficient bookkeeping and elimination are additional work, not free CPU time.

| Subgroup r | Folded columns | Previous Hecke/scalar free logs | Pair-only rank / free logs | Hecke + pair rank / free logs | Marginal Hecke rank over pair-only |
| --- | ---: | ---: | --- | --- | ---: |
| 769 | 32 | 9 | 31 / 1 | 31 / 1 | 0 |
| 16,319 | 32 | 12 | 21 / 11 | 31 / 1 | 10 |
| 206,477 | 32 | 12 | 1 / 31 | 20 / 12 | 19 |
| 46,273, conductor30 | 159 | 45 | 158 / 1 | 158 / 1 | 0 |

Thus pair-index reuse lowers required generic log queries9→1,12→1, and45→1
on three fixed cells. It does not reduce the12 remaining queries on the
sparsest cell. The earlier doubling/tripling-only generic comparison is a
weaker control; its original measured values remain correct for that method,
but must not be read as the best available generic preprocessing baseline.
In particular the conductor30 pair-only system already has rank158, so
Hecke supplies no further rank there under this stronger comparison.

Hecke still supplies10 and19 marginal constraints on the medium/large f6
cells, respectively. This is information beyond this complete pair-collision
collector, not a lower bound against every same-budget generic algorithm.
The extra cost of generating the Hecke relations has not been fully priced.

## Costs, controls and target behavior

Index construction still uses2145 additions for each f6 cell and51040 for
conductor30, exactly matching the original index. Its input point set and,
on the large field, its point-set digest match the frozen arity-control index.
Every unordered signed pair is enumerated, including duplicates, even after
the retained relation basis reaches maximal possible rank.

The frozen sqrt(r)-sized BSGS table is unchanged across arms. Counts below
cover generic base-log queries and each query's scalar replay, not geometric
construction, matrix bookkeeping, or final all-label replay.

| r | Previous Hecke/scalar query additions | Generic pair-only query additions | Hecke + pair query additions |
| --- | ---: | ---: | ---: |
| 769 | 219 | 33 | 33 |
| 16,319 | 858 | 897 | 94 |
| 206,477 | 3836 | 9902 | 3836 |
| 46,273 | 5941 | 73 | 73 |

Fewer generic queries do not automatically mean proportionally fewer additions:
the generic medium-field arm uses11 queries but897 additions versus the
previous12-query arm's858 because different free points require different
search lengths. Full costs and qualified speed ratios remain unknown.

All three arms on all four cells recover identical base labels and preserve
the original target statuses: three successes at the same attempt counts,
and the large-field256-attempt failure. Changing label preparation leaves
the base point set and target coverage unchanged. No additional target
decomposition or fresh-target success is claimed.

## Reproduction and verification

[PAIR_REUSE_PROTOCOL.md](PAIR_REUSE_PROTOCOL.md) was committed locally before
enumeration. Publication of that commit was delayed by a concurrent merge
into the shared PR branch; it was preserved and merged without force-pushing.
These are exploratory fixed-fixture controls, not an independently public
holdout. No earlier raw receipt was modified.

Run `run_pair_reuse.py --out-root UNIQUE_DIRECTORY` through the checkpoint
gate. It retains all four attempts, including failures, with600-second cell
and2400-second suite caps. [runs/pair-reuse-01](runs/pair-reuse-01) contains
the outputs, source/input hashes, group counters, collision-basis rows and
explicit four-point witnesses. A separate short-Weierstrass implementation
re-enumerates all57,475 pairs and independently checks the rank of all21,118
nonzero collision rows, not just the retained basis. It also replays all765
base-label checks across the three arms (255 points per arm).

Two additional unit tests check dependent/independent coefficient rows, a
hand-known five-torsion collision, zero identities, and rejection of a
corrupted witness. The earlier four arithmetic tests remain required.
The geometric interpretation and Lean limitations remain as stated in
[PROOF_MAP.md](PROOF_MAP.md); no new global theorem is claimed.

## Remaining blocker for the external goal

The requested same-total-budget advantage is still not established. It needs
a declared complete cost boundary that charges geometric function/fiber
construction, coefficient tracking, LA, bootstrap and target work for both
arms, along with stronger generic collectors and fresh single-target controls.
Reusing a table gives a verified improvement in query preparation within this
pipeline; it does not settle that comparison.

The selected environment has no NVIDIA device or configured RunPod/Modal/fleet
compute binding; [access evidence](validation/pair-reuse-compute-access.json)
records presence checks without secret values. The repository's
[AGENTS.md](../../AGENTS.md#run-index-calculus-on-a-gpu) states:
"Index-calculus runs, benchmarks and measurements execute on a CUDA GPU host."
Qualified cost/rho measurement is blocked on
that execution capability; ordinary-host correctness diagnostics do not
substitute for it. This is an access/measurement gap, not a proof that a
Hecke advantage is impossible. The source problem record retains the goal.

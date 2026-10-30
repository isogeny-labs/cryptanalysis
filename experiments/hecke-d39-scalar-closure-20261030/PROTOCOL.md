# D=-39 scalar-closure discriminator

Status: proposed; no new numerical result claimed. User request: pursue Hecke
index calculus from the cited low-conductor experiment.

## Frozen input and baseline

Input: `../ecdlp-hecke-d39-holdout-20261026/data/exp11_class_walk_D39_f6.json`
at revision `cf35a825b25c3f1ece5d7d36dd98d78ea66a4022`.
Input SHA-256: `4bcc8eb1905a9ed79a47cc31820e722dc7a6ff87f18bb37aeebafa35e6cc6df9`.
Curve: y^2+y=x^3-x^2-10x-20 over F_367 (X_0(11), 11a1).
Saved order 385=5*7*11; work modulo r=11, projecting P to [35]P.
Keep all 64 original columns, even when projected points coincide.
Baseline: 48 Hecke rows, rank 40; adding 64 Atkin–Lehner rows gives rank 52.
These are relation-stage diagnostics, not a verified complete IC baseline.

## Fixed arms

Can small scalar identities supply the 11 extra independent constraints needed
to reduce nullity from 12 to one, before a known-log anchor?

Compare six arms: Hecke; Hecke+Atkin–Lehner (baseline); baseline+projected
equalities/zeros; baseline+multiplier 2; baseline+multipliers 2,3;
baseline+all those equalities and scalar identities.
For each m in {2,3}, add e_j-m*e_i whenever [35]P_j=[35m]P_i.
Add e_i for projected zero and e_i-e_j for coincident projections.
Verify every row in the projected elliptic-curve group; do not collect by
enumerating logs. Count rows, rank, nullity and group operations.

## Controls

Independently count curve points (small-field correctness control), check every
serialized point and Hecke row in the full group. Check Atkin–Lehner rows after
projection: their full-group identities have a torsion offset. Require every
projected point killed by 11, with at least one nonzero point. Cross-check ranks
with independently written elimination routines. For a nullity-one outcome,
anchor the first nonzero projected column to one and independently verify all
recovered scalars against that point. This normalizes logs within the saved
base; arbitrary-target descent is not supplied by this step.

## Execution and interpretation

One saved finite fixture, no random seeds or fresh targets, no timing claim.
Stop after six arms; fail closed on invalid rows or rank disagreement.
Launch only after `bash scripts/checkpoint.sh gate` succeeds, with timeout 60.
This CPU-only correctness/rank audit is not a CUDA IC benchmark. Retain receipt,
source/input hashes, operation counts and failures in a unique run directory.
Any increase is a relation-stage result, not a speedup. If rank improves, test
larger frozen classes with the same multiplier budget and matched random-set
controls next. Collisions inside an 11-element subgroup can be a density effect.
If rank does not improve, retain the null result and inspect the residual kernel.
Beating rho remains unestablished without a complete solver, target descent,
independent replay and matched single-target measurements.

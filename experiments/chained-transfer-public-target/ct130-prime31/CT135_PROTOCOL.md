# CT135 — fast-inverse cold CM comparator; scope and prospective holdout

2026-11-15. [pcc:unverified]. CT134 #1545 child, CT133 #1542 comparator and root crypto #3877.

## Already executed exploratory panel (NOT prospective)

Locally, before this protocol was committed, CT135 re-ran CT133's published four seed labels
20261210–20261213, 64 public targets per panel with six cold solver calls each. This is a
**retrospective engineering comparison** against a native source implementation using extended
Euclid inversions instead of exponentiation inversions, and is not a new preregistered holdout.
Preserve it and its failures; never promote these panels as an independent prospective experiment.

## Prospective exact-head CI holdout (frozen before launch)

Run exactly seeds **20261220, 20261221, 20261222, 20261223**, each **64** distinct public targets,
with **six solver calls per target** in orders ABCCBA/CBAABC. The same source E/F_p, q, G, target
j=1728, H and degree-2 phi as CT133: p=2147483033, q=536857417,
a=622683939, b=2147483024, G=(911976709,415929193),
T: y²=x³+9x, H=(180482573,1535800095). Both rho arms use the same
extended-Euclid finite-field inversion routine. A: fresh-table source BSGS;
B: 32-jump source negation-map rho; C: 32-jump target order-four rho
with phi(G),phi(Q) inside each timed solve. Six rho restarts * 200000 step cap;
fail the whole panel on any crash, wrong answer, invalid point, duplicate k or mismatch.

Compile with `g++ -O3 -std=c++17 -Wall -Wextra -Werror`. No paid EKS/Spot.
Capture compiler/CPU/OS, ordered stdout/stderr, SHA256, elapsed raw ns, operation counts,
kernel/resource limits and process RSS (via /usr/bin/time -v if available).
Run independent pure-Python arithmetic auditor normally and with `-O`; require both
positive/audit reports to agree and reject all nine corrupted-record controls.

**Primary scoped metric:** same-host min(total source BSGS, total source negation rho) /
target fourfold rho, including mapping G/Q and source postverification, across all 256 public
queries; per-panel metrics and paired bootstrap descriptive interval. This compares
*only* three portable C++17 algorithms. Curve construction, generator search,
native full-Jacobian corrections, CT126 C169/C13/D, strongest optimized source
rho/IC, actual execution proof, signed PCC and full prime-field generality are absent.

## Control and decision tree

- If target loses, record the complete negative result and switch to source-optimized
  projective/batched rho or non-generic IC.
- If target wins, compare next with an optimized projective/batched source rho and
  source-side endomorphism/pullback, and enforce source-side cold IC and full-Jacobian
  transfer/correction/setup memory before calling the owner acceptance criterion.
- If a check fails or runtime times out, retain full raw failure, do not reselect seed,
  curve or fixture and do not infer performance from censored runs.

Sources checked: crypto #3877/#4215 and cryptanalysis #1523/#1534/#1539–1545, CT133/CT134
protocols and reports, standard Vélu and GLV methods. Shared KB/lead-atlas checkout
unavailable in this runtime; no claim that a lead is novel or unsearched.

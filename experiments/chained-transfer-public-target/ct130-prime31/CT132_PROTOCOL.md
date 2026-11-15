# CT132 — prospective three-arm cold single-target cost gate (2026-11-15)

**[pcc:unverified].** Child of CT131 #1540; root crypto #3877. This file is committed **before** any CT132 implementation/timing. Existing CT130/CT131 sources, archived 695/672/701 Jacobian fixtures, native CT126 pricing and PCC ledger are untouched.

## Hypothesis and control

The reported 1.026x and 1.230x CT131 toy ratios compare target four-orbit rho only against a source negation-rho, and may vanish relative to a distinct complete source BSGS algorithm. Hold fixed the **same** ordinary E/Fp with p=2147483033, q=536857417, source G=(911976709,415929193), explicit degree-2 map to target T with H=(180482573,1535800095), lambda=390258842 and i=392507391. No smooth-order replacement.

Run three genuinely *cold* single-target public-Q arms, all on the same Python affine backend and host: A = fresh-table source BSGS, B = fresh-jump source negation rho, C = point-transfer + fresh-jump target fourfold GLV rho. Include all setup per invocation, both transfer maps for C, source-log verification, group addition/inversion counts, rho fruitless cycles, BSGS table entries, and whole-process maximum RSS. Mark curve/fixed parameters as predeclared (not a cold discovery measurement); separately report their discovery cost as omitted. No caching of baby tables, jump tables or mapped public Q across solver invocations.

Predeclare two independent random.Random scalar panels seed **20261118** and **20261119**, **24** public Q values per panel, scalar drawn in [q//8,q-1). Each panel runs in a separate process; each target uses either A,B,C,C,B,A or C,B,A,A,B,C, alternating by target index; every arm twice. The planted k is allowed only in fixture generation and **after** the actual solve, not passed to solvers. Rho seeds are seed+19*index; finite bound 300,000 steps x 6 retries; failures/timeout are kept, never resampled. The existing CT131 rho solver is used unchanged.

Primary diagnostic: *per-process* total(A+B sources? No): the best source cold clock among A or B is **min(sum(A),sum(B))**, compared with sum(C). Report A/C and B/C separately, between-process variation, each A/A max/min distribution, actual scalar errors, and resource scope. Do **not** mix individual fastest samples across algorithms, multiply historical ratios or use this toy screen as a strongest native rho/IC/full-Jacobian claim. No automatic promotion if C wins one process.

## Gates before interpretating numbers

Require exact public curve/subgroup/isogeny/CM checks, 24 distinct public Q per panel, three arms per target, exact ABCCBA/CB AABC order as listed without editing, two repeats per arm, same scalar returned and checked against original G for every solve, 4*baby_step entries consistent with isqrt(q-1)+1 for each BSGS run, bounded rho iterations, positive timing samples, no use of Python assert in the evidence verifier. Preserve complete raw JSON and hashes; independent validator must reject mutations under regular Python and Python -O.

The produced observation remains [pcc:unverified] until a signed independent PCC verdict, exact-source CI and matched native repeat. All native C169, C13a, C13b, D, original 701 and full Jacobian/IC/LA costs are outside this small portable test. If C loses or is unstable against either source method, log that as an explicit negative and return to CT126 pricing; if C wins, test native strongest rho/BSGS/IC on an uncorrelated curve set.

## Prior art and bounded scope

Existing CT130 #1539, CT131 #1540, CT126 #1534, CT129 #1537, root #3877 and crypto GPU IC #4178 read before design. GLV 2001: https://www.iacr.org/archive/crypto2001/21390189.pdf; rho/automorphism cycles: https://eprint.iacr.org/2011/008.pdf. KB MCP and repository wrapper unavailable in this runtime; no novelty/absence claim. No paid EKS/Spot, no protected merge or prior ledger mutation.

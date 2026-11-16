# CT155 — projective / batch-inversion BSGS public-source comparator

Date: 2026-11-16 UTC. Stacked research PR cryptanalysis #1589; root crypto #3877. [pcc:unverified].

**Prospective for paired timing; exploratory arithmetic debugging preceded this commit.** Compare the frozen CT154 **public Q only** BSGS against a new same-curve BSGS using Jacobian coordinates and Montgomery batch inversion, retaining CT153/154 sources byte-for-byte. Existing original-source field: F223[z]/(z^3-3), E coefficients a2=(127,56,199),a4=(152,35,36),a6=(212,109,150), generator G=((162,197,140),(45,11,207)), ell=2773073. This is not a Jacobian transfer solver or a prime-field source.

Require: independent affine-versus-projective scalar checks including infinity/doubling/inverses; complete recovery on six frozen public test points; negative invalid-coordinate, off-curve, outside-subgroup and corrupted-result controls; independent Python recomputation of every output. Alternate 2 balanced process blocks of CT154 BSGS / candidate (fresh processes), record raw rows, source/tool digests, field inversions/mults, solver and spawn-wall timing, VmHWM, A/A drift and paired uncertainty. No performance conclusion without those checks. No changed original Jacobian fixture/695 or 701-record producer logs; no paid EKS jobs, ledger change, or protected merge.

Prior art: CT153/154 reports, CT125 #1533, CT142 #1562, crypto #4215 / #4178, Bernstein–Lange Explicit-Formulas Database https://www.hyperelliptic.org/EFD/g1p/index.html (Jacobian arithmetic), conventional simultaneous inversion. Research-KB MCP and local wrapper unavailable in connector-only runtime; no novelty claim.

Global acceptance remains owner-admitted same-host native C169, C13a/C13b, D, independently checked whole 695/701 norm parity, complete transferred public DLP, and strongest matched cold rho/BSGS/IC including setup/LA/transport/verification/RSS/CI/PCC. This scoped generic baseline can change which reference is strongest but does not discharge the transfer gate.

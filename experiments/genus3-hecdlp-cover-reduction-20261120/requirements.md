# Requested scope

Find a drastic reduction for the hyperelliptic-curve/Jacobian DLP produced by
an ECDLP cover, without substituting a constant-factor speedup for an [pcc:unverified]
end-to-end reduction.

| Requirement | Acceptance evidence |
|---|---|
| Identify an exponent-changing transfer | Source and destination algorithms with explicit asymptotic exponents |
| State the applicable cover family | Genus, characteristic, field, curve model, and rational-kernel requirements |
| Preserve the transported ECDLP subgroup | Kernel-intersection and dual-recovery certificate |
| Retract cover-lifted instances | Pullback/pushforward identity, composed recovery formula, and explicit exclusion of arbitrary Prym/Jacobian classes |
| Make applicability testable | Reproducible factorization-type/perfect-matching screen |
| Validate the claimed coverage | Independent reproduction of the published factorization table and asymptotic success proportion |
| Measure the scaling primitives | Verified generic logarithms, verified plane-quartic relations, raw timings and operation counts, and fitted slopes with no cryptographic-size extrapolation |
| Run a complete toy HECDLP | Exact genus-3 Jacobian arithmetic, full-rank relations, factor-base linear algebra, individual-log recovery, and same-target rho timings |
| Measure signed transfer and recovery | Explicit signed map, DLP preservation, polarized-dual composition, recovery scalar, timings, and separation from the unresolved P-224 map |
| Preserve limitations | Explicit distinction between modeled advantage, executable construction, and measured end-to-end advantage |

No production key-recovery or cryptographic-size discrete-logarithm run is in
scope. Public structural checks, toy/bounded validation, and cost modeling are
in scope.

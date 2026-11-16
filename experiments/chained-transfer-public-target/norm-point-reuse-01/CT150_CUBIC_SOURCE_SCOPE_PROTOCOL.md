# CT150 — prospective cubic-source and quotient-injectivity scope audit

Date: 2026-11-15 (America/Denver). Standing: [pcc:unverified].
Follow-up to CT149 on cryptanalysis PR #1589; root crypto PR #3877. This is a source-domain and finite-group audit **not** a new q223 mapping, public-target solve or speedup.

## Frozen input claims and field qualification
Read source prime 223 from CT126 `primitive-pricing-01/src/main.rs`, the degree-three Weil-restriction / polarized-degree statement in root `08-MAP_NORMS_AND_DEGREES_01.md`, and the two previously **reported**, not independently recounted, rational source-group orders from CT149:
- original fixed: ell=2,773,073, full N=11,092,292=4ell;
- fixed nu12: ell=2,771,711, full N=11,086,844=4ell.

Treat the two source models separately. The field for these finite transfer tests is assumed to be `F_(223^3)`; do not identify it with `F_223`. A root/consumer source audit must bind that assumption independently before a stronger claim.

## Exact tests prescribed
For q=223^3, compute cubic trace T=q+1-N. Exhaust every possible trace t of an F_223 elliptic curve, |t|<=floor(2sqrt(223))=29. Under base change to F_(223^3), T must equal t^3-3*223*t. Report every model's exact membership verdict and minimum absolute trace gap. A **negative** verdict conditionally forbids F_(223^3)-isogeny to the cubic base-change of an elliptic curve defined over F_223, since isogeny preserves finite-field point counts; it does **not** rule out Weil restriction to a threefold over F_223.

Separately use the group-homomorphism kernel-size criterion: for genuine degree-8 quotient and genuine degree-169 elliptic composite, the induced three-dimensional geometric degree is 8*169^3. If gcd(ell,8*169^3)=1, restriction to the ell-subgroup is injective. Check gcd(4ell,8*169^3) explicitly and **do not infer** full-group injectivity when it is greater than one. This is a necessary structural arithmetic certificate **conditional** on the actual geometric/program maps being homomorphisms with those degrees, not a constructive decoder or a finite-record map check.

## Test controls, acceptance and boundaries
The standalone deterministic script must run under normal and optimized Python with byte-identical JSON; reject wrong cofactor-four source order and composite base characteristic; positively accept a constructed Frobenius trace t=4 base-change order (a polynomial control, not a curve implementation); retain a kernel-degree 2-primary negative qualification. Do not mutate existing frozen artifacts, PCC ledger, PR #3877 or CT149. Do not dispatch EKS/Spot, hosted native timing, or paid compute.

Success for CT150 is a reproducible **conditional** field-descent obstruction/injectivity-scope analysis only. It cannot certify original-prime p31/NIST DLP transfer, C169/C13/D pricing, 695/701 actual parity, complete cold rho/BSGS/IC comparison, or signed PCC. Record the exact remaining prime-field bridge as a separate obligation.

## Sources consulted
Root crypto #3877 frozen `public-n4-complete-chain-checkpoint-01` outcome and `08-MAP_NORMS_AND_DEGREES_01.md`; cryptanalysis #1589 CT149 report and CT126 compiled source; standard Weil-restriction point-functor identity and elliptic Frobenius characteristic polynomial (Silverman, *Arithmetic of Elliptic Curves*, ch. V). Shared research-KB MCP and checkout-local CLI/Conductor unavailable in this runtime. No novelty/absence claim.

# Fixed-nu12 geometric prime-field algebraic transfer obstruction

- **Status:** investigating; fixed class excluded conditional on CT160 source identity. [pcc:unverified]
- **Kind:** proved conditional mathematical obstruction for one target isogeny class; implementation/performance gap for the replacement
- **Affected work:** [cryptanalysis #1589](https://github.com/isogeny-labs/cryptanalysis/pull/1589), [root crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [CT166 report](../experiments/chained-transfer-public-target/norm-point-reuse-01/CT166_GEOMETRIC_CM_REPORT.md)
- **Next action owner:** chained-transfer researcher, subject to original compute-admission gate
- **Last updated:** 2026-11-16

## Problem

No source elliptic curve over F223 admits a nonzero *algebraic* homomorphism over **any finite extension** into the actual fixed-nu12 Weil-restriction isogeny class, conditional on the CT160 actual elliptic model/point-count binding. This target cannot carry the requested prime-field ECDLP by an algebraic homomorphic route. The existing extension-field transfer, even if sped up, must not be conflated with a complete prime-field attack. [pcc:unverified]

## Evidence and uncertainty

- **Observed:** CT160 reports actual fixed-nu12 source/target #E(F223^3)=11,086,844; CT161 shows irreducible degree-six F223 Frobenius, CT165 shows the odd-primary abstract **F223-rational** point-group obstruction. CT166 source-checker and independent Node checker bind the unchanged CT160 Git blob and test finite CM arithmetic; original signed PCC remains unverified.
- **Derived:** T=2724, D=T²-4·223³=-4·23·311·1291 and End^0 of the ordinary geometric elliptic factor is Q(sqrt(-9234523)). Every ordinary E/F223 instead has End^0=Q(sqrt(t²-892)), |t|≤29, t !=0, with squarefree radicand magnitude at most 892. Supersingular t=0 cannot map nontrivially into an ordinary target via an isogeny. After geometric base change, Weil restriction decomposes into conjugate ordinary factors sharing the target CM field; any F223-isogenous quotient has the same geometric factors up to isogeny. Hence no algebraic geometric hom, but only under the actual model binding.
- **Suspected explanation:** none needed for this conditional algebraic obstruction; it is a standard isogeny-invariant CM mismatch.
- **Missing capability:** first exhibit a *different* target isogeny class with matching source-geometric CM plus an explicit scalar-blind subgroup-injective evaluator and complete solver. Separately, actual native 695/701 whole Jacobian parity and admitted C169/C13a/C13b/D are unexecuted in CT166.
- **Not established:** impossibility of nonalgebraic encoded transfer, rational point-group maps over larger extensions, geometric CM classification of alternative target families, independently signed CT160 census, or any cold end-to-end prime-field ECDLP speedup.

## What would unblock it

- [ ] For a chosen actual E/Fp, identify a new target B and explicit algebraic source-to-target map over a stated field with certified nonzero image and injectivity on its DLP subgroup, including all maps and correction branches.
- [ ] Independent end-to-end public-target recovery on identical source inputs, with complete cold setup, transport, corrections, relation/linear algebra, verification, peak RSS, paired strongest rho/BSGS/IC, A/A, CI, and PCC.
- [ ] Independently replay all frozen original/reuse 695/701 records and, with owner admission, same-host primitive timing, preserving all negative/exception rows.

The first condition resolves algebraic feasibility for a *new* source/target pair, not the complete cost objective. The second resolves the measured objective only if verified baseline/candidate>1 including all costs.

## Next discriminating step

- **Action:** Screen a candidate target with *source matching geometric CM* and explicit map/evaluator; in parallel preserve the owner-gated native CT125 whole replay queue rather than running unauthorized compute.
- **Inputs/controls:** fixed prime-field elliptic curve and subgroup; positive compatible CM pair, deliberate incompatible CM negative, checked original/reuse native corpus and strongest matched rho/BSGS/IC.
- **Limits:** source-only arithmetic permitted; no unapproved EKS Spot/GPU/native spend or protected merge. Existing CT141 budget/admission gate applies.
- **Outcomes:** matching CM is necessary but not sufficient; failure excludes an algebraic route for that pair; a valid map permits complete timing, not a speedup claim; incomplete evidence retains [pcc:unverified].
- **Recheck trigger:** independent CT160/PCC evidence, new candidate target, or approved native replay and pricing.

## Resolution and history

- 2026-11-16: CT166 conditional geometric CM obstruction derived and source-only implementations committed, without signed PCC. The *fixed-nu12 algebraic* route is mathematically excluded under the stated source conditions; the larger cheaper-ECDLP goal is unresolved. [pcc:unverified]

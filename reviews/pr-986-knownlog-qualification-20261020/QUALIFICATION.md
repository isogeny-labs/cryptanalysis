# PR #986 measurement and theory qualification

This additive qualification preserves the frozen experiment README, receipts, and numeric results. It corrects how the PR's reference row describes the theoretical comparison and the evidence tier.

## What the DKM statement supports

The cited DKM Theorem 1.1 concerns non-adaptive generic discrete logarithm with advice and online queries. The repository's literature audit transcribes its success bound and summarizes the below-sqrt(N) consequence as an asymptotic time-space lower bound, S*T >= N, for that model. It does not give a finite-instance runtime comparison against rho, establish a concrete constant-factor ordering, or account for this implementation's measured costs. The PR's claim that the construction therefore “can never beat rho” was too strong and is removed from the current ledger wording. The exact measured result remains the evidence for this run: end-to-end cold G = 2.1919 [1.8584, 2.5893] above rT770 on the same points.

Source: Dinur, Keller, Marmor, [Non-Adaptive Cryptanalytic Time-Space Lower Bounds via a Shearer-like Inequality for Permutations](https://arxiv.org/abs/2505.00894), Theorem 1.1. The repository transcription and its stated model boundary are at `crypto/research/lit2026_w3_ggm_audit_20261011/README.md`, lines 78–85. Applicability of that model to this concrete quotient construction is a theoretical classification, not a finite-cost dominance proof.

## What the timing evidence supports

Run 39307634508 contains one cL220 and one rT770 primary observation per point for 40 points. Its four-block rank comparison and its separate A/A control are not repeated alternating cL220/rT770 primary pairs. The current Tier 1 speedup rule requires repeated alternating pairs and a paired 95% confidence interval with lower bound above 1. Therefore the archived result remains a valid one-run, instance-scoped reference timing record, but it is not a qualified Tier 1 speedup claim. The observed above-rho result is retained as measured; the statistical interval does not waive the repeated-pair requirement.

## Preserved record

The frozen run, protocol, source hashes, primary estimate, interval, controls, and reference-only status are unchanged. The n=83 IC baseline row and its measured values are unchanged. This note supplements the current ledger and the PR description; it does not rewrite the historical README or receipts.

Validation for this correction: exact current branch content before this note was `6ace5cb`, with main base `517073a`. Full archived receipt replay and local tests are recorded in the local review packet.

# Frozen protocol — rational 2-isogeny ECDLP transfer (2026-11-18)

**Status:** exploratory construction, not a prospective speedup claim. Known Vélu/2-descent baseline. [pcc:unverified]

## Hypothesis and falsification

Hypothesis H0: an explicit separable degree-2 isogeny transports a chosen odd prime-order ECDLP without changing group smoothness, and adds mapping cost unless a genuinely cheaper codomain DLP solver is independently demonstrated.

Reject a valid transfer if any of: point images off-curve, non-homomorphism on checked pairs, nontrivial intersection of the source prime-order subgroup with the kernel, wrong point orders, failed dual composition, failed subgroup inverse, or a recovered target log failing original-curve verification.

Reject a speedup claim unless **total** source-to-destination-to-verified-original solving cost falls below a matched source solver and the matched rho reference under the same accounting. Neither generic BSGS nor curve-coordinate changes count as new cryptanalysis.

## Frozen instance

* Field F_1009, curve E: y^2=x^3+11*x^2+13*x. Distinguished rational 2-torsion T=(0,0).
* Target E': y^2=x^3-22*x^2+69*x.
* Expect source and target cardinality 982=2*491, with subgroup H of prime order r=491. Expectations must be checked by independent exhaustive enumeration, not assumed.
* Map phi: O and T -> O; otherwise (x+11+13/x, y*(13/x^2-1)).
* Dual psi from E' via its 2-isogeny with coefficients a'=-22, b'=69, then (X,Y)->(X/4,Y/8). Check psi(phi(P))=[2]P for all P.
* Group generator: first lexicographically enumerated nonzero [2]R with [491]([2]R)=O.
* Target Q=[k]G; deterministic 64 unique k from random.Random(20261118).sample(range(1,491),64). BSGS with ceil(sqrt(491)).
* Use affine formulas. Record modular adds/subtracts, multiplies, squares, inversions, group calls, two point-map evaluations and inverse-map overhead separately; hash script, seed and all raw outputs.
* Correctness: enumerate all F_1009-rational points, count both groups; every map and dual composition; image cardinality and fibers; 491^2 ordered subgroup homomorphism pairs; every subgroup inverse; 64 planted logs and original-point verification.
* No GPU, native compiler, memory-normalized performance, benchrec record or independent signed PCC verdict in this small deterministic arithmetic check. Timing is not a claim.
* Reference rho expected steps: sqrt(pi*r/2); a heuristic, **not** a measured baseline. Explicitly separate counted group calls from field arithmetic.

## Literature / prior work / closure

* Classical 2-isogeny and its dual: Silverman, *The Arithmetic of Elliptic Curves*, X.4; exact normalized Vélu construction; existing local implementation `suite/src/isogeny/velu.rs`.
* Existing transfer-audit completeness obstruction: `problems/transfer-audit-completeness.md`; new work is a toy regression control, **not** a claim that efficient transfer is novel or that a weak isogenous curve exists.
* Closure review: `crypto/research/ic_mega_pass_20261031/{brief/BRIEF.md,report/REPORT.md}`, `crypto-autoresearcher/knowledge/leads/ecdlp/transfer/`; index-calculus mechanisms remain separate.
* Independent research-KB and Conductor APIs are not available in this automation's tool set. This is disclosed, not silently treated as a clear claim.

## Budget and negative controls

Pure Python standard library, p<=1009, at most 491^2 homomorphism pairs, 64 DLP inputs, no extrapolation to real curves. Include T -> O and O -> O; check dual([2]-composition), show smoothness cannot improve when rational isogenies preserve point cardinality.

# CT148 prospective-in-repository protocol: degree-13 Vélu DLP injectivity gate

Date: 2026-11-15 (America/Denver); root isogeny-labs/crypto#3877; extend existing cryptanalysis#1589 without changing its CT146/CT147 experiments or original q223 sources. Scientific standing: [pcc:unverified].

## Why

CT147 checks degree-two homomorphism and corrected-half equality, but these are NOT enough to establish that an isogeny preserves discrete logarithms on the source's declared cyclic subgroup. For a homomorphism gamma and source generator G of order n, the image determines x in Q=[x]G uniquely **if and only if** ord(gamma(G))=n, equivalently ker(gamma) intersect <G>={O}. For separable degree d, gcd(n,d)=1 is sufficient (not necessary). The same condition must be applied to each composed hop or to the composite map as a whole. If ord(gamma(G))=m<n, source scalars x and x+m have the same image; a target-only DLP does not recover x without extra source-side information, which must be priced.

## Exact finite instance and tests

Use F_229, E: y^2=x^3+x^2+x, #E(F_229)=208. Enumerate a cyclic rational order-13 kernel deterministically; construct the genuine degree-13 Vélu map as a sum of kernel translations including correct exceptional mapping of all kernel points to infinity. Recover the target coefficients from two independent mapped nonzero points, then check all 208 source points land on a single nonsingular target of cardinality 208; kernel must equal the declared 13-point subgroup. Check **every ordered source-point pair**, 208^2=43,264, for homomorphism. Inference of target coefficients from samples must never substitute for this exhaustive test.

Enumerate source cyclic subgroups. On the largest subgroup of order coprime to 13, solve every public known-answer DLP using independently implemented target BSGS and verify each scalar back on the source. On the largest 13-divisible subgroup, solve target DLP modulo its image-generator order, retain every full source scalar, count exact image collisions and require source verification to reject every ambiguous wrong scalar. Publish explicit two distinct source scalars with the same target image as the negative control.

The local exploratory implementation ran **before this repository protocol commit**. Therefore this is not a prospectively blinded scientific result or performance trial. This protocol still precedes the committed in-repository CT148 program. No timing speedup, original-prime result, new attack or novelty claim.

## Reproducibility, custody and limits

- Pure Python standard library; deterministic point ordering, bounded 208-point census, 43,264 pair checks, exhaustive declared-subgroup BSGS; no network, EKS, Spot, GPU or paid resource.
- Run normal and optimized Python with identical JSON; independent hosted source-only CI must check expected fields. Preserve failures rather than switching primes, kernels or generators after observing an outcome.
- This checker is written by the producer, not an independent verifier and has no signed PCC standing. Full original q223 rational maps, all 695/701 frozen records, C169/C13a/C13b/D, and strongest cold rho/BSGS/IC remain separate gates.

## Prior work and sources checked

- cryptanalysis #1533 (CT125), #1584 (CT145), #1589 (CT146/147); crypto #3877/#4215; crypto #4178 (GPU IC), cryptanalysis #1523 (original Jacobian setup). CT147 already proves the degree-two corrected-half identity; CT148 addresses **the different DLP-injectivity condition**.
- SageMath official isogeny documentation https://doc.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/ell_curve_isogeny.html (pointed morphisms, kernels, Vélu implementation); Silverman, *Arithmetic of Elliptic Curves* III.4.8 (homomorphism of pointed morphisms).
- Research-KB MCP, Conductor and repository-local lead-atlas commands are not exposed in this connector runtime; repo PRs/primary code and public documentation are the fallback. This is no claim of novelty.

## Exit conditions / next highest-value work

The finite 13-isogeny canary establishes the necessary subgroup-order guard and an explicit source-collision failure on a **toy** group. Wire the same order-of-image or exact-kernel-intersection test to the real q223 generator(s), every degree-13/169 hop and target/dual map, including exceptional classes; thereafter compare native unfiltered 695/701 original/reuse outputs. Only owner-approved native ABBA primitive timing followed by full single-target cold comparisons can support the requested cost advantage. [pcc:unverified]

# CT166 — geometric CM obstruction across every finite field extension

2026-11-16. [pcc:unverified]. The result is conditional on CT160's reported and source-only-censused group order being correct for the *actual fixed nu12 endpoints*, not an independently signed native map or a complete DLP attack.

## New stronger scope

Let k=F_223, K=F_(223^3), and let E'/K be either actual fixed-nu12 elliptic endpoint of CT160 with reported order 11,086,844. Let A=Res_(K/k)(E'), and let B/k be any abelian variety k-isogenous to A, including (if they exist geometrically with the asserted compatibility) the degree-eight CT163 quotient candidates.

**Conditional theorem:** For every elliptic E/k, Hom over the algebraic closure Hom_(bar{k})(E_(bar{k}), B_(bar{k}))=0. In particular, no finite extension of k can produce a nonzero **algebraic group homomorphism** from an F223-elliptic source into this exact k-isogeny class. This strengthens CT151's k-defined Frobenius obstruction and CT165's k-rational group obstruction along a distinct axis: the characteristic field is fixed but the map's field of definition can grow without limit.

**Scope qualification:** This does NOT exclude nonalgebraic/abstract group maps after extension, encodings without a homomorphism, other target Weil polynomials, or extension-field ECDLP for E'/K itself. It does NOT establish any cheaper complete prime-field solver.

## Mathematical certificate (independent of scanning extensions)

The target's K-Frobenius trace and discriminant are

    q=223^3=11,089,567
    T=q+1-11,086,844=2724
    D=T^2-4q=-36,938,092=-4*23*311*1291.

Complete trial division finds 23,311,1291 to be distinct primes. Since T is not divisible by 223, E' is ordinary; its geometric rational endomorphism algebra is the imaginary quadratic field

    End^0_(bar K)(E') = Q(sqrt(D)) = Q(sqrt(-9,234,523)).

Every elliptic E/F223 has trace t in [-29,29]. For t=0, E is supersingular, hence not geometrically isogenous to E'. Every t !=0 is ordinary, with

    End^0_(bar k)(E) = Q(sqrt(t^2 - 892)).

The negative integer t^2-892 has absolute value at most 892; its squarefree part therefore has absolute value at most 892. The target's squarefree radicand has magnitude **9,234,523**. Therefore the two imaginary quadratic fields cannot coincide for any of the 58 ordinary traces. A nonzero geometric homomorphism between elliptic curves is an isogeny and an isogeny identifies their rational endomorphism algebras. Hence Hom_(bar k)(E,E')=0 for every elliptic E/F223.

After extending the Weil restriction to bar k, it becomes the product of the three k-Frobenius-conjugate E' curves. These are all geometrically isogenous via Frobenius isogenies, and each has the target CM field. Thus Hom_(bar k)(E,A)=0. Composing with a quasi-inverse to the B~A isogeny yields Hom_(bar k)(E,B)=0.

**This result differs from CT161's k-simplicity.** A is geometrically nonsimple (it splits into elliptic factors), yet none of those geometric elliptic factors can be isogenous to a curve descended from F223.

## Reproducibility, directed controls and standing

The initial geometric CM factor observation preceded the CT166 protocol; the fixture-binding and dual-language replay protocol was then committed at d8da470d. Reproduction files:

- ct166_geometric_cm.py: exact Git-blob guard of immutable CT160 census, strict integer JSON parsing, trial-factor CM certificate, 59-trace classification and 9 negative controls.
- ct166_geometric_cm_independent.mjs: independently implemented Node square-divisor reduction, trial-factor check, 59-trace classification and bounded positive/negative controls.
- ct166-geometric-cm.yml: source-only GitHub Actions workflow, compares normal Python, optimized Python and Node canonical JSON; records SHA-256 and nine mutation checks.
- CT166_GEOMETRIC_CM_PROTOCOL.md: claim scope, source preconditions and declared acceptance criteria.

Positive boundary: hypothetical genuine cubic base change of an ordinary F223 curve with trace t=4 has trace T3=-2612 and squarefree CM radicand -219 in both descriptions. This shows that the rejection condition does not simply reject every possible cubic base change.

The original CT160 census, fixed generators, CT163/164 kernels, the frozen 695/701 native records, mathematical ledger, and execution-admission policy were not modified. Python/Node are producer-authored checkers and require independent hosted replay; even passing source-only CI does not certify original Rust/native geometric construction or signed scientific PCC. [pcc:unverified]

## Source and prior work examined

- CT150, CT151, CT160, CT161, CT163, CT164, CT165 on cryptanalysis PR #1589, plus root crypto PR #3877; concurrent explicit genus-three work crypto #4357 (not duplicated).
- MIT 18.783 Lecture 13, Theorem 13.6, which identifies rational endomorphism algebras with discriminant t²-4q for ordinary elliptic curves: https://math.mit.edu/classes/18.783/2021/LectureNotes13.pdf
- Ordinary/supersingular geometric endomorphism classification, Springer J. Cryptology (2020): https://link.springer.com/article/10.1007/s00145-019-09316-0
- Weil restriction base-change construction (standard descent/functor of points): https://en.wikipedia.org/wiki/Weil_restriction

The shared KB interface and Conductor reservation were not loaded in this connector runtime, so no originality or no-prior-art claim is made. [pcc:unverified]

## Next discriminator under owner's performance priority

Do not spend on a new genus-three model that purports to make *this fixed-nu12* isogeny class into an algebraic prime-field ECDLP target; a new class with matching source CM is necessary for an algebraic route. The concrete native performance task remains independently replaying all 695/701 actual original/reuse Jacobian records (not only the published 48 selected vectors), then owner-admitted paired same-host C169/C13a/C13b/D and a complete cold public-target comparison with matched optimized rho, BSGS and IC. Count all setup, transport, half/correction, matrix solve, verification, RSS and uncertainty. Record losses; never claim candidate/baseline ratio>1 without independently reproduced full solves and signed PCC.

**Performance status:** unpriced, no whole-corpus replay in this CT166 continuation, no complete prime-field ECDLP advantage established, no paid EKS/Spot/GPU compute or protected merge. [pcc:unverified]

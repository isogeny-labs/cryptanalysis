# Actual degree-13 source isogeny and a different product

Frozen before implementation, 2026-11-13. This is bounded native correctness
development. It admits no benchmark or computational advantage claim.
[pcc:unverified]

The current explicit Jacobian routes pass through A=Res(E), where
K=F223[z]/(z^3-3) and the original short source has
a=(214,144,205), b=(137,218,9), order11092292 and ell2773073.
The original quadratic source and all five public targets retain their
existing field/model tags. The old short-coordinate shift is (191,93,215).
Repeated routes through this SAME A collapse as recorded in2e21d5. The next
question is whether an actual odd source isogeny gives an explicitly
different elliptic product and then further prime-field Jacobian maps.
[pcc:unverified]

## Prediction and source review

The original order gives qK=223^3 and trace-2724. Modulo13, the expected
Frobenius eigenvalues are2 and4. There are no rational nonzero13-torsion
points over K. A point-based generator construction would require larger
extensions than the original fixed-degree FpR representation supports.
Instead use its actual kernel polynomial over K. These are predictions to
check, not evidence of an implemented isogeny. [pcc:unverified]

Read original isogeny_algos/src/find/divpoly.rs, kernel/kohel.rs,
find/sea.rs, poly.rs, curve.rs and field.rs at the original pinned producer
3d49af7f3d0a28e76b79e4825c9d2324e85853d2, and compare current source bytes.
The original division-polynomial convention is g_n=psi_n for odd n,
g_n=psi_n/(2y) for even n. Kohel returns normalized rational x=N/D and
y'=y*(N'D-ND')/D^2. The existing function check_x_identity uses finitely
many random evaluations; it is not an exact polynomial-identity check.
This phase adds a whole-coefficient check without changing that engine.
[pcc:unverified]

The shared KB tools are absent; two actual wrapper searches for degree13
and negative odd-source routes exit127. Preserve commands and logs under
odd-source-review-01 and use original source directly. The lead atlas and
lab contract in vault8edec422 remain inaccessible; do not unlock or edit.
No novelty or absence inference is made. Kohel/SEA/division-polynomial
machinery is existing classical mathematics. [pcc:unverified]

## Frozen construction and controls

1. Construct the original checked instance and field. Confirm source
   smoothness, exact ell generator/order certificate, order modulo13 and
   both predicted eigenvalues in Rust.
2. Compute the entire degree84 psi13 and squarefreeness. Iterate the qK
   Frobenius polynomial six times; avoid forming qK^6 in u128. Predict
   gcd(psi13,x^(qK^3)-x) degree6 and the sixth-power gcd degree12.
   Their exact quotient h2 has degree6 and should have eigenvalue2 in
   the original SEA quotient-ring checker. Retain both gcds and all steps.
3. Use the original Kohel engine to construct gamma:E→Eprime of degree13.
   Require smooth target, gcd(N,D)=1 and degrees13/12. Check the FULL
   coefficient identity S*(N'D-ND')^2=N^3*D+aPrime*N*D^3+bPrime*D^4,
   S=x^3+a*x+b. A deliberately wrong target coefficient must fail this
   exact identity. All coefficients and whole residuals are retained.
4. On Eprime repeat psi13/Frobenius. Its third-power gcd should be the
   degree6 normalized dual kernel with eigenvalue4. Original Kohel gives
   normalized dual codomain aDouble=13^4*a,bDouble=13^6*b. Divide output
   x by13^2 and y by13^3 to obtain the actual dual Eprime→E. Validate the
   normalized identity and the full scaling equations. Retain failures.
5. Compare BOTH rational compositions to multiplication[13] by full
   polynomial cross-products. For odd13 use raw, unnormalized division
   polynomials: x13=(x*g13^2-4*S*g12*g14)/g13^2. Preserve leading13 in
   g13. Compose by homogeneous polynomial substitution. Retain every
   numerator/denominator and zero residual. Point checks alone do not
   replace these global identities. The normalized differential gives
   the y relation y13=y*x13'/13; verify its polynomial identity too.
6. Check both[13] compositions on at least32 source points (eight fixed
   odd scalars times all four actual cofactor points) and32 deterministic
   target points, including infinity. Check homomorphism pairs, every
   actual rational2-torsion point, target/source membership, nonzero exact
   ell image, all five unchanged public targets and independent source
   known-answer scalar relations outside map inputs. No DLP oracle,
   hidden scalar, fitted translation or private instance mutation.
7. Retain full fresh source/target equation/map/kernel IDs and both
   p223-Frobenius j-conjugate sets. Do not assume disjointness. If they
   meet, retain this negative or inconclusive product discriminator and
   choose the next route using the recorded outcome. If disjoint, the
   principally polarized elliptic products differ; written geometric
   interpretation and faithful feasible Lean lemmas remain required.

## Limits, evidence and continuation

Use Rust with the original field/polynomial/elliptic engines as ordinary
dependencies. Add one unfiltered comprehensive test. Each first failure
keeps its exact source and whole capture before a versioned correction.
Use a separate source snapshot, all selected before/after hashes, complete
stdout/stderr, toolchain, commands, seed and phase exit files. Compilation
and test each have900-second bounds; native test is serial with2GiB address
space. Reusing an existing outside compiler cache is labeled warm and is
not a cold benchmark. No paid compute or broad parameter sweep is admitted.
[pcc:unverified]

Success for THIS phase requires actual smooth curves, both exact map and
composition identities, nonzero odd-subgroup transport and every stated
control. It does not construct a new Jacobian. After success, freeze a
separate target-gluing protocol: use fresh typed Eprime/P0/Picard identities,
retain all HLP signs and singular/nonsquare/duplicate outcomes, and build
PhiPrime/NormPrime. Only then test
F=PhiPrime*Res(gamma)*Nold and reverse
G=PhiOld*Res(dual gamma)*NormPrime, expected both[52] and degree140608.
These last maps and numbers are proposals. Full measurement admission,
complete transport cost and strongest ECDLP references remain open.
[pcc:unverified]

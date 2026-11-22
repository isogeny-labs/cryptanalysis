# Attempt and dependency log

## Preserved unsuccessful checks

1. `python -m pytest -q tests/test_nist_333.py` failed because `pytest` is not [pcc:unverified]
   installed. The suite was converted to dependency-free `unittest`; this was
   an infrastructure failure, not mathematical evidence.
2. `command -v sage`, `command -v magma`, and `command -v gp` returned no
   executable. Debian 13's configured package sources expose no `sagemath`
   candidate.
3. The arXiv e-print archive for `2012.07173` was downloaded and inspected. It
   contains `Cover_attack.tex`, `Cover_attack.bbl`, and `llncs.cls`; it contains
   no implementation or machine-readable example.
4. Bounded GitHub repository and grep.app searches for the exact paper title,
   `normal Weil set`, `(3,3,3)-isogeny`, and genus-three theta reconstruction
   returned no reusable implementation. This is not a universal code-absence
   claim.
5. `galois` 0.4.11 independently confirmed that the P-224 quadratic torsion
   polynomial is irreducible. Creating the full 448-bit extension then stalled
   in the library's primitive-element search (factoring/processing the enormous
   multiplicative-group order) and was interrupted after more than 90 seconds.
   The primary exact field implementation does not require a primitive element
   and completes both curves in about eight seconds.
6. The public Magma calculator endpoint returned HTTP 401, so the generated
   `handoff/nist_333_kernel_input.m` could not be syntax-checked remotely.
7. A final connected-Drive search for `normal Weil set`, `Aronhold theta genus
   3`, `Dixmier Ohno quartic reconstruction`, `Tian333`, `lllisogeny`, and
   `Weber Riemann theta quartic` found the Tian paper and adjacent Kani/Weil
   research, but no executable genus-three reconstruction code.
8. A renewed 2026-11-19 GitHub repository/API and grep.app search for `normal
   Weil set`, the exact paper title, `Tian333`, `lllisogeny`, Aronhold/Weber
   reconstruction, and genus-three theta-quartic code found no reusable Tian
   implementation.  The only `IsogenyFromKernel` hits were unrelated
   genus-two/SIKE reference code.  This is a bounded public-code result, not a
   universal absence claim.
9. A later repository search found the maintained
   `JRSijsling/quartic` Magma package.  It does not implement Tian's normal
   Weil-set isogeny, but it supplies the independent Dixmier–Ohno, smoothness,
   reconstruction, and isomorphism checks needed after a candidate quartic is
   produced.  The package is bundled with Magma 2.29.
10. The public Magma calculator, which had previously returned HTTP 401,
    later accepted anonymous jobs.  The historical 401 is retained above as
    the earlier infrastructure result; it is no longer the active blocker.
11. The Python finite-field reconstruction produced a nonsingular P-224
    candidate with exact `28/36` theta pattern and seven bitangents.  Magma
    refuted its Frobenius-rational moduli claim.  The same implementation was
    run on Tian's published `q=523` example; its candidate is not geometrically
    isomorphic to the published quartic.  Both candidates are quarantined.
12. The elliptic level-2 Weil-function square-root constants displayed in
    Tian's paper were implemented exactly over `F_(523^18)` and the control was
    repeated.  The `28/36` pattern remained valid, but both the published-curve
    and Frobenius-moduli comparisons remained false.  Omission of those
    constants is therefore ruled out as the active defect.
13. Two exact convention controls narrowed the defect further.  The
    constant-free and displayed-constant candidates have equal moduli, so the
    quotient normalization absorbs those scalings.  In contrast, exchanging
    `Q1` and `Q2` in each symplectic pair changes the candidate's moduli even
    though it only relabels the same quotient.  Using the transposed `d_2`
    refinement does not repair the Tian or Frobenius controls.  The remaining
    defect is therefore in level-2 theta marking/normalization or its Weber
    interpretation, not in the elliptic constants or orientation alone.
14. The relabeling comparison was then performed before Weber reconstruction.
    All 64 raw `h(0)` values and all 64 squared normalized theta values match
    exactly under the top/bottom characteristic permutation.  Hence the
    normalization is basis-consistent at the squared-null level; the remaining
    defect is the coherent sign/metaplectic lift into Weber's signed products.
15. All `2^6` sign choices for the six nontrivial Aronhold coefficients were
    tested against Tian's published `q=523` curve.  Exactly one matched:
    mask `48`, which flips `alpha_32` and `alpha_33`.  This closes the source
    control and shows that the two minus signs printed in the 2020 preprint
    are incompatible with its published example under the implemented reduced
    characteristic convention.
16. The corrected P-224 candidate has Frobenius-rational moduli.  Direct
    invariant-to-quartic reconstruction exceeded the public Magma service's
    memory limit, so it was replaced by a lower-memory Galois descent.  The
    unique Frobenius isomorphism satisfies the degree-three cocycle, matrix
    Hilbert 90 produces `B^sigma*M=B`, and substitution by `B^-1` yields the
    nonsingular `F_p` quartic in `artifacts/p224_descended_quartic.json`.
17. P-256 now completes the finite-field theta reconstruction. Its 2-division
    polynomial splits in the existing cubic subfield; the exact run has 28
    odd zeros, 36 nonzero even theta values, and seven verified Aronhold
    bitangents. The resulting 15-term quartic has all quadratic-extension
    components zero and is defined over `F_(p^3)`, but not in the displayed
    coordinates over `F_p`.
18. The P-256 Frobenius-descent input was generated, but no local Magma or Sage
    executable is installed. On 2026-11-19 the public calculator returned HTTP
    401 and the connected browser surface could not be initialized. This is a
    computational validation obstruction, not evidence that descent fails.
19. The P-256 theta-characteristic Frobenius action was computed exactly. The
    28 odd characteristics decompose as one fixed point and nine 3-cycles.
    Only one of the seven reconstructed Aronhold lines maps back into that
    selected system; the other six require equations for the remaining 21
    bitangents. This rules out the simple seven-line descent shortcut without
    ruling out descent itself.

## Reconstruction work that remains

Tian's published construction requires all of the following beyond the kernel
input now present in `artifacts/evidence.json`; current status is shown inline:

1. normal Weil functions on `E^3[3]` and the invariant theta section —
   implemented; all 729 restricted-kernel identities pass;
2. the 64 normalized two-torsion theta values — implemented; all 4,096 normal
   multiplication identities and the `28/36` vanishing pattern pass;
3. Weber/Riemann/Aronhold plane-quartic reconstruction — implemented; the
   corrected reduced-characteristic signs pass Tian's published control;
4. direct Frobenius/Hilbert-90 descent back to `F_p` — implemented and
   externally validated for P-224;
5. image recovery using the eight low-degree symmetric functions;
6. Gröbner recovery and formal-point interpolation of the homomorphism;
7. exceptional-point, homomorphism, kernel, and polarized-dual verification.

The present artifacts now supply the accepted P-224 finite-field quartic,
exact normalization audits, and descent certificate.  The active construction
blocker is the source-to-Jacobian point map and its composition verification.

Because this specialization starts from `E^3`, the eventual reconstruction must
also test whether the induced principal polarization is indecomposable; the
coordinate-factor transversality checks alone do not settle that repeated-factor
question.

## Repeated-product progress after the initial handoff

1. All 13 scalar diagonal elliptic subgroups `E_v[3]`, indexed by
   `P^2(F_3)`, are now tested for every admissible rational kernel.  Among the
   768 P-224 kernels the incidence histogram is `0:192, 1:240, 2:288, 4:48`.
   An explicit zero-incidence P-224 alternate is exported.  All 12 P-256
   kernels have four scalar-diagonal incidences.
2. A quotient period matrix was derived for graph kernels:
   `Omega'=3*tau*(I+tau*S)^(-1)`.  At three independent complex periods, both
   the shared kernel and the P-224 alternate have all 36 even theta constants
   nonzero; odd theta constants cancel below `3e-16` and cutoff changes stay
   below `5e-16` in the recorded run.
3. This numerical result shows that repeated `E^3` with these kernel types is
   not generically forced to decompose or be hyperelliptic.  It is not a proof
   for the NIST finite-field fibers.  Elliptic subvarieties involving
   non-scalar elements of `End(E)`, the finite-field theta nulls, descent, and
   the Serre obstruction remain open.

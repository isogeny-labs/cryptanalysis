# Attempts and boundaries

## Completed

- Enumerated all 105 perfect matchings of eight Weierstrass points.
- Reproduced Smith's complete table of Frobenius-stable matchings for every
  factorization partition of degree eight.
- Independently recomputed the modeled random-curve success proportion as
  0.1857381419453889.
- Verified the published positive-control polynomial over `F_37` has [pcc:unverified]
  homogeneous factorization type `(6,1,1)` and one tractable rational kernel.
- Added an odd-order subgroup preservation and dual-recovery certificate.
- Added the exact cover retraction `f_* f^*=[d]` and its compositions with
  polarized `(2,2,2)` and `(3,3,3)` isogenies.  This reduces DLPs in the
  transported elliptic subgroup back to the original ECDLP, but does not apply
  to arbitrary Prym/Jacobian classes.

## Not completed, with reason

- No user-specific cover was screened because no genus-3 hyperelliptic
  equation or cover/descent map was supplied.
- No executable Smith isogeny constructor is included.  The primary paper
  provides the construction and an explicit example, but this environment did
  not contain a ready Sage/Magma implementation to validate independently.
- No end-to-end DLP run was attempted.  The result is a published asymptotic
  transfer, not a performance measurement or a cryptographic key-recovery
  claim.
- A same-field cover of a NIST prime-field curve does not make the original
  ECDLP easier: plane-quartic `soft-O(p)` is slower than elliptic Pollard rho
  `O(p^(1/2))`.  The dramatic comparison needs a descent representation over a
  substantially smaller field.

# Actual q223 geometric two-torsion and a second nondual Jacobian map

- **Status:** open
- **Kind:** implementation gap and partial formalization
- **Affected work:** Chained ECDLP Transfers, crypto PR3877 and cryptanalysis
  PR1523; [two-primary derivation](../experiments/chained-transfer-public-target/two-primary/DERIVATION-01.md)
- **Next action owner:** current research session / next resuming session
- **Last updated:** 2026-11-13

## Problem

The actual prime-field genus3 Jacobian has no second implemented nondual
isogeny in this continuation: its geometric two-torsion coordinates,
Frobenius action and suitable kernel/codomain construction remain missing.

The exact fixed case is N4 q223/seed1, K=F223[z]/(z³−3), ell2773073,
order11092292. The completed Phi/Norm pair has both compositions[2]. Going
back through the same dual pair is insufficient to establish a useful new
chain or computational advantage. [pcc:unverified]

## Evidence and uncertainty

- **Observed:** native02/510d03 uses original arithmetic and all224 rational
  C point classes, four cofactor classes, all16 sums and64 associative triples.
  Rational Jacobian2-Sylow is C4; source E(K)[2] is C2×C2. Both rational map
  kernels/images have size2, and both compositions pass. All2318 selected
  source hashes remain unchanged. Partial-capture01 is retained in1311d9.
  [pcc:unverified]
- **Derived:** written65f7a4 combines this fixed-point count with the Ciani
  Weil polynomial to derive full geometric J[2] splitting degree6. All four
  faithful partial algebra declarations pass both original Lean gates and
  exact local PCC bindings. Actual geometric/Tate/CH/orbit/field bridges are
  written and remain open in Lean. [pcc:unverified]
- **Missing capability:** the reviewed original plane-quartic Picard engine
  handles admitted prime fields; it has no established F223^6 group interface
  in the checked source catalogc3b30d. Genus-two Richelot and hyperelliptic
  arithmetic do not automatically support this smooth plane quartic.
  [pcc:unverified]
- **Unknown:** actual geometric Frobenius matrix, stable maximal-isotropic
  kernels, explicit nondual codomains, and their total solving cost. The
  characteristic polynomial alone does not justify a semisimple order-three
  action or a stable-kernel count. [pcc:unverified]
- **Limits:** a full torsion field of degree6 does not exclude an F223-rational
  isogeny. Its kernel need only be Frobenius-stable. Missing KB tools and the
  encrypted atlas give no absence or novelty evidence. [pcc:unverified]

## What would unblock it

- [ ] Construct actual geometric J[2] coordinates and Frobenius action over
  the required extension, or an explicit equivalent coordinate kernel descent;
  retain independent field, curve/divisor, torsion and descent checks.
- [ ] Select an actual Frobenius-stable maximal-isotropic kernel distinct
  from the original dual backtrack; compute its codomain and explicit map.
- [ ] Prove the homomorphism and nonzero prime-ell transport, independently [pcc:unverified]
  replay maps/compositions, and complete feasible faithful Lean obligations.

These conditions establish an executable second transfer. A computational
advantage still requires original benchmark admission, complete arithmetic
accounting and matched strongest ECDLP references. [pcc:unverified]

## Next discriminating step

Inspect the original Ciani coordinates, finite-extension arithmetic and
bitangent/divisor machinery. Derive an actual coordinate construction over
F223^6 before writing a kernel census. A first implementation should retain
all28 geometric bitangents or a full rank-six torsion basis, with tangent or
torsion equations and Frobenius closure checked by original field arithmetic.
This is a bounded local correctness development, not an admitted benchmark.
If the chosen API cannot represent the extension or divisor model, preserve
that implementation gap and continue through an explicit extension or
coordinate-descent implementation. A bounded failure does not prove that no
map exists. [pcc:unverified]

## Resolution and history

2026-11-13: native510d03, written65f7a4, exact partial bindings
4e7bfe/cc7273/abcfec/5facfe; two-page reportce9a6d. Unresolved.
[pcc:unverified]

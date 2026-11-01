# H110 paired reference harness — canonical p²-lift defect

Status: **independent replay complete; scoped null confirmed** (2026-11-01).

This directory independently checks
[crypto#3111](https://github.com/isogeny-labs/crypto/pull/3111).
The verifier is standard-library-only and does not import the canonical runner.

It independently recomputed:

- all Hensel, affine, mixed-projective, and formal-coordinate arithmetic for
  9,096 canonical targets;
- all 28 complete finite-difference degrees;
- all 32 random-section/permutation controls;
- both coordinate-isomorphic control words;
- every torsion correction, each of which produced `tau=0`.

Every candidate and control word had maximum possible degree. Zero rows passed
the frozen degree gate.

Run:

```sh
python verify.py results/p2-lift-defect-cocycle.json.gz
```

This confirms only the scoped null for the frozen coordinate-section
scalar-polynomial bridge. It is not a generic lower bound.

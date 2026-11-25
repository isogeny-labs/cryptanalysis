# Target-dependent relations and the one-orbit CM gate

## The point relation already has prior art

[Amadori, Pintore, and Sala, *On the Discrete Logarithm Problem for
Prime-Field Elliptic Curves*, §3](https://eprint.iacr.org/2017/609.pdf)
build factor-base points with known expressions `[a_i]G+[b_i]Q`.
A verified signed zero sum among such points gives

```text
[A]G + [B]Q = O,       A = sum(sign_i*a_i), B = sum(sign_i*b_i).
```

For `Q=[d]G` and `B != 0 mod r`, this contains the unknown scalar:
`A+B*d=0 mod r`. Thus a *generic* point-dependent relation is known;
the gap in this PR is a relation whose yield or solving cost improves
because of the smooth horizontal structure. The cited paper explicitly
leaves its polynomial-system solve cost unestimated and makes no claim
of beating rho. An x-coordinate summation-polynomial root is not by
itself the signed group relation above; signs and the point sum must
be checked. [pcc:unverified]

## Why one known-scalar orbit loses the target

Let a horizontal principal loop act as the known unit `lambda mod r`
on the prime-order rational group. Take one nonzero seed
`H=[a]G+[b]Q` and any finite signed collection of its orbit points
`[lambda^j]H`. Its group sum is `[C]H`, where
`C=sum(sign_j*lambda^j) mod r`. Because `H` has order `r`, the sum
is zero exactly when `C=0 mod r`. This condition is determined by
the selected exponents and signs; it does not depend on `d`.
Expanding the resulting relation gives `A=a*C=0` and `B=b*C=0`,
so it cannot yield a nondegenerate equation for `d`. [pcc:unverified]

If `H=O` instead, the defining equation `a+b*d=0 mod r` already
contains the sought scalar when `b` is a unit. Finding such a seed
is the original point collision, not an orbit relation advantage.
The one-seed conclusion applies to *known-scalar orbit points on one
rational group*. It does not rule out bases using distinct seed
coefficient vectors, non-linear coordinate selection, or relations
on an auxiliary variety. [pcc:unverified]

The finite `D=-19` control makes the distinction visible. On
`E/F_47: y^2=x^3+x+38`, `r=61`, `G=(2,1)`, and `Q=[3]G=(32,19)`.
The smooth endomorphism `1+pi` acts as `[2]` on rational points,
so `G+[2]G-Q=O`. The signed relation contains `d=3`, but the
same relation is obtained with ordinary doubling; this control
does not attribute any saving to the CM map. Sage checked the curve
order, generator order, target coordinates, and point identity.
[pcc:unverified]

## What remains to price

Within the orbit-built family, a nontrivial signed zero sum needs
at least two seed coefficient vectors that are not proportional,
unless one seed is already zero. Such a construction would need to
count **informative** relations after discarding within-orbit
identities, certify the signed witnesses, and charge base generation,
failed searches, and solver work against a matched known-scalar
orbit and same-target rho. The two-summand arc screen in the
[CM orbit hypothesis](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/ledger/hypotheses/H-CMFB-7d4e1a.yaml)
has a BSGS-equivalent search model; it explicitly does not test
target-dependent or higher-arity orbit bases. This note supplies no
cost claim for those untested cases. [pcc:unverified]

## Formal proof map

[`formal/OrbitGate.lean`](formal/OrbitGate.lean) imports the
repository's minimal additive-group model
`research/base-point-independence-20261108/formal/BasePointIndependence/Core.lean`
(SHA-256 `09ec555b36dd89631e30d983ef02d16ad953dd394fbd27e69f1bfd4652fb231d`).
`orbitSum_eq` consolidates any finite unsigned orbit sum;
`seedOrbitSum` expands one seed into its `G,Q` coefficients;
`signed_orbit_coeff` handles arbitrary positive and negative lists;
and `signed_seed_coeff` proves that both public coefficient totals
agree modulo `r` when the seed has exact order `r`. No theorem assumes
the desired zero coefficients. The signed statement is faithful to
the group-algebra part of the argument. [pcc:unverified]

The pinned Lean 4 toolchain is `v4.34.1`. From the repository root,
compile the imported Core to a local, uncommitted `.olean`, then check
the new module:

```sh
mkdir -p research/cm_joint_s4_20261123/formal/BasePointIndependence
lean -o research/cm_joint_s4_20261123/formal/BasePointIndependence/Core.olean research/base-point-independence-20261108/formal/BasePointIndependence/Core.lean
LEAN_PATH="$PWD/research/cm_joint_s4_20261123/formal" lean -t 0 research/cm_joint_s4_20261123/formal/OrbitGate.lean
```

The producer run passed and `#print axioms` reported only Lean's
standard `propext` for the four declarations. `lean4checker` was not
available. The formal module assumes exact seed order and a known
scalar action; it does not formalize the specific elliptic curve,
horizontal map, or the cost of finding a signed relation. Independent
PCC verification of the research claim remains open. [pcc:unverified]

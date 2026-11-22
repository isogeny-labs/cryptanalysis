# Checkable small-prime controls for the Xedni rank-decay panel

Status: deterministic control implementation only. It does not generate a
natural lift over `Q`, compute a Mordell--Weil rank, or satisfy the blocked
checkpoint gate. All control outputs remain producer assertions pending
independent PCC standing. [pcc:unverified]

## Arms

`local_conditions.py` implements the exact local arms needed to reproduce and
separate the 2000 paper's reverse-Mestre experiment:

- `A_none`: no CRT prime and `M=1`.
- `B_reverse_mestre`: for every admitted prime `l`, require
  `#E(F_l) = l + 1 - floor(2 sqrt(l))`.
- `B_reverse_mestre_plus1` and `B_reverse_mestre_plus2`: the paper's two
  explicitly named weaker conditions.
- `P_neutral_crt`: impose the same CRT machinery but require the neutral trace
  `#E(F_l)=l+1`, which is distance zero from the frozen “nearest to `l+1`”
  target. This is the same-modulus placebo missing from the historical A/B/C
  comparison.
- `I_incompatible`: start from the exact B system and deliberately change one
  point image in the first nontrivial common quotient. This is a known-negative
  control, and both the top-level record and its compatibility record set
  `primary_estimand_eligible=false`.

[pcc:unverified]

The fixed prime pool is every prime from 7 through 97 inclusive. `P` and `I`
inherit B's admissible-prime schedule, so B/P/I use the same prime prefix and
CRT modulus for a given `r` and product target. A prime with fewer than `r`
usable affine points is retained as an explicit rejection. There is one
additional exact rejection: when `r=6` and the selected group order is seven,
all six affine points form three inverse pairs and their seven-column
Weierstrass incidence rank is at most five. `target_product` selects the
smallest remaining increasing prime prefix whose product reaches the requested
budget; failure to reach it through 97 is fatal. [pcc:unverified]

Only `r=2..6` is executable. Every `r>=7` request fails closed because the
frozen protocol does not yet have a certified general-cubic-to-Jacobian map for
all selected points. A ten-column local cubic rank is not used as a surrogate
for that missing bridge. [pcc:unverified]

## Construction and certificates

For each admitted prime, the constructor deterministically searches short
Weierstrass curves `y^2=x^3+ax+b`. Every attempted `(a,b)` records its
discriminant core, point count when nonsingular, and rejection reason. An
accepted curve must be nonsingular, have the exact requested point count, and
have a certified cyclic generator. [pcc:unverified]

One shared integer scalar vector constructs all local point tuples from their
certified generators. Each tuple must consist of `r` distinct affine points.
The required incidence test is exactly the paper's seven-column Weierstrass
row

```text
(Y^2 Z, X Y Z, Y Z^2, X^3, X^2 Z, X Z^2, Z^3).
```

It must have row rank `r`; the ten-column general-cubic rank is recorded only
as a diagnostic. The checker also verifies that each seven-column row kills
the recorded short-Weierstrass coefficient vector. Rejected scalar vectors and
their first failing prime/rank are retained. [pcc:unverified]

This cyclic/shared-scalar restriction supplies a checkable sufficient version
of the cross-prime compatibility warning in Section 3.2 of Jacobson, Koblitz,
Silverman, Stein, and Teske. For every pair of local groups and every divisor
`tau > 1` of the gcd of their orders, the image of point `i` in
`E(F_l)/tau E(F_l)` is represented by the same shared scalar modulo `tau`.
The JSON records all such divisors and residues. The checker recomputes every
curve, deterministic search attempt, generator, point, incidence rank, modulus
product, and quotient image from the primary fields. [pcc:unverified]

For `I_incompatible`, the constructor first makes the same compatible cyclic
system as B. It then searches deterministic one-point mutations on the right
side of the first pair having a common quotient, preserving affineness,
distinctness, curve membership, and seven-column rank. The record gives the
pair, quotient order `tau`, point index, old/new scalar residues, unequal
quotient images, the complete list of cyclic-quotient isomorphism units (which
must be empty), and every rejected mutation. The checker reconstructs the
mutation and requires that no unit multiplication maps the whole labelled left
tuple to the right tuple; changing only a status label is rejected. If every
admitted local order is pairwise coprime, construction fails instead of
claiming an incompatibility that was never exercised.
[pcc:unverified]

Full common-quotient construction for arbitrary noncyclic finite elliptic-curve
groups is **not implemented**. The implemented certificate is the exact but
more restrictive cyclic case: chosen generators identify
`E(F_l)/tau E(F_l)` with `Z/tau Z`, and the public scalar labels provide the
images. The constructor rejects noncyclic groups, does not guess an isomorphism
between unrelated quotients, and does not label a capped search compatible.
This can exclude valid local systems; it cannot silently admit an unsupported
one. [pcc:unverified]

## Commands

Run the deterministic controls:

```sh
python3 -m unittest research/xedni_rank_decay_20261118/test_local_conditions.py
```

Build and recheck a saved small historical-style control:

```sh
python3 research/xedni_rank_decay_20261118/local_conditions.py build \
  --arm B_reverse_mestre --r 2 --primes 7,11 \
  --seed xedni-rank-decay-local-v1 --output /tmp/local.json
python3 research/xedni_rank_decay_20261118/local_conditions.py check /tmp/local.json
```

Build the amendment's incompatible known-negative (never a primary row):

```sh
python3 research/xedni_rank_decay_20261118/local_conditions.py build \
  --arm I_incompatible --r 2 --primes 7,11 \
  --seed xedni-rank-decay-local-v1 --output /tmp/incompatible.json
```

The output's status is `control_only_no_natural_rank_rows`. Producing these
finite-field controls does not discharge the requested rank panel or authorize
bypassing its checkpoint requirement. [pcc:unverified]

## Source

Jacobson, Koblitz, Silverman, Stein, and Teske, “Analysis of the Xedni Calculus
Attack,” *Designs, Codes and Cryptography* 20 (2000), Sections 3.2 and 5.4,
DOI `10.1023/A:1008312401197`. Section 3.2 defines the exact and `+1`/`+2`
reverse-Mestre counts, the incidence-rank condition, and the common-quotient
compatibility issue. Section 5.4 defines historical arms A, B, and C.
[pcc:unverified]

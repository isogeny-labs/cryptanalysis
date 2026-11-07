# Independent algebra review: J1

Task: `TASK-20261028-32bc7d`  
Joint owned: `J1` only  
Verdict: **holds**, for the four universal polynomial identities below.

The only supplied mathematical input was `blind-input/brief.md`, whose SHA256
was verified as
`754c5ee3187316fff1a8efb9e39ad3d9cdcd1b1291ab771c02cb682e4a5323d3`.
The derivations are independent ring calculations. No repository, producer
proof, sibling report, review plan, memory, or external source was consulted.
This verdict does not certify any producer implementation or any other joint.
The unconditional cancellation and division extensions are false as specified
below; they are not consequences included in the identity verdict.

## Identities and derivations

Let K be a commutative ring and a, b, c be arbitrary elements. Write

    s1 = a + b - c
    s2 = a^2 + b^2 - c^2
    s3 = a^3 + b^3 - c^3
    D  = (a - c)(b - c).

Integer coefficients mean repeated addition in K. Every step below uses
associativity, commutativity, distributivity, and additive inverses; it uses
neither division nor cancellation of a multiplicative factor.

**1. The first expression is 2a.**

    (a + b) - (b + c) + (c + a)
      = a + b - b - c + c + a
      = a + a
      = 2a.

**2. The second expression is 2D.**

    s1^2 - s2
      = (a + b - c)^2 - (a^2 + b^2 - c^2)
      = a^2 + b^2 + c^2 + 2ab - 2ac - 2bc
        - a^2 - b^2 + c^2
      = 2(ab - ac - bc + c^2)
      = 2(a - c)(b - c)
      = 2D.

**3. The third expression is 6cD.**

For a compact independent expansion, set u = a + b and v = ab. Direct
binomial expansion gives

    s1 = u - c
    s2 = u^2 - 2v - c^2
    s3 = u^3 - 3uv - c^3.

These are polynomial rewrites; in particular, the expression for s3 does not
divide by 3. Therefore

    -s1^3 + 3s1*s2 - 2s3
      = -(u - c)^3
        + 3(u - c)(u^2 - 2v - c^2)
        - 2(u^3 - 3uv - c^3)
      = (-u^3 + 3u^2*c - 3u*c^2 + c^3)
        + (3u^3 - 6uv - 3u*c^2 - 3u^2*c + 6vc + 3c^3)
        + (-2u^3 + 6uv + 2c^3)
      = 6vc - 6u*c^2 + 6c^3
      = 6c(v - uc + c^2)
      = 6c(ab - ac - bc + c^2)
      = 6c(a - c)(b - c)
      = 6cD.

**4. The fourth expression is 2ab.**

Substituting the established second identity,

    s1^2 - s2 + 2c*s1
      = 2(ab - ac - bc + c^2) + 2c(a + b - c)
      = 2ab - 2ac - 2bc + 2c^2 + 2ac + 2bc - 2c^2
      = 2ab.

## Exceptional rings for the identities

No exclusion is needed for any of the four identities. They are identities
over the integers, hence remain valid when their coefficients and variables
are interpreted in any commutative ring.

- In the zero ring, every expression is the sole element, so all identities
  hold.
- In characteristic 2, every displayed result is zero because its coefficient
  is divisible by 2. This loss of information does not invalidate an identity.
- In characteristic 3, the third result is zero because 6 = 0. The other
  results remain 2a, 2D, and 2ab, respectively, and need not vanish.
- Zero divisors do not affect any derivation: no factor was removed from an
  equality and no inverse was used.

## Stronger implication: 2a = 2b implies a = b

For a fixed ring K, this implication holds for every a and b if and only if

    2x = 0 implies x = 0 for every x in K.

Indeed, apply that condition to x = a - b; conversely, take a = x and b = 0
in the proposed implication. Thus multiplication by 2 must be injective.
A unit 2 is sufficient, but being a unit is unnecessary: multiplication by
2 is injective in the integers even though 2 has no integer inverse.

**Nonzero characteristic 2: breaks.** In F_2, take a = 0 and b = 1. Then
2a = 0 = 2b, whereas a != b. The same choice works in every nonzero ring of
characteristic 2.

**Characteristic 3: holds, including with zero divisors.** In such a ring,
2*2 = 4 = 1. Multiplying 2a = 2b by 2 yields a = b. This applies, for example,
to the ring F_3 x F_3, which has zero divisors.

**General rings with zero divisors: no unconditional implication.** In
Z/4Z, take a = 0 and b = 2. Then 2a = 0 = 2b, but a != b. Zero divisors alone
do not determine the outcome: the preceding characteristic-3 example has
injective multiplication by 2. Even characteristic zero alone is insufficient:
in Z x F_2, the distinct elements (0,0) and (0,1) have equal doubles.

**Zero ring: holds.** All pairs a and b are already equal. This is not a
counterexample, and no claim that a nonzero element 2 is necessary applies to
this degenerate ring.

## Division and cancellation by D = (a - c)(b - c)

There are two distinct algebraic requirements:

1. Multiplying by a ring inverse of D, or forming a quotient with denominator
   D using such an inverse inside K, requires D to be a unit.
2. Inferring X = Y from DX = DY requires multiplication by D to be injective,
   equivalently, Dz = 0 implies z = 0 for all z in K.

The second condition does not require a unit. For example, in Z, take a = 2,
b = 1, c = 0, so D = 2. Cancellation is valid, but an inverse 1/2 is absent
from Z. A numerical quotient can happen to exist for a particular numerator
without providing an inverse operation on all of K.

**Zero denominator, including fields of characteristics 2 and 3.** In either
F_2 or F_3, take a = c = 0 and b = 1. Then D = 0, and D*0 = D*1 although
0 != 1. Thus cancellation fails, and D has no inverse. The unqualified
division step is invalid even in these fields.

**Nonzero zero divisor in characteristic 2 or 3.** For p = 2 or p = 3, use
K = F_p x F_p, with componentwise operations, and take

    a = (1,0), b = (1,1), c = (0,0),
    D = (1,0), X = (0,0), Y = (0,1).

Here a != c, b != c, D != 0, and X != Y, but

    DX = (0,0) = DY.

Moreover, D times any element has second coordinate zero, so it cannot equal
1_K = (1,1); D has no inverse. This explicitly refutes cancellation even
under a != c, b != c, and D != 0 when zero divisors are present. For p = 3,
it also demonstrates that valid cancellation of 2 says nothing about valid
cancellation of D.

**Another finite example.** In Z/4Z, a = 2, b = 1, c = 0 gives D = 2 != 0.
Then D*0 = D*2 = 0 with 0 != 2, and D is not a unit.

**When it is valid.** In a field, a != c and b != c ensure D is a unit.
In an integral domain, they ensure D is nonzero and cancellable, but D need
not have an inverse in that domain. In an arbitrary commutative ring, D is a
unit if and only if both a - c and b - c are units. For the nontrivial
direction, if DE = 1, then (a - c)((b - c)E) = 1 and similarly for b - c.
No characteristic assumption alone ensures these conditions. For example,
D = 1 when a = b = 1 and c = 0, including in characteristics 2 and 3.

**Zero ring.** With the usual unital convention allowing the zero ring,
0 = 1 and the sole element is a unit: 0*0 = 1. Its multiplication map is
injective on a singleton. Hence cancellation and the unique inverse operation
are trivial there. One should not apply the nonzero-ring assertion that zero
has no inverse to this case.

The small-characteristic identities also cannot justify cancelling their
integer coefficients. In F_2 with a = b = 1 and c = 0, D = 1 while 2D = 0;
one cannot infer D = 0. In F_3 with a = b = 0 and c = 1, D = 1 and cD = 1
while 6cD = 0; one cannot infer cD = 0. These explicit examples mark the
boundary between a valid polynomial identity and an invalid stronger claim.

## Evidence and scope

The evidence is the displayed algebraic derivation and explicit ring
counterexamples. No Lean or Mathlib build, symbolic engine, arithmetic
diagnostic, experiment, benchmark, or cloud action was run. Local commands
read and hashed the supplied brief, created the assigned output directory,
and validated/hashed the authored artifacts. The attestation lists those
commands and all task-file reads. There were no deviations from the blind
input restriction. Only J1 is judged.

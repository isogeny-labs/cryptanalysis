# Implemented tensor construction

The implementation targets ell=1, sufficient for exact Boolean counts and
relation witnesses. It implements the recursive algorithm and its leaf
fallback. The general truncated V-polynomial case ell>1 is not implemented.

## Algorithm-to-code mapping

The local reference is `reference/quantitative-contraction.tex`, from
[the October 25 manuscript](https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/build/quantitative-contraction.tex).

| Source subsection | Code |
| --- | --- |
| Coefficient ring and exact arithmetic | `UnramifiedRing`, binary irreducibility, Newton unit inversion, canonical lifts |
| Parameters and collision packing | `TensorContraction.plan`, `pack_network`; exact conditional expectations |
| Cauchy deformation and integral local coordinates | `cauchy_entry`; power-of-two cancellation before odd-unit inversion |
| Tapered Hermite recovery | `hermite_data`, `precision_for_node`, `hermite_recover` |
| Modes for interactions between groups | `packet_modes`, `mode_tuples` |
| Child networks and descriptions | `packet_tensor_entry`, `child_network` |
| Recursive contraction | `TensorContraction._contract`, `evaluate_deformation` |
| Count-to-witness reduction | `witness`; Boolean leaves may stop at their first satisfying assignment |

The default parameters are r=64, epsilon=1/131072, u_d=floor(epsilon*lambda/2^d),
a_d=2*sum(u_j), and H=ceil(s/floor(sqrt(lambda))). Packing conditions are checked
before recursion. Failure selects exact summation. Explicit equality tensors
are eliminated at leaves without changing the count.

Each retained entry keeps its creation precision and its original canonical
coefficient representatives. New packet entries refer to their own immutable
kernel data; their entry routines do not recursively call the original tensors.
Mode enumeration and coefficient extraction use explicit depth-first stacks.

Two optional exact optimizations are separately tested:

1. Modes with identical source linear forms are coalesced. Their row coefficients
   are added, and the smallest constituent weight is retained. Divisibility by
   that power of two remains valid.
2. `tight_precision` computes the exact Hermite multiplier valuation loss instead
   of the paper's sufficient bound. The default uses the paper's bound.

Small recursive tests use marked experimental parameters so the nonleaf path can
execute on ordinary hardware. They make no asymptotic performance claim. The
default policy retains the manuscript's constants and leaf conditions.

## Arithmetic graph construction

Operations are Boolean predicates on input/output ports. Fanout uses
degree-three equality trees. Every graph edge is subdivided once to make the
graph bipartite. Evaluation hints construct full assignments for testing; hints
are not predicates or oracles in the tensor network.

Integer multiplication follows the paper's two-stage Fourier construction over
Z/(2^J+1). It partitions inputs into J/4-bit limbs, applies two layers of smaller
transforms, multiplies pointwise, applies the inverse transform, and checks
output limbs and carries. The total number of bit ports is linear in input
length up to the construction's constants, with the O(d^(3/4)) degree scale.

Binary-polynomial multiplication uses an odd-length analogue. For J a power of
three, take

    f(U) = U^(2J) + U^J + 1.

This is the cyclotomic polynomial of order 3J. It is irreducible over F2 because
2 has multiplicative order 2J modulo 3J. Thus U has order 3J in the resulting
field. Choose a power-of-three transform length L >= 2n-1 dividing 3J. Odd L is
invertible in characteristic two. Cut inputs into k=floor(J/4) coefficient
blocks and increase J until L <= 3J. Convolution coefficients have degree below
2k-1 < 2J, so field reduction preserves their polynomial content. Two Fourier
stages and their inverse compute the coefficients; overlapping blocks are
recombined by XOR.

These choices put J and L on the square-root input-length scale, giving a linear
total number of bit ports and transform predicates on the d^(3/4) degree scale.
This is a binary-field adaptation, not a claim that the original prime-field
paper formally proves it. Tests compare products against independent carryless
arithmetic, including 131-bit operands. The challenge's sparse reduction
polynomial also permits linear-size XOR reduction graphs.

## Curve and factor-base constraints

Point validity and addition use characteristic-two formulas. The identity has a
dedicated flag and zero coordinates. Selectors distinguish identity input,
inverse pairs, generic addition, and doubling. Slopes are constrained witnesses;
gated equalities do not bypass point validity.

Subgroup membership is encoded as A=[4]S with two doublings and A != O. No
130-bit subgroup scalar multiplication is placed in the network. Since the
curve order is 4n with odd prime n, multiplication by four has the required
prime-order image.

Point encoding uses the low bit of y/x, tied to the coordinates by a constrained
field product. Compact integer products, binary adders, and a comparator enforce

    alpha*enc(A) + beta = quotient*s + residue,
    0 <= residue < threshold.

The complete challenge graph uses public curve parameters, the actual published
Q, and recorded affine hash seeds. No hidden scalar or planted replacement
target is supplied.

## Validation and limit

Tests cover rational Cauchy evaluations, extension-ring interpolation, mode
identities against direct deformation sums, tapered Hermite recovery, recursive
contraction, two levels with canonical lifts, Fourier multiplication, all
point-addition cases, full coordinate relation witnesses, and tampering. The
reference binary arithmetic is also compared with OpenSSL.

The full target graph compiles and passes structural edge/degree checks. Its
default u_0 is zero, selecting exact summation. The recorded attempt exits at
its operation budget and has not found a challenge relation or scalar. The code
and tests do not formally verify the external manuscript or demonstrate a
practical subexponential attack.

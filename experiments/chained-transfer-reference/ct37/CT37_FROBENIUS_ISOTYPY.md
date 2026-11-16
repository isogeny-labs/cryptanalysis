# CT37 — all-extension cross-factor obstruction and Frobenius projectors

**2026-11-12. Standing [pcc:unverified].** This extends CT36's elliptic dual-map work, and does not duplicate the separate native genus-2/Cantor consumer #1501.

## Precise theorem for this fixed pair

The original factors of crypto PR #3877 have models
`E109: y²=x³+x+46` and `E113: y²=x³+44x+21` over F101.
Their independently re-enumerated point counts are 109 and 113, hence
Frobenius traces -7 and -11 and characteristic polynomials

```text
f109(T)=T²+7T+101,  delta109=49-404=-355
f113(T)=T²+11T+101, delta113=121-404=-283.
```

**Proposition.** Hom over the algebraic closure Fbar101 vanishes in BOTH
directions between E109 and E113, hence also over F101^m for every m>=1.
It remains zero after transporting either elliptic factor within its
isogeny class. This is a fixture-specific obstruction, not a statement
about every target factor, cover, nonlinear algorithm or cross-characteristic
computational method.

**Proof.** Both curves are ordinary because 101 does not divide either
Frobenius trace. The classical ordinary-elliptic-curve endomorphism theorem
identifies the rational geometric endomorphism algebras as
Q(sqrt(-355)) and Q(sqrt(-283)); 355=5*71 and 283 is prime, so these
imaginary quadratic fields are different. A nonzero homomorphism between
elliptic curves over an algebraically closed field is an isogeny.
Conjugation by its rational inverse would identify the two endomorphism
Q-algebras, contradiction. This uses standard Deuring/Tate theory and is
not a newly discovered theorem. [pcc:unverified]

This strengthens the prior fixed-prime 3/5/7 CRT *torsion*-separation
argument in `crypto:research/chained_jacobian_transfers_20261110/ODD_KERNEL_CHECKPOINT.md`;
it is now a **geometric all-extension Hom obstruction**, rather than
a bounded Frobenius eigenspace enumeration.

## Constructive integral polynomial identities

With pi the 101-power Frobenius, define in Z[T]:

```text
A(T)=-(T+7)(T²+11T+101)
B(T)= (T+11)(T²+7T+101)
A(T)+B(T)=404.
```

The identity and the respective curve Frobenius equations imply that
A(pi) acts as [404] on E109 and zero on E113; B(pi) does the
opposite. A(pi)/404 and B(pi)/404 are orthogonal idempotents in
End^0(E109 x E113). **These are rational, not integral, idempotents.**
An isogenous genus-2 Jacobian has the same rational isotypic
decomposition, but its integral lattice/polarization can differ.

On the fixed F101-rational group of order 12,317=109*113,
Frobenius fixes points and gcd(404,12317)=1, so these give pointwise
scalar projectors e109=9266, e113=3052 mod 12,317. They are
orthogonal, sum to one and square to themselves on THAT finite group.
These numbers were already mentioned in the root queue: they are
**not presented as a new numerical discovery**. Pointwise
idempotency does not mean global Jacobian idempotency.

## Independent arithmetic oracle and bounds

`ct37_frobenius_isotypy.py` is stdlib-only, uses no producer arithmetic
imports, and counts both exact F101 point groups (109+113), verifies their
orders and Frobenius traces/discriminants, exact Z[T] identities,
annihilating polynomials and orthogonal projectors, and checks both
scalar projectors on **every rational point**, including O.
The extension trace recurrence m=1..24 is a diagnostic and is
not substituted for the all-extension proof. The equal-trace mutation
shows when the distinct-CM premise cannot be applied. All control
failures use explicit exceptions so Python -O cannot drop them.

Run from cryptanalysis root:

```sh
python3 -B experiments/chained-transfer-reference/ct37/ct37_frobenius_isotypy.py > /tmp/ct37.normal
python3 -O -B experiments/chained-transfer-reference/ct37/ct37_frobenius_isotypy.py > /tmp/ct37.optimized
diff -u /tmp/ct37.normal /tmp/ct37.optimized
python3 -m py_compile experiments/chained-transfer-reference/ct37/ct37_frobenius_isotypy.py
```

Development SHA256 source `63375f2be88f213501cf25ac4af0c1245047521fda51beb02da2b581b5c5421b`,
normal stdout `c3f883bfcdd0b7e74c007d201c10e859bbaa28c5bb4d6ef5952d30a90de9a337`.
Local ordinary and optimized runs were byte-identical and compilation passed.
These are producer evidence only. **[pcc:unverified].**

## Consequences, nonconsequences, next bridge

Further elliptic 7-isogeny hops or field extensions cannot create a
homomorphism between these two *geometric* isotypic factors. This
does not prevent genuine Jacobian covers, additional isotypic
components, different ECDLP representations, or algorithms that do
not reduce to those particular cross-factor Hom groups.

The next discriminating test is still projection of the actual native
Phi2/Psi2 and duals through both quotient norms, with independent
Cantor replay across 12,317 rational classes including nonsplit,
ramified and exceptional supports. All-matched cold rho and
index-calculus costs require admission; no paid compute was launched
and no solver-speed claim is made.

## Sources checked (KB unavailable)

- crypto `research/chained_jacobian_transfers_20261110/ODD_KERNEL_CHECKPOINT.md`
  (prior 3/5/7 CRT barrier and 9266/3052 projected scalars).
- crypto `research/chained_jacobian_transfers_20261110/SEVEN_CHAIN_PROOF.md`
  (fixed elliptic models and isogeny relations).
- cryptanalysis `experiments/chained-transfer-reference/ct36/CT36_DUAL49_AUDIT.md`
  (elliptic dual identities; Jacobian bridge still open).
- Tate (1966), *Endomorphisms of Abelian Varieties over Finite Fields*,
  https://doi.org/10.1007/BF01404549 .
- Galbraith (1999), *Constructing Isogenies between Elliptic Curves Over Finite Fields*,
  https://doi.org/10.1112/S1461157000000097 .
- Zarhin (2023), *Isogeny Classes and Endomorphism Algebras of Abelian Varieties Over Finite Fields*,
  https://doi.org/10.4213/im9332e .

Shared research-KB MCP/CLI and encrypted autoresearcher atlas were not
available in this runtime; no exhaustive novelty/absence claim.

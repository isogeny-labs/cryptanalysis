# CT42: maximal two-primary gluing in the three fixed F101 Jacobians

**12 November 2026 | [pcc:unverified].** Scope: the three smooth genus-two sextics T0/T1/T2 and their common CT39 Weil polynomial
`P(T)=(T²+7T+101)(T²+11T+101)`. This extends the upper bound in CT41 to an **exact 2-adic lattice quotient** for the actual three Jacobians. It does *not* establish the principal polarization, native Phi2/Psi2 geometric kernels or their dual, an algorithmic speedup, or a signed scientific proof.

## Computed input and negative controls

The monic sextics, low-to-high coefficients over F101, are:
- T0: `[31,75,74,54,71,55,1]`
- T1: `[95,26,19,27,94,91,1]`
- T2: `[95,93,43,39,92,17,1]`.

Independent polynomial Euclidean, Frobenius powering and squarefreeness tests find `gcd(f,f')=1` and the degree signatures
`[deg gcd(f, X^(101^d)-X) for d=1..6] = [0,0,0,0,0,6]` for each sextic. Thus each is irreducible of degree six and Frobenius permutes all six finite Weierstrass points as one cycle. Independent local Python and Go implementations reproduced this polynomial signature; the separately committed JavaScript program is CI-executable. Negative controls: smooth T0 constant `31 -> 37` has factor degrees (3,3) and signature `[0,0,6,0,0,6]`; smooth T0 x-coefficient `75 -> 79` has (2,4) and signature `[0,2,0,6,0,2]`.

## Frobenius on geometric J[2]

For a squarefree degree-six hyperelliptic genus-two model `y²=f(x)` in odd characteristic, `J[2](Fbar)` is the four-dimensional F2 space of **even subsets** of the six finite branch points, modulo complements. A six-cycle on the roots acts in the four basis classes `b_i={root_i,root_5}`, i=0,..,3, as the linear operator with column bitmasks `[3,5,9,14]`.

Direct F2 arithmetic gives `F^6=I`, `rank(F^3-I)=2`, `rank(F-I)=4`, and characteristic and minimal polynomials `(T²+T+1)²`. This J[2] is a nonsemisimple self-extension. Each individual elliptic factor has irreducible mod-2 polynomial `T²+T+1` and `F^3=I` on its 2-torsion. In particular none of the three J is F101-isomorphic to the split elliptic product.

## Exact 2-adic gluing theorem (conditional on CT39)

Let `M=T_2(J)`, `W109,W113` be the rational isotypic subspaces defined by `S=F+V` with eigenvalues -7 and -11, and `Mi=M ∩ Wi`. CT41 constructs the Frobenius-equivariant injection

`G=M/(M109+M113) -> (1/4)M109/M109 ≅ (Z/4Z)^2`.

Hence `4G=0` and `|G|<=16`. **Claim for each T0/T1/T2: `G ≅ (Z/4Z)^2`, with exponent four and order sixteen [pcc:unverified].**

1. On `M109`, `F²+7F+101=0` gives `F³+I=4(-13F+177)`. On `M113`, `F²+11F+101=0` gives `F³+I=4(5F+278)`. These are integral identities on the saturated sublattices.
2. If `2G=0`, then `2m=m109+m113` for each `m∈M`. Applying `F³+I` produces `2(F³+I)m∈4(M109+M113)`, so torsion-freeness forces `(F³+I)m∈2M`. Thus `F³=I` on `J[2]=M/2M`, contradicting the rank-two nonzero `F³-I` established by the six-cycle. Therefore G contains an element of order four.
3. The image of G in `M109/4M109` is Frobenius-stable. Its subgroup `2G` is now nonzero and Frobenius-stable in `2(M109/4M109) ≅ M109/2M109`. The latter has irreducible polynomial `T²+T+1`; therefore `2G=2(M109/4M109)`.
4. This forces `G=M109/4M109`: for a subgroup H of `(Z/4)^2`, `2H=2(Z/4)^2` implies H spans modulo 2 and hence equals all of `(Z/4)^2` (Nakayama, or elementary counting). So `|G|=16`, attaining CT41's abstract bound in the actual three Jacobian modules.

The argument determines only the **unpolarized quotient**. It does not identify the graph of the mod-4 factor gluing, its Weil pairing, the principal polarization, or the actual kernels of the two Jacobian hops. This is an application of classical branch-point torsion and 2-adic lattice theory, not a new general theorem. The standalone oracle audits arithmetic inputs and necessary module identities; it is not a machine-checked algebraic geometry proof.

## Reproduction

```sh
node --check experiments/chained-transfer-reference/ct42/ct42_gluing.js
node experiments/chained-transfer-reference/ct42/ct42_gluing.js > /tmp/ct42.normal
node --no-opt experiments/chained-transfer-reference/ct42/ct42_gluing.js > /tmp/ct42.noopt
diff -u /tmp/ct42.normal /tmp/ct42.noopt
cat /tmp/ct42.normal
```

This run's separately written Python and Go prime-field oracles agree on the full five-sextic signature corpus. The code and bounded tests cannot independently sign the scientific claim. **[pcc:unverified].**

## Sources and next decisive proof obligation

- [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877): exact T0/T1/T2 models and `GEOMETRIC_JACOBIAN_DISTINCTION.md`, plus prime-field maps and retained native audits.
- [cryptanalysis #1502](https://github.com/isogeny-labs/cryptanalysis/pull/1502): CT39 two-field Weil polynomial, CT40 projector identities, CT41 F+V bound.
- Cassels and Flynn, *Prolegomena to a Middlebrow Arithmetic of Curves of Genus 2*: hyperelliptic branch-point 2-torsion; Milne, *Abelian Varieties*: Tate modules. The shared research-KB connector and locked autoresearcher lead atlas were not accessible in this runtime; no novelty or absence claim.

**Next discriminator:** reconstruct the *actual* mod-4 gluing graph and Weil pairing from the native degree-four elliptic quotients, and test polarization/kernel compatibility against the independently replayed 12,317-class Cantor corpus and geometric torsion. Only then can this constrain actual correspondence degrees and duals. Cold end-to-end comparisons with optimized rho and the existing index-calculus baseline remain subject to approved EKS/S3 budget admission. No cloud spending, merge bypass or speedup claim.

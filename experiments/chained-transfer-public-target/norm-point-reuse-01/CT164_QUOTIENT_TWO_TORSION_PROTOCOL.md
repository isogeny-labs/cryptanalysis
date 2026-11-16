# CT164 — mod-4 rational 2-torsion of degree-eight fixed-nu12 quotients: protocol

2026-11-16. Source-only bounded continuation of CT160–163. **[pcc:unverified]**.

## Source and non-blinding disclosure
Exploratory local SymPy Hermite-lattice and independent finite-coset computations were performed **before this protocol was committed**. They suggested that every one of CT163's nine Frobenius-stable maximal isotropic kernels yields a principally polarized quotient with exactly **two** rational 2-torsion points over F223. This follow-up is therefore a **retrospective mathematical replication**, not a blinded preregistered discovery or any timing experiment. Freeze this statement and acceptance rules before the committed source and hosted replay. Do not edit CT160–163 source/fixtures.

Inputs: CT160 actual fixed-nu12 source/target F223^3 point census (order 11086844, full K-rational E[2]); CT161 Weil polynomial X^6-2724 X^3+223^3; CT162 four genus-three hyperelliptic orbit partitions and their rational J[2] sizes; CT163 nine explicit Galois-stable kernels and the 3-cycle geometric Frobenius on A[2]. Parent PR #1589; owner-priority native norm-reuse #1533, admitted primitive-price #1562, and concurrent explicit genus-3 #4357 remain untouched.

## Algebra and acceptance rules

Write K=F_(223^3), k=F_223, A=Res_(K/k)(E), and let pi be K-Frobenius on E's 2-adic Tate module. Since E[2](K) has four points and #E(K) is 4 times an odd integer, pi=I+2M (mod 4), where M mod 2 is invertible. From tr(pi)=2724 we obtain tr(M)=1 mod 2; hence det(M)=1 mod 2 as well. Enumerate **both** 2x2 matrices over F2 with trace=det=1, without choosing one from unchecked native coordinates.

Choose compatible Tate bases of three Frobenius-conjugate geometric factors, giving k-Frobenius F(v0,v1,v2)=(pi v2,v0,v1) mod 4. For each exact CT163 kernel H subset (F2)^6, form the integral index-eight lattice L'=2 Z^6 + lifts(H). Since A/H has 2-adic Tate lattice (1/2)L', the rational quotient 2-torsion has size 2^d where d=dim_F2 ker(F-I on L'/2L').

Primary checker: compute an explicit 6x6 integral basis for L', express the Frobenius action in that basis, and compute binary rank. Independent checker: enumerate all 64 quotient classes from 512 mod-4 representatives in L'/4 Z^6; count fixed classes without calculating a lattice basis.

Require: exact nine CT163 basis records, two valid M matrices, same 2-torsion size for both M matrices and for every kernel, all nine lattice invariance checks, 64 cosets per kernel, mutually identical canonical JSON under normal Python, Python -O and Node, plus negative controls. If any case differs, do not promote the screening conclusion.

When successful, the six **mixed** even-degree quotients have #B(k)[2]=2, which, combined with CT162, retains hyperelliptic orbit types (1,1,6) and (2,3,3), excluding the two with four rational 2-torsion points. Factorwise quotients are geometrically product-polarized and are not smooth genus-three Jacobians. This screen says nothing about a *nonhyperelliptic* genus-three Jacobian, actual quotient equations, a prime-field elliptic source homomorphism or ECDLP cost.

## Reproduction and boundaries

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
python3 -B "$D/ct164_quotient_two_torsion.py" --self-test > /tmp/ct164-a.json
python3 -O -B "$D/ct164_quotient_two_torsion.py" --self-test > /tmp/ct164-o.json
node "$D/ct164_independent_coset.cjs" --self-test > /tmp/ct164-n.json
cmp /tmp/ct164-a.json /tmp/ct164-o.json
cmp /tmp/ct164-a.json /tmp/ct164-n.json
cmp /tmp/ct164-a.json "$D/CT164_RESULT.json"
sha256sum /tmp/ct164-a.json
```

No EKS/Spot, GPU, native actual 695/701 replay, paid pricing, complete solve, benchmark ledger or PCC promotion is authorized by this protocol. The owner-admitted C169/C13a/C13b/D and fully matched cold single-target prime-field solve retain their existing gates.

Literature / existing results: CT160–163 reports and exact scripts; Howe–Leprévost–Poonen, *Large torsion subgroups of split Jacobians of curves of genus two or three*, Forum Math. 12 (2000), 315–364, https://arxiv.org/abs/math/9809210; Costa et al., *Restrictions on Weil Polynomials of Jacobians of Hyperelliptic Curves* (2022), https://doi.org/10.1007/978-3-030-80914-0_7. These are related construction and parity tests, **not** a claim that the CT164 quotient exists as a curve. Shared research-KB unavailable in this connector execution; inspected repository reports as fallback. No novelty claim.

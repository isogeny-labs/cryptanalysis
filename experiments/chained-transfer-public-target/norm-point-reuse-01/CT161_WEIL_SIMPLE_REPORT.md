# CT161 — actual fixed-nu12 Weil restriction is F223-simple (dimension 3)

2026-11-16 · **[pcc:unverified]**. Additive follow-up on cryptanalysis #1589 and root crypto #3877; protocol `CT161_WEIL_SIMPLE_PROTOCOL.md` committed **before** the new checker. Earlier exploratory SymPy factoring suggested the claim; neither novelty nor blind discovery is asserted.

## Input, verified scope and exact polynomial

CT160's two *actual fixed* elliptic models have complete producer/hosted-census group order `#E(F_(223^3))=11,086,844`, hence cubic trace `T=223^3+1-11,086,844=2724`. The certificate reads the unchanged `CT160_FULL_CENSUS.json` and requires the exact schema, full cardinality, both model partitions/orders, group-count identities, nominal flag and source data SHA-256 `58af5c02d3a5afc722e1662e2fb5ade0534e65f824a29c97abc51dab827d08c8`.

For either model, let `K=F_(223^3)`, `k=F_223`, `A=Res_(K/k)(E)`. Restriction-of-scalars/Frobenius induction gives its **degree-six** characteristic polynomial

```text
F(X) = X^6 - 2724 X^3 + 11,089,567.
```

Because F is monic, a nontrivial factorization over Q would reduce to a nontrivial factorization of equal degrees over F5. The reduction is `f(X)=X^6+X^3+2`.

## Finite irreducibility certificate, no CAS dependency

Our standalone polynomial implementation over F5 computes these *actual residues*, in coefficient/monomial notation:

```text
X^(5^2) mod f  = X + 3 X^4
X^(5^3) mod f  = X^5 + X^2
X^(5^6) mod f  = X
gcd(f, X^(5^2)-X) = gcd(f, 3 X^4) = 1
gcd(f, X^(5^3)-X) = gcd(f, X^5+X^2-X) = 1
```

The second gcd has an explicit Euclidean remainder chain `X^2+2, 3X+3, 3`, ending in a nonzero constant. Since the only prime divisors of degree 6 are 2 and 3, Rabin's criterion proves f irreducible over F5. Therefore **F is irreducible over Q**, without any appeal to a factorization heuristic. A separately executed SymPy `Poly(...).is_irreducible` returned true for both F/Q and f/F5, but this is merely an independent local algebra cross-check, not signed PCC.

## Precise algebraic implication

A has dimension 3. Since its rational Frobenius polynomial is irreducible, it has **no proper nonzero k-abelian subvariety** (use Frobenius characteristic polynomials, Poincaré complete reducibility and Tate's finite-field isogeny criterion). Hence A is **k-simple**, and

`Hom_k(A,B)=Hom_k(B,A)=0`

for *any* abelian variety B/k of dimension 1 or 2. In particular no k-defined elliptic curve or genus-2 Jacobian can serve as an isogeny/homomorphism carrier into or out of either actual fixed nu12 Weil restriction. This strictly extends CT160's no-prime-field-elliptic-Hom calculation to every k-abelian surface.

**Do not conclude geometric simplicity.** Over K the Weil restriction splits into the product of E and its two Frobenius conjugates. The obstruction only concerns maps **defined over k=F223** and the two exact CT160 isogeny classes. It does not rule out a genus-3 or higher carrier, non-homomorphic computational transport, maps after base extension to K, other primes, other curves, or cross-characteristic algorithms.

## Reproducibility and controls

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
python3 -B "$D/ct161_weil_simple_certificate.py" > /tmp/ct161.json
python3 -O -B "$D/ct161_weil_simple_certificate.py" > /tmp/ct161-opt.json
cmp /tmp/ct161.json /tmp/ct161-opt.json
```

Local Python normal/-O produced equal canonical JSON. Five controls were rejected: source model count, field size, boolean masquerading as target count, mutant flag and **actual reducible** `X^6+1` (specified by the controlled `trace=0, field=1`) failing the Rabin gate. A first negative variant had used `trace=0, field=223` and was rejected by the pinned-f polynomial assertion rather than demonstrating reducibility; it was corrected before this report and preserved as a source commit `93b01a24`. Developer-local result JSON SHA-256 `65abb01cf14bd1d0f4a766ccb7ec0dfefa31f21deef73b906b9b206d0c8b6df3` (canonical output before/after the test-only correction is identical). Source-only CI must be inspected separately.

Research-KB and Conductor weren't available in this connected runtime. Sources reviewed: actual CT160 certificate/source, CT151, CT149, #1533, #1589, root #3877 and #4425, ordinary finite-field Weil-restriction/Tate theory, and F. Oort's *Abelian varieties over finite fields* §5.3–5.4 (https://math.nyu.edu/~tschinke/books/finite-fields/submitted/oort.pdf). This is an exact-instance consequence of established theory, not a novelty claim.

## Performance research follow-up

The strongest candidate remaining for this *specific* k-model is a dimension-3-or-higher factor with exactly the matching irreducible Weil polynomial and an **explicit scalar-blind, subgroup-injective map**. Finite curve enumeration or a theoretical isogeny does not furnish the map or a better DLP solver.

Keep CT125's original 695/701 all-record native norm-reuse parity and the admitted same-host `C169, C13a, C13b, D` pricing as the separate highest-priority cost gate. No owner admission, no paid EKS/Spot/GPU work, no complete transferred public-Q prime-field DLP, no matched cold rho/BSGS/IC wall/counter+RSS result, and no signed PCC were produced here. [pcc:unverified]

# Exact anti-Frobenius kernel and EDS-normalizer identity

## Statement

Let `E/F_p: y²=x³+Ax+B` be nonsingular, `p>3`, and let its rational
group have odd prime order `r>=5` with `gcd(r,p-1)=1`. For any
nonidentity rational point `P`, let `K_E(X)` be the monic x-kernel
polynomial of `1+pi`, as in the [generic kernel-value identity](GENERIC_KERNEL_EVALUATION_IDENTITY.md).
Let `psi_n(P)` use the convention `psi_2(P)=2y(P)` and define the
[Lauter–Stange EDS normalizer](https://arxiv.org/pdf/0803.0728)

```text
Phi(P) = (psi_(p-1)(P)/psi_(p-1+r)(P))^(inverse(r² mod p-1)).
```

Then the following is an **exact field-value identity**, not just a
quadratic-character agreement:

```text
K_E(x(P)) = 2 y(P) Phi(P)^r.                              (1)
```

For the quadratic character `chi_p`, `r` is odd, so (1) implies

```text
chi_p(K_E(x(P))) = chi_p(2) chi_p(y(P) Phi(P)).           (2)
```

The orientation is determined by the field and is independent of
the curve and generator. This construction uses no CM assumption or
smooth horizontal relation. [pcc:unverified]

## Derivation

The [Ward period law, as stated in Lauter–Stange Theorem 4](https://arxiv.org/pdf/0803.0728),
gives an element `alpha in F_p*` such that, whenever `psi_n(P)` is
nonzero,

```text
psi_(n+r)(P)/psi_n(P) = alpha^(2nr+r²).                  (3)
```

The condition `gcd(r,p-1)=1` selects `alpha` uniquely in `F_p*`.
At `n=p-1`, the exponent in (3) reduces to `r² mod (p-1)`.
Thus the displayed definition of `Phi(P)` gives `Phi(P)=alpha^(-1)`.
Now `h=(r-1)/2` and `h+1=-h+r`. Since
`psi_(-h)(P)=-psi_h(P)`, equation (3) at `n=-h` yields

```text
psi_(h+1)(P) = -psi_h(P) alpha^r,
psi_h(P)/psi_(h+1)(P) = -Phi(P)^r.                        (4)
```

The [generic kernel-value identity](GENERIC_KERNEL_EVALUATION_IDENTITY.md)
is `K_E(x(P))=-psi_2(P)psi_h(P)/psi_(h+1)(P)`. Combining it with
(4) and `psi_2(P)=2y(P)` proves (1). All terms used above are
nonzero: `P` has order `r`, the indices are nonmultiples of `r`, and
`p-1` is coprime to `r`. [pcc:unverified]

## Independent finite checks and consequence

The saved [exact-value checker](eds_kernel_normalizer_value_check.py)
passes on all 60 nonzero points of the `D=-19`, `p=47`, `r=61`
control; all 52 of the `D=-163`, `p=47`, `r=53` control; eight
predeclared labels on each endpoint of the `p=1009`, `r=1069`
degree-five horizontal edge; and all 46 nonzero points of
`E/F_43:y²=x³+x+3`, `r=47`. The last curve has `chi_43(2)=-1`,
and the predicted sign reversal holds at every point. Run from the
repository root:

```sh
/Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/eds_kernel_normalizer_value_check.py
```

The finite checks validate the implementation of the definitions;
the derivation supplies the general statement. The earlier
[kernel/normalizer census](NORMALIZER_KERNEL_EQUIVALENCE_REPORT.md)
had only established sign agreement on its tested fields. Equation
(2) explains it and fixes the previously unspecified orientation.
It also makes the EDS-normalizer and anti-Frobenius-kernel predicates
the **same generic point function up to `chi_p(2)`**. Their separate
failed scalar-character screens cannot be combined as independent
bits. A point relation containing the hidden scalar and a CM-specific
yield or cost advantage still require a different construction.
[pcc:unverified]

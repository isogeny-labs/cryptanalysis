# Frozen y-normalized EDS character screen

## Candidate

For a nonzero rational point `Q=[d]G` on the fixed
`D=-19`, `E/F_47:y²=x³+x+38`, `r=61`, `G=(2,1)` control, let
`Phi(Q)` be the EDS normalizer of [Lauter and Stange,
Theorem 8](https://arxiv.org/pdf/0803.0728):

```text
Phi(Q) = (W_Q(p-1)/W_Q(p-1+r))^(inverse(r² mod p-1)).
```

Their theorem makes this a function of the supplied point without
knowing `d`. For odd `p` and `r`, standard division-polynomial parity
gives `Phi(-Q)=-Phi(Q)`: the numerator index is even, the denominator
index odd, and the inverse exponent is odd. Since `y(-Q)=-y(Q)`,
the field-character predicate `chi_p(y(Q)*Phi(Q))` is even under
point negation, matching a necessary symmetry of `chi_r(d)` when
`r=1 mod 4`. This is a **candidate**, not an asserted identity.
It does not use the smooth CM element in its definition. [pcc:unverified]

Orient the predicate by its value at `G`, so it equals `+1` there.
The predeclared exact prediction is

```text
chi_p(y(G)*Phi(G)) * chi_p(y([d]G)*Phi([d]G)) = chi_61(d)
```

for **every** `d=1,...,60`. The first three scalar labels were
inspected before this freeze and agree; they are a pilot, not
independent confirmation. The runner must retain all 60 values,
check nonzero denominators, check `Phi(-Q)=-Phi(Q)` pointwise, and
report the first mismatch and full agreement count. Any mismatch
rejects this exact ray-label identity on the fixed smooth CM control.
If it survives all 60, only then test a second CM curve, a same-order
horizontal pair, and known P-192 multiples under a new frozen
protocol. Even exact finite agreement would not show a CM-specific
gain or full recovery cost below rho. [pcc:unverified]

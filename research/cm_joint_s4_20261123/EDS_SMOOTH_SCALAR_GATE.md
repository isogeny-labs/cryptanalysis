# EDS residues under a smooth CM scalar: the remaining orientation

## The published point-dependent object

Let `W_G(n)=psi_n(G)` be the elliptic divisibility sequence formed by
evaluating standard division polynomials at `G`, and let `Q=[d]G` with
the minimal positive `d` unknown. The EDS-residue problem asks for the
field quadratic character `chi_p(W_G(d))` from `(E,G,Q)`. This is a
genuinely point-dependent one-bit problem, but it is **different** from
the scalar's ray character `chi_r(d)` in the preceding notes. In the
non-perfectly-periodic regime and under the stated character condition,
[Lauter and Stange, Theorem 1 and Corollary 2](https://arxiv.org/pdf/0803.0728)
show that an EDS-residue evaluator can be used in a subexponential-time
reduction to the full ECDLP. The assumptions and reduction cost matter;
the theorem does not provide the evaluator. [pcc:unverified]

Under its hypotheses, the same paper's Proposition 4 gives the
quadratic character of `W_G(d+1)/W_G(d)` from the known points in
polynomial time. This
propagates **relative** EDS signs while leaving the absolute sign of
`W_G(d)` undetermined. Its Proposition 3 and Corollary 2 explain why an
oracle for that absolute sign can be consequential. The repository's
earlier [EDS-residue study](https://github.com/isogeny-labs/crypto/blob/main/research/notes/cm-isogeny/RESEARCH_EDS_RESIDUE.md)
already explores its period, bias, and pairing connections; this note
only audits how the current smooth-norm scalar interacts with it.
[pcc:unverified]

## What a known smooth scalar contributes

The division-polynomial composition identity in
[Shparlinski and Stange, Lemma 2](https://arxiv.org/pdf/0912.5246)
is, for positive `m,n`,

```text
W_G(nm) = psi_n([m]G) * W_G(m)^(n^2).
```

Taking `m=d`, with `n` coprime to `r`, gives an exact relation that reads the independently
supplied `Q`:

```text
chi_p(W_G(nd)) = chi_p(psi_n(Q)) * chi_p(W_G(d))^(n^2).
```

If `n` is even, the unknown EDS-residue sign cancels. If `n` is odd,
the known point value only transfers that unknown sign to another
indexed term. On the `D=-19` control, the smooth-norm element
`alpha=1+pi` has norm `35=5*7` and acts on rational points as `[2]`.
The `n=2` identity therefore reads
`chi_47(W_G(2d))=chi_47(psi_2(Q))=chi_47(2y(Q))`. This is a valid
coordinate-dependent relation, but the smooth ideal does not calculate
the missing absolute sign. Direct doubling already supplies the same
scalar action. [pcc:unverified]

The two one-bit quantities disagree on the finite CM control even at a
known scalar: `psi_1(G)=1`, while `psi_2(G)=2y(G)=2` has
`chi_47(2)=+1` and the ray label has `chi_61(2)=-1`. This rules out
identifying the EDS residue with the ray character by their shared
quadratic terminology. The small check is reproducible with
`pow(2,23,47)==1` and `pow(2,30,61)==60`. [pcc:unverified]

## P-192 negation gate and cost condition

For standard short-Weierstrass division polynomials,
`psi_n(-Q)=(-1)^(n+1)psi_n(Q)`. P-192 has `p=3 mod 4` and
`r=1 mod 4`. Hence, for even `n` and nonzero values,

```text
chi_p(psi_n(-Q)) = -chi_p(psi_n(Q)),
chi_r(-d) = chi_r(d).
```

No unmodified even-index field-character value can equal the ray label
on both `Q` and `-Q`. This does not exclude odd-index division-polynomial
values, ratios with another negation-odd factor, or EDS residue as a
*different* oracle. The modular conditions and `gcd(r,p-1)=1` were
checked from the exact P-192 parameters in the adjacent notes.
[pcc:unverified]

### The normalizing-character condition is met on P-192

Lauter–Stange Theorem 6 defines a known-point normalizer
`Phi(G)=(W_G(p-1)/W_G(p-1+r))^(1/r^2)` in `F_p^*`, where the exponent is
the inverse of `r^2 mod (p-1)`. Its Corollary 2 requires `Phi(G)` to be a
quadratic nonresidue. On the exact standard P-192 generator, evaluated
division-polynomial recurrences give

```text
Phi(G) = 0x1d10735da9aeffd5b5f65e3aca48654bbbf69949c49f14c0,
chi_p(Phi(G)) = -1.
```

The `D=-19` finite control gives `Phi(G)=0x28` and the same character.
Both computations checked that the defining ratio is nonzero, that
`Phi(G)^(r^2)` equals it, and that the value computed separately at
`[2]G` equals `Phi(G)^4 psi_2(G)`. These are producer checks, not an
independent PCC verdict. [pcc:unverified]

There is a second exact sign calculation using Ward's shift multiplier
in the same paper's Theorem 4. Write
`W_G(n+r)=A^n B W_G(n)`, where
`B=W_G(r+1)^2 W_G(2)/W_G(r+2)`. Since `p-1` is even,
`A^(p-1)=1`; hence the normalizer's defining ratio is `1/B`.
Taking quadratic characters, with `r` odd, gives

```text
chi_p(Phi(G)) = chi_p(B) = chi_p(W_G(2)/W_G(r+2)).
```

This shorter route also returns `-1` on both instances. It only
evaluates division polynomials at **known** points and indices, and
does not evaluate `W_G(d)` for an unknown `d`. [pcc:unverified]

The checks can be reproduced without constructing the high-degree
coefficient polynomials:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import GF, EllipticCurve, ZZ

cases = [
    ('D-19', 47, 61, 1, 38, 2, 1),
    ('P-192',
     6277101735386680763835789423207666416083908700390324961279,
     6277101735386680763835789423176059013767194773182842284081,
     -3, int('64210519E59C80E70FA7E9AB72243049FEB8DEECC146B9B1', 16),
     int('188DA80EB03090F67CBF20EB43A18800F4FF0AFD82FF1012', 16),
     int('07192B95FFC8DA78631011ED6B24CDD573F977A11E794811', 16)),
]
for name, p, r, a, b, gx, gy in cases:
    E = EllipticCurve(GF(p), [a, b])
    G = E(gx, gy)
    assert (r*G).is_zero() and ZZ(r*r).gcd(p-1) == 1
    def W(P, n):
        return E.division_polynomial(ZZ(n), (P[0], P[1]),
                                     two_torsion_multiplicity=1,
                                     force_evaluate=0)
    ratio = W(G, p-1)/W(G, p-1+r)
    phi = ratio**ZZ(r*r).inverse_mod(p-1)
    phi2 = (W(2*G, p-1)/W(2*G, p-1+r))**ZZ(r*r).inverse_mod(p-1)
    B = W(G, r+1)**2 * W(G, 2)/W(G, r+2)
    assert phi**(r*r) == ratio == 1/B
    assert phi2 == phi**4 * W(G, 2)
    assert phi**((p-1)//2) == B**((p-1)//2) == -1
    print(name, {'phi_G': hex(int(phi)), 'phi_legendre': -1,
                 'shift_multiplier_legendre': -1,
                 'doubling_identity_ok': True})
PY
```

These conditions make the **published conditional reduction** applicable
to a hypothetical absolute EDS-residue evaluator for the specified
P-192 generator. They do not construct that evaluator. Producer claim
`PCC-20261124-202050` is unverified. [pcc:unverified]

If an absolute EDS-residue oracle costs `T` in a common operation unit, the
published reduction uses order `log2(r)` oracle calls plus polynomial
overhead. A cold P-192 claim therefore needs a budget of the shape

```text
setup + about 192*T + recovery overhead < sqrt(pi*r/4),
```

with all phases charged in the same unit. The rho reference is about
`2^95.826` group additions, making `2^88.241` equivalents per call an
optimistic count-level ceiling before setup and overhead. The paper's
big-O constants have not been instantiated here; this is a conditional
oracle cost gate, not an
end-to-end measurement. The `alpha=1+pi` composition relation supplies
no such oracle because its even case cancels the required sign.
[pcc:unverified]

The next admissible CM proposal would need an explicit function of
`(E,G,Q)` and the horizontal-isogeny data that returns the **absolute**
EDS residue (or an equally useful point label), a proof of its
transformation law, and a same-order ordinary-curve control that isolates
the isogeny's contribution to cost or yield. Only then is a fully
charged comparison with rho meaningful. [pcc:unverified]

Producer claim: `PCC-20261124-17c073` (unverified). [pcc:unverified]

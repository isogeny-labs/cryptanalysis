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

Conditionally, if an EDS-residue oracle meets the hypotheses of
Lauter–Stange Corollary 2 and costs `T` in a common operation unit, the
published reduction uses order `log2(r)` oracle calls plus polynomial
overhead. A cold P-192 claim therefore needs a budget of the shape

```text
setup + about 192*T + recovery overhead < sqrt(pi*r/4),
```

with all phases charged in the same unit. The rho reference is about
`2^95.826` group additions, making `2^88.241` equivalents per call an
optimistic count-level ceiling before setup and overhead. The paper's
big-O constants and its character condition have **not** been
instantiated for P-192 here; this is a conditional gate, not an
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

# CT29: independent rational-map audit

Standing: **[pcc:unverified]**. Producer-run local evidence, not a signed PCC verdict.

## Exact identity

For E: y²=f(x)=x³+ax+b and each declared monic cubic kernel h, the standalone Python verifier derives the normalized map using root power sums and the logarithmic derivative L=h'/h:

    T=f L-(3*x²+s1*x+s2+3*a)
    A=(3*x²+a)L-9*x-3*s1
    X=x+2*A-4*T'
    Y=y*X'

Here s1 and s2 are the first two root power sums of h. With X=N/D, D=h² and W=N'D-ND', it checks the following identity coefficient by coefficient in F101[x]:

    f*W² == D*(N³+a'*N*D²+b'*D³)

This checks a global rational-function identity, not merely a fixed number of point samples. It does NOT independently derive the cubic kernels or prove the geometric kernel order.

## Reproduction

    python3 -B experiments/chained-transfer-reference/ct29/audit_rational_maps_stdlib.py

The file is stdlib-only and independent of the producer's SymPy code. Local Python 3.13.5 results on 2026-11-11:

| Case | Rational source points | Ordered homomorphism pairs | Equation identity | Wrong-target negative control |
|---|---:|---:|---|---|
| E109 nondual | 109 | 11,881 | pass | pass |
| E109 backtrack | 109 | 11,881 | pass | pass |
| E113 nondual | 113 | 12,769 | pass | pass |
| E113 backtrack | 113 | 12,769 | pass | pass |

**Total: 49,300 ordered point-pair homomorphism checks, four polynomial identities, four wrong-codomain rejection checks** [pcc:unverified]. A scoped GitHub Actions workflow executes this script separately; check its exact-head result before claiming CI success.

## Sources and scope

Repository sources: crypto #3877 CT24_PLAN.md, cryptanalysis #1492 RESULTS.md and concurrent #1493. Literature: Kohel/Vélu formulas as implemented in Sage: https://sources.debian.org/src/sagemath/10.10-3/src/sage/schemes/elliptic_curves/ell_curve_isogeny.py . The shared KB MCP was unavailable in this runtime; autoresearcher lead atlas was locked, so no novelty claim.

The geometric F101^6 7-kernel, Frobenius, gluing, genus-two Jacobian map, dual and complete solving costs remain outside this check. No cloud spend.

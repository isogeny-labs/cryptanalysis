# CT162 — genus-3 hyperelliptic Weil-polynomial and 2-torsion carrier screen

2026-11-16 · **[pcc:unverified]**. Additive research on cryptanalysis #1589, following CT160/CT161. The CT125 native 695/701 and CT141 pricing owner lanes remain untouched. This is a **necessary-condition filter, not a construction or completed attack**.

## Exact fixed nu12 input

Over k=F223 and K=F_(223^3), the two actual fixed nu12 elliptic curves counted by CT160 have #E(K)=11,086,844 = 4 × 2,771,711 and **three K-rational roots of y=0** each. Therefore their K-rational 2-torsion groups each have exactly four elements (including O). By restriction of scalars, A=Res_(K/k)(E) has #A(k)[2]=4. CT160's immutable JSON is bound by SHA-256 \`58af5c02d3a5afc722e1662e2fb5ade0534e65f824a29c97abc51dab827d08c8\`; this continuation reuses its recorded counts rather than rerunning full native Jacobian arithmetic.

CT161's six-dimensional rational Frobenius polynomial is

\`F(X)=X^6-2724X^3+223^3\`, so \`F(X) mod 2 = X^6+1\`.

For any smooth *hyperelliptic* genus-3 C/k whose Jacobian is k-isogenous to A, Costa–Donepudi–Fernando–Karemaker–Springer–West (2020), Proposition 2.4, require

\`F(X) ≡ prod_i (X^(d_i)-1)/(X-1)^2 (mod 2)\`,

where the d_i are the Frobenius orbit lengths on the eight geometric Weierstrass points, a partition of 8. This is a **necessary**, not sufficient, criterion.

## Complete mod-2 enumeration

Two separately coded source-only enumerators (Python GF2 bit-polynomial arithmetic and Node GF2 coefficient arrays) enumerated **all 22 partitions of 8** and found exactly four permitted partitions:

| Frobenius orbit sizes | Rational J[2] points computed from even subsets / complement | Allowed for odd-degree A→J isogeny? |
|---|---:|---|
| 1+1+3+3 | 4 | Yes |
| 1+1+6 | 2 | No |
| 2+3+3 | 2 | No |
| 2+6 | 4 | Yes |

This is an exact finite statement about the fixed Weil polynomial. The second column is computed by permuting all 64 elements of J[2](kbar) represented as even subsets of eight branch points modulo complement and counting the Frobenius-fixed classes.

**Crucial degree qualification:** If A→J is an **odd-degree k-isogeny**, it is an isomorphism on geometric 2-torsion with Frobenius action; hence the second column must equal #A(k)[2]=4, leaving only \`(1,1,3,3)\` or \`(2,6)\`. An **even-degree** isogeny can change the rational 2-torsion rank. In particular the root project's proposed geometric degree-eight quotient is *not* covered by this extra exclusion. All four mod-2 patterns remain possible under a general unspecified-degree isogeny.

Because at least one pattern passes, **this does NOT exclude a hyperelliptic genus-3 Jacobian**. It says nothing about a nonhyperelliptic smooth plane quartic, any actual isogeny construction, Jacobian DLP cost, or arbitrary prime-field inputs.

## Another free carrier search gate: point counts

The polynomial has only X^6,X^3,X^0 coefficients, so for a hypothetical genus-3 C/k with this Jacobian, its first three extension-field point counts are forced:

* #C(F223) = 223+1 = **224**;
* #C(F_(223^2)) = 223^2+1 = **49,730**;
* #C(F_(223^3)) = 223^3+1-3×2724 = **11,081,396**.

Any candidate explicit C failing a count cannot have the target Weil polynomial; matching these small counts alone does not establish an isogeny or group embedding. For a hyperelliptic C, additionally factor its degree-7/8 branch polynomial, include the point at infinity where needed, and enforce one of the four orbit partitions above. For proposed *odd-degree* carriers, enforce one of the two stronger patterns. These are cheap early filters **before** implementing expensive divisor arithmetic or cost benchmarking.

## Evidence, controls, reproducibility

The quick exploratory partition enumeration occurred **before** the CT162 repository protocol; discovery is retrospective. The controlled source-only Python and independent Node implementations were run **after** protocol commit \`7ccb6c68\`. Python normal and \`-O\` output agreed locally, with nine deliberately altered input/logic cases rejected: field-size mismatch, wrong rational-2-torsion count, bool-as-integer alias, duplicate JSON key, nonfinite constant, huge-exponent float, malformed orbit partition, wrong factorization target, and wrong trace parity. Node independently reproduced the four partitions and 2-torsion counts; both languages remain producer-run unsigned, not an independent PCC attestation.

From the repository root:

\`\`\`sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
python3 -B "$D/ct162_genus3_torsion_filter.py" --self-test > /tmp/ct162-py.json
python3 -O -B "$D/ct162_genus3_torsion_filter.py" --self-test > /tmp/ct162-opt.json
cmp /tmp/ct162-py.json /tmp/ct162-opt.json
node "$D/ct162_genus3_torsion_independent.mjs"
\`\`\`

Freeze file: \`CT162_RESULT.json\`. Local Python source SHA-256 was \`956730b2ca9eb10e7c3e93e658f359806938837baca600cdd4f6fa4761751dc7\` (local before exact remote readback; do not treat as a signed receipt). Frozen source input SHA as above. All scientific assertions are **[pcc:unverified]** pending exact-head hosted checks and independent signed verification.

## Literature and research coordination

Primary paper: E. Costa et al., *Restrictions on Weil polynomials of Jacobians of hyperelliptic curves* (2020), Proposition 2.4 and Theorem 2.8, https://arxiv.org/pdf/2002.02067. Theorem 2.8's exclusion condition (a2 even, a3 odd) does **not** apply here (a3=-2724 even); this run explicitly enumerates admissible partitions instead of misusing the theorem. Additional 2025 research on genus-3 hyperelliptic isogeny classes: https://arxiv.org/abs/2508.16885. We make no novelty claim for the published parity theory.

Reviewed existing CT160/CT161, CT125 #1533, CT141/142 #1562, source #1589, root crypto #3877, prospective #4215, GPU IC #4178 and the crypto-autoresearcher transfer lead catalog file names. Shared research-KB/Conductor and individual autoresearcher YAML content were inaccessible through this connector runtime; no absence inference.

## Decision and next unblocked work

An exact genus-3 hyperelliptic candidate should now be screened for these necessary arithmetic/orbit conditions before any expensive algebra. The **higher-priority performance gate** remains the independently replayed **all 695/701 actual original/reuse Jacobian logs**, owner-admitted same-host C169/C13a/C13b/D, and a **complete cold single-target prime-field** ECDLP using a fully specified scalar-blind transfer compared with matched optimized rho/BSGS/IC. Setup, map, correction, linear algebra, verification, RSS, uncertainty, and signed PCC all count. The CT162 filter does not move that cost gate and no paid native or GPU compute, protected merge or frozen ledger rewrite was performed.

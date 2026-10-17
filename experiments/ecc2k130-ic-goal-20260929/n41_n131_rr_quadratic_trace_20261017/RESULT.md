# Target-conditioned odd-trace certificates over signed source-code families

## Result

A four-term trace polynomial

\[
H(D)=\operatorname{Tr}_{\mathbb F_{2^{131}}/\mathbb F_2}
       (a_1D+a_3D^3+a_5D^5+a_7D^7)
\]

equals one on all **512 signed seven-point determinants** in four frozen N131
source-code families. Each family includes both admissible first-slot x roots
and all 64 sign choices for six pair sums; the remaining five pair slots and
public target are fixed by `panel_n131_v2.json`. The exact four coefficients
are in `odd_certificate.json`. A separate checked-Sage program recomputed
every determinant and every trace value from the frozen points and verified
all 512 equalities. Consequently none of these 512 configurations has a zero
determinant.

This experiment also measures the size of the required shared certificate.
Each added odd power provides 131 more Boolean trace coefficients and extends
the certified prefix by one selected code family. The result guides the
target-conditioned pruning design: a single low-degree global trace has no
observed compression across these families, while a four-term trace gives a
compact certificate for a specified 512-state panel. The candidate remains a
design proposal (`candidate_id: null`); its relation-collection and target
descent stages are not specified or measured here.

## Method

Let \(s\in\mathbb F_2^6\) choose the sign of each of six pair-sum points,
and let \(D(s)\) be the determinant of the seven-point matrix with row
\((1,x,y,x^2,xy,x^3,x^2y)\), including the conjugate of the fixed target as
the seventh row. Write its Boolean algebraic normal form as

\[
D(s)=\sum_{S\subseteq[6]}c_S\prod_{i\in S}s_i.
\]

Characteristic two and \(s_i^2=s_i\) give the coefficient of \(s^T\) in
\(D^3\) exactly as
\(\sum_{A\cup B=T}c_A^2c_B\). For each chart and odd power, the producer
obtained all 64 coefficients by symbolic multiplication or a 64-value
Möbius transform. A single shared tuple \((a_1,a_3,\ldots)\) exists exactly
when the binary linear equations

\[
\operatorname{Tr}\!\left(\sum_j a_{2j+1}c^{(2j+1)}_S\right)
=\begin{cases}1&S=\varnothing,\\0&S\ne\varnothing\end{cases}
\]

are consistent for every selected chart. The trace pairing identifies each
coordinate functional with a unique field coefficient. If these equations
hold, \(H(D(s))=1\) for all signs; since \(H(0)=0\), a zero determinant is
excluded. Failure of this sufficient certificate is only an obstruction to
that particular shared feature family. `QuadraticTrace.lean` checks the
zero-exclusion implication and its witnessed-zero converse; the full Boolean
ANF and trace-pairing bridge remains a formalization obligation.

## Frozen panels and ranks

The N131 field is the polynomial-basis \(\mathbb F_2[t]/
(t^{131}+t^{13}+t^2+t+1)\), with curve \(y^2+xy=x^3+1\). The four selected
first-slot source codes are 3, 10, 41, and 46. These are complete two-root
signed-code families for the frozen five other slots, not a sample of sign
choices. All eight charts are nonexceptional and have 64 direct determinant
values. No zero occurred in the 512 direct Sage values. The rank table lists
the feature-matrix rank after each full code family; `fail` marks the first
prefix where the constant-one column raises rank by one.

| Odd powers | Feature width | Code 3 | Code 10 | Code 41 | Code 46 | First failed prefix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 131 | 70 | 131 | 131 | 131 | 10 |
| 1, 3 | 262 | 128 | 256 | 262 | 262 | 41 |
| 1, 3, 5 | 393 | 128 | 256 | 384 | 393 | 46 |
| 1, 3, 5, 7 | 524 | 128 | 256 | 384 | 512 | none in panel |

For the quadratic feature pair, the third-family inconsistency has an exact
142-row XOR witness: the feature words cancel while the requested labels XOR
to one. `result.json` contains the row indices. A checked-Sage determinant
and GF(2)-matrix replay reproduces every rank in the table, as well as that
XOR witness. For the four-power row, `recover_odd_certificate.py` recovers
the trace coefficients and `verify_odd_cert_sage.py` independently checks all
512 trace values.

The N41 control uses the fixed W8 six-pair target, 35 column-compatible
first-slot code families, two x roots per family, and the same 64 sign choices
per chart. For \(D,D^3\), the first family (code 2) already has feature rank
82 and augmented rank 83 despite having zero zero-determinant signs. Its
40-row XOR inconsistency is saved in `result.json`. Code 6/root 1/sign mask
15 has a zero determinant; the independent Sage replay checks that witness.
This control shows both that a genuine relation defeats a separator and that
certificate failure can occur without a zero in the tested family.

## Execution and verification

The producer was launched through the repository's checked `sage` launcher
with a frozen one-worker, 600-second, 4-GiB envelope. It completed in 1.577 s
of parent wall time with 49,184,768 bytes sampled combined RSS. Its exclusive
internal screen times were 0.759 s for N41 and 0.597 s for N131. The odd-power
dimension screen recorded 0.191 s of internal computation. These are local
algorithmic diagnostics, with no physical-host isolation or paired rho run.
The odd-power screen and independent audits were executed sequentially on the
same local checked Sage runtime. `sage_runtime_info.json` pins that runtime;
each protocol pins its source and input hashes. `terminal.json` reports
`PASS_TERMINAL_READBACK` after checking all bindings, three independent Sage
audits, and the Lean axiom output.

`QuadraticTrace.lean` builds with the pinned Lean 4.34.1 toolchain. Both
declared theorems have only standard `propext` in `#print axioms`; there are
no placeholders or custom research axioms. The proof map is in
`PROOF_MAP.md`. `lean4checker --fresh` was unavailable on this host.

## Next experiment

The next target-conditioned solver test should generate a local trace
certificate for each candidate code family, use it to reject all 128 sign
states at once, and compare the complete certificate-generation plus clause
cost against direct determinant or SAT filtering on the same unpinned N41
query. Then carry only a measured reduction in total target-dependent work
to the frozen N131 query. A global odd-power trace alone scales one feature
block per additional selected family on the current panel.

# Exact quartic block membership on the N41 W11 residual panel

**A target-conditioned quartic eliminates the four signed states of one
source code from the second-product membership test.** Multiplying the
quartics of all codes in a width-eight prefix block and intersecting its
roots with the allowed product subspace rejected every one of the 109
blocks on each of 24 frozen ordinary residuals. It retained one block,
prefix 31, on the independently verified positive residual and rejected
the other 108. Each of the 25 rows also checked one complete quartic's
four roots against direct elliptic-curve subtraction, including code
253 on the positive residual.

The construction is algebraically smaller than a point-by-point block
scan: it makes two quadratic expressions per source code and no group
subtractions for the block decision. Its current checked-Sage GCD
kernel is slower on this panel. Over 25 queries, quartic construction
took 15.154 seconds and block products plus GCDs took 263.234 seconds.
This locates the next optimization at the subspace-intersection step,
while the code-by-code construction remains a separate N131 scaling
barrier.

## Exact instance and input law

The field is `GF(2)[u]/(u^41+u³+1)` and the curve is
`y²+xy=x³+1`, ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order
549,756,390,943 with cofactor four. The W11 fixed-seed source has
281 valid codes, each with four signed pair points. The first and
second pair rotations are 12 and 24. The positive residual is
`R=(1434452595080,1460136977354)`, with compatible source codes
`(253,63)`. The other 24 target points are the frozen public raw point
minus three random distinct-code source pairs, with input law and
hashes inherited from the prior [block panel](../n41_w11_target_block_filter_20261018/RESULT.md).
The [completed protocol](full600_protocol.json) fixes those 25 points,
source snapshots, one Sage process and a 600-second alarm.

## Quartic and subspace gate

For source-pair reciprocal `w`, target reciprocal `t`, candidate
second source product `p`, and rotated pair constants `H,C`, use the
prior exact eliminated-pair polynomial

`R(w;t,p,H,C)=A D p²+B M p+M²+C H B²`, where
`B=tw`, `A=1+B²`, `D=t²+w²`, and `M=A H+C D`.

A fixed first source code has two pair reciprocals `w0,w1`, each
supporting two signed points. Its four-branch condition is the quartic
`Q_code(p)=R(w0;t,p,H,C)R(w1;t,p,H,C)`. The checked run found degree
four for all 281 quartics at each of the 25 target points. For the
audited code on every row, its four field roots exactly matched the
four `p=C/x(R−P)+H x(R−P)` products from direct group subtraction.
The audit checks the full point coordinate and signs even though the
gate itself uses only `x(R)`; extra quartic roots would only retain an
additional block, not discard an actual witness.

The rotated source product is binary linear in ten free code bits:
`a(a+s)=a²+as`. The 1,024 source products form a dimension-ten
binary space `U`. A repeated characteristic-two recurrence builds its
degree-1,024 vanishing polynomial `L_U`, which has only 11 nonzero
terms. For each source-code prefix block `B`, put
`Q_B=∏_{code∈B}Q_code`. The block is rejected exactly when
`gcd(Q_B,L_U)=1`: since `L_U` splits at every product in `U`, a
nonconstant GCD is precisely an allowed product root of `Q_B`.
The implementation computes `L_U mod Q_B` from its 11 linearized
terms by ten modular squarings, then takes the small-degree GCD.
The [Lean proof map](PROOF_MAP.md) records a checked recurrence theorem
and the remaining concrete elimination and GCD bridges.

## Frozen measurements and controls

| Phase, one checked-Sage process | 25-query total | Mean per query |
| --- | ---: | ---: |
| Reusable field, source and `L_U` construction | 21.062 s | — |
| 281 target-conditioned quartics | 15.154 s | 0.606 s |
| 109 block products and modular GCDs | 263.234 s | 10.529 s |
| Complete target-dependent interval, including one direct four-root audit per query | 279.135 s | 11.165 s |
| Entire process interval after checked launcher startup | 300.220 s | — |

The completed process recorded 276,873,216 B raw maximum RSS,
including Sage. The positive GCD-degree histogram was 108 blocks of
degree zero and one block of degree one. All 24 ordinary rows had 109
degree-zero blocks. The [result](full600_result.json),
[stdout](full600.stdout), [runtime receipt](full600_sage_runtime_info.json),
and [verification receipt](verification_result.json) bind the phase
costs, input hashes, exact-scan agreement and direct-root audits.
These are ordinary-host component timings, with no CPU isolation or
same-point IC/rho timing. The complete IC configuration remains
unresolved, so `candidate_id` is `null`.

The first frozen implementation used a direct GCD with the degree-1,024
polynomial and hit its 180-second cap while evaluating blocks;
[attempt 1](attempt1.json) is `BOUNDED_UNKNOWN`. The modular-reduction
revision completed four arithmetic query logs but failed result JSON
serialization on a Sage integer; [attempt 2](attempt2_receipt.json)
is `PRODUCER_FAILURE`, with [stdout](attempt2.stdout) retained. The
25-query modular run under a 300-second cap logged 22 complete queries
before its alarm; [that cap](full_cap_receipt.json) remains
`BOUNDED_UNKNOWN` for that run. The 600-second run then completed the
same 25-query panel using the same modular algorithm and a one-line
serialization repair.

## Scaling decision

The exact embedded W20 subset of the proposed N131 W33 source has
132,045 valid codes. A code-by-code quartic construction would visit
at least those 132,045 codes per target residual, before any wider W33
codes. Even an ideal constant-cost width-eight block oracle would
have at least 16,506 occupied prefix blocks on this subset. The N41
GCD implementation therefore does not qualify for N131 promotion.

The useful next design is a **free-code resultant circuit**. Eliminate
the two pair reciprocals while keeping both source products as linear
functions of still-free code bits, then test whether target-conditioned
Boolean propagation rejects families without enumerating source codes.
Its N41 positive and ordinary controls should be compared against the
existing exact two-pair XCNF under the same caps and full construction
cost. The resulting gate must have a credible N131 memory and work
projection before touching the frozen N131 public target.

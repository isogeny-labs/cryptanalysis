# Target-conditioned rank-two quotient join for two free N41 source slots

**A seven-point Riemann–Roch determinant with four source-pair slots fixed becomes a two-dimensional signature equality for the remaining two slots.** On the frozen N41 public-point panel, this reduced a 144 × 144 eligible-state rectangle to one match in 0.158 seconds of ordinary-host Python join time. The match is the archived six-pair relation's state pair `(12,122)`. Independent checked Sage performed group subtraction on all **20,736** pairs and found exactly the same pair.

## Exact reduction

Use the basis `1,x,y,x²,xy,x³,x²y` of `L(7O)` on `E:y²+xy=x³+1`. The target enters as `−Q=(x_Q,y_Q+x_Q)`. Four fixed pair-output points and `−Q` give five rows of the seven-column evaluation matrix. Their rank is five on the frozen input. Let `f,g` be a basis of their right kernel. For candidate pair-output points `P,R`, the seven rows are dependent precisely when

`f(P)g(R)+g(P)f(R)=0`.

This follows by reducing the final two rows modulo the fixed five-row span and taking their two-by-two determinant. With nonzero signatures `(f(P),g(P))` and `(f(R),g(R))`, the condition says their projective ratios are equal. The runner hashes the first slot's ratios and probes them with the second slot. It checks the column rule on the resulting matches. A zero signature would require an exceptional branch; the runner explicitly asserts that neither side has one on this panel.

All five fixed x coordinates are distinct. Neither candidate side reuses a fixed x coordinate, and no left/right candidate pair shares an x coordinate. Thus all 20,736 tested seven-point charts satisfy the distinct-x condition used by the Riemann–Roch relation criterion. The independent Sage audit checks group equality directly, without using the determinant or quotient signature.

## Frozen input and measurements

The field is `GF(2)[t]/(t^41+t³+1)`, the curve is `y²+xy=x³+1`, and the subgroup order is `549756390943` (`EC1N41Ckb1h7d5e80d3c4d0`). The source has 1,120 actual usable projected points, 77 folded columns, and 160 signed pair states per slot. Four source slots (indices 2–5) are fixed to states from the independently replayed six-pair relation; the public raw target is `(2026560328086,1928332930914)`. Eligible states in slots 0 and 1 avoid every fixed column.

| Stage | Exact result |
| --- | ---: |
| Five-row rank / quotient dimension | 5 / 2 |
| Eligible states, left / right | 144 / 144 |
| Zero quotient signatures, left / right | 0 / 0 |
| Raw equal-signature pairs | 1 |
| Distinct-column pairs | 1: `(12,122)` |
| Checked-Sage group pairs evaluated | 20,736 |
| Independent group matches | 1: `(12,122)` |
| Quotient join wall, including kernel and key construction | 0.157889459 s |

The [protocol](protocol.json) pins geometry, relation certificate, field source, runner, target, and slot policy by SHA-256. [result.json](result.json) records the kernel vectors, pivots, free columns, counts and match. The checked Sage [runtime](sage_runtime_info.json), [group audit](audit_sage.json), and [terminal replay](terminal.json) retain independent verification. The wall is an ordinary-host stage diagnostic with no isolation or paired rho timing; the four fixed slots come from an archived witness. `candidate_id` is `null` because this is a terminal relation-search component.

## N131 transfer gate

The archived W23 N131 source has **1,049,218** eligible pair edges per slot, hence **4,196,872** signed states per slot. For a *given four-slot suffix*, a native quotient join would replace **17,613,734,584,384** pair comparisons with two signature passes and a hash lookup; this is a source-size calculation, not an N131 runtime prediction. Enumerating four free suffix slots before this join has **310,243,646,009,125,001,216,659,456** labeled combinations before compatibility filtering. The two-slot quotient therefore needs a prior exact constraint that removes whole suffix-code families while those four slots remain unresolved.

The next experiment is an unpinned N41 public-point search that lifts the quotient to at least one unresolved suffix family, checks that all true relations survive, and measures complete target-dependent work against the existing exact three-plus-three join. Its N131 promotion gate remains one worker, 600 seconds, and 4 GiB on the frozen ordinary public point.

# CT35 — cold toy-DLP cost audit for cyclic-49 isogeny transfers

**2026-11-12 | bounded developer-run control | [pcc:unverified]**

## Objective and source boundaries

This is an operation-count **negative control**, not a new isogeny or attack. It builds on the published F101 degree-(7+7) and direct-49 elliptic maps from [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [cryptanalysis #1495](https://github.com/isogeny-labs/cryptanalysis/pull/1495) and [#1499](https://github.com/isogeny-labs/cryptanalysis/pull/1499). It avoids duplicating the concurrent Phi2/Psi2/C2-genus-2 implementation in [#1496](https://github.com/isogeny-labs/cryptanalysis/pull/1496) and [#1498](https://github.com/isogeny-labs/cryptanalysis/pull/1498). Arithmetic source is independently written; the original selected public kernel cubics and codomains remain assumed fixtures, *not* independently discovered geometric isogenies. [pcc:unverified]

The cold routes are: direct source BSGS; two degree-7 maps then destination BSGS; and one degree-49 map then destination BSGS. For **every** public query Q=kG in both rational groups, BSGS receives only G and Q and recovers k independently. Both transferred routes map **both G and Q anew per cold query**; the target baby-step dictionary and validation are built afresh. Every source and target point is independently enumerated. No known log is supplied to the solver. The source and transferred logarithms match for all **109/109** and **113/113** cases, and the transferred maps agree on every rational point. Mutation controls reject both a wrong high-degree direct numerator coefficient and a wrong destination curve constant. [pcc:unverified]

## Exact primitive field-operation model

Each F101 residue addition/subtraction is counted as one addition, multiplication (including squaring or multiplication by a literal) as one multiplication, and modular inverse as one inversion. These are **source-level operation vectors, not hardware timing**; Python overhead, memory, branching, hash lookups, kernel discovery and precomputed input fixtures are excluded. Degree-d odd separable normalized maps X=N/K², Y=y dX/dx have deg(N)=d, deg(K)=(d-1)/2. Paired-Horner N,N' and K,K', then one inverse and its powers, cost exactly in this implementation:

- Fp additions: 3d
- Fp multiplications: 3d+7
- Fp inversions: 1

| One nonidentity map | Adds | Multiplies | Inverses |
|---|---:|---:|---:|
| Two degree-7 maps | 42 | 56 | 2 |
| Direct degree-49 map | 147 | 154 | 1 |

The independent Go program checks the operation formulas. Thus with an addition costing A multiplication-equivalents, direct-49 dense evaluation beats two-seven evaluation **only if the saved inversion costs strictly more than 98 + 105A multiplication-equivalents**. A different isogeny evaluation scheme could change the threshold; it is not a universal complexity lower bound. [pcc:unverified]

## All cold BSGS logs: full counted operation vectors

Counts include *per-query* transfer of the public base and target (for the transferred pipelines), baby/giant BSGS steps, and scalar verification. They exclude one-time polynomial/kernel setup, reported separately below. [pcc:unverified]

| Curve | Route, all cold logs | Fp adds | Fp muls | Fp invs |
|---|---|---:|---:|---:|
| Order 109; 109 logs | Source BSGS | 18,615 | 12,849 | 3,101 |
| | 7+7 transfer + BSGS | 27,729 | 25,001 | 3,535 |
| | Direct49 transfer + BSGS | 50,514 | 46,267 | 3,318 |
| Order 113; 113 logs | Source BSGS | 19,486 | 13,428 | 3,246 |
| | 7+7 transfer + BSGS | 28,936 | 26,028 | 3,696 |
| | Direct49 transfer + BSGS | 52,561 | 48,078 | 3,471 |

Source BSGS is **strictly cheaper in all three counted field-operation dimensions** than either transfer route on both fixed corpora, so *no nonnegative linear weighting of these three operations* favors the measured transferred routes. This is a negative result **only for the specified cold BSGS solver, source/destination representations, public toy groups and metering boundary**. It does not establish an obstruction to a different Jacobian solver, optimized rho, index calculus, endomorphism exploitation, large fields or cross-characteristic computational representations. [pcc:unverified]

One-time dense numerator generation from supplied cubic kernel inputs: 234 adds + 240 muls for two-seven; degree-49 pullback support plus direct numerator: 3,823 adds + 3,829 muls. These are reference coefficient-arithmetic counts and are not included in the corpus totals; faster polynomial algorithms could change them. [pcc:unverified]

## Reproduction

```bash
python3 -B experiments/chained-transfer-reference/ct35/ct35_cost_oracle.py > /tmp/ct35.out
python3 -O -B experiments/chained-transfer-reference/ct35/ct35_cost_oracle.py > /tmp/ct35.opt.out
diff -u /tmp/ct35.out /tmp/ct35.opt.out
go run experiments/chained-transfer-reference/ct35/ct35_analytic_independent.go
```

The standard/optimized Python runs were identical locally; the Go formula audit passed locally. Both programs are standalone and import no CT33/CT34 producers. This is **unsigned developer evidence only**. The Go verifier checks the analytic operation identity, *not* genus-2 Cantor or the full elliptic group maps. Wrong-numerator and wrong-target-equation controls are encoded in the Python program. No paid EKS Spot/S3/cloud compute, solver benchmark lease or checkpoint bypass. [pcc:unverified]

## Next gates

Independently replay the actual native Phi2/Psi2 Jacobian correspondence and dual over **all 12,317 balanced classes**, including nonsplit, ramified, repeated, zero and infinity supports; compare genuine Jacobian DLP recovery cost against optimized negation-map rho and the established index-calculus baseline on matched instances using an admitted frozen protocol. Required independent signed PCC, research-KB/locked atlas access, S3/live budget admission, root ledger/archive and PR review/merge gates remain separate and unresolved. The results here do not warrant a speedup claim. [pcc:unverified]

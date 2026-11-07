# Two octic-norm primes carry large rational C–E fibers

A bounded stage-one Pollard (p-1) search split the saved 230-digit cofactor of the **octic** conjugate-pair resultant cube root. The discovered 21-digit divisor factors as

`178760799831235072777 = 414340033 × 431435018569`.

Checked Sage proved both factors prime and verified that each divides the octic cube root but not the quartic cube root. The cofactor left after this exact split has 210 digits. The integer decomposition and the divisor split are also checked in [`OcticFactors.lean`](formal/OcticFactors.lean); [`lean-check.txt`](formal/lean-check.txt) records the build and `#print axioms` output.

For **each** new prime, the source-`j=1728` condition on `C:y²+y=x³−7` has 18 rational C points. Their resolvent fibers contain 213 distinct rational `x_E` roots: 15 source points have 12 roots and three have 11. Every root lifts to two points on `E:y²=x³+432`, giving **426 C–E pairs**. Of these, 144 lie in the base quartic factor and 282 in the base octic factor. The inverse B-branch numerator and denominator are both zero on six pairs and both nonzero on the other 420. The original curve, source-j, resolvent, factor-membership, and branch equations were evaluated in checked Sage and independently in integer modular arithmetic; the separate polynomial-gcd kernel reproduced the pair counts for all 18 fibers at each prime. The two-prime independent audit used 1,440 and 2,052 polynomial multiplications, respectively, as algorithmic operation counts.

The registered nearby control `p=414340153` is the next prime above `414340033` with `p ≡ 1 (mod 24)` that divides neither saved norm root. It also has 18 rational source C points, but its 72 rational resolvent `x_E` roots, four per source, yield **zero E-point lifts**. Its independent polynomial-gcd audit used 1,440 polynomial multiplications. This paired control shows that the 426-pair fiber does not follow merely from the congruence class or from complete splitting of the source polynomial in these cases.

## Frozen experiments and receipts

[`run.py`](run.py) pinned the prior power certificate and gave PARI `factorint(n,8)` a 45-second wall cap. It recorded `TIME_LIMIT` with no factor returned. [`pm1.py`](pm1.py) then ran predeclared stage-one bounds `10^4`, `10^5`, `10^6` with bases 2 and 3. Both bases found the same proper divisor at `10^5`; exact division and its factorization are recorded in [`pm1_result.json`](pm1_result.json) and [`prime_result.json`](prime_result.json). The first divisor was composite, as preserved in [`composite_divisor_result.json`](composite_divisor_result.json); the two prime factors were frozen in [`prime_protocol.json`](prime_protocol.json) before the Sage curve replay.

[`classify_primes_sage.py`](classify_primes_sage.py) checks proof-grade primality, exact product and quotient, C and E equations, source-j condition, all rational resolvent roots, both base-factor values, and the two branch polynomials. [`audit_primes.py`](audit_primes.py) independently reconstructs the source points, local polynomial-gcd counts, and modular equations for every saved pair. [`control_sage.py`](control_sage.py) and [`audit_control.py`](audit_control.py) apply the same checks to the nearby control. Each replay has a preceding hash-bound protocol in this directory. All new local Sage jobs used the checked repository launcher; [`sage-runtime-info.txt`](sage-runtime-info.txt) records the accepted build. [`validation.json`](validation.json) binds the final artifacts.

The 210-digit remaining cofactor was subjected to a separate stage-one (p-1) run at bound `10^6`, bases 2 and 3. Both gcds were 1, as recorded in [`remaining_pm1_result.json`](remaining_pm1_result.json). Its factorization remains open under this bounded search.

## Proof map and next step

| Result | Formal or executable check | Status |
| --- | --- | --- |
| Exact 230-digit cofactor decomposition and 21-digit divisor split | `J1728OcticFactors.octic_cofactor_split`, `pm1_divisor_split` | Lean checked; only standard `propext` axiom reported |
| Primality of the two factors | `classify_primes_sage.py`, `prime_result.json` | Checked Sage `is_prime(proof=True)` |
| Source C points, C–E pairs, factor membership, branch values | `prime_result.json`, `audit_result.json` | Checked Sage plus independent modular and local-gcd audit |
| Same-congruence nearby control | `control_result.json`, `control_audit_result.json` | Checked Sage plus independent local-gcd audit |

The field, curve, and branch classification is checked by executable certificates rather than formalized in Lean; that formal bridge remains partial. The next mathematical question is why the two certified octic-norm divisors produce 213 rational resolvent roots and full E-point lifts while the nearby same-class control has 72 roots and no lifts. A Frobenius or resultant-factor criterion could turn this observed split into a predictive theorem. The next arithmetic search is bounded ECM or another certified factor method on the 210-digit residual.

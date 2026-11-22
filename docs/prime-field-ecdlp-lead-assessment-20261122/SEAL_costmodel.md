# Rigorous seal: cost model confirms no IC/rho crossover under the measured degree law

**Harness:** isogeny-labs/lfd-summation-systems `experiments/ic-costmodel` (Rust), the lab's
own validated model. `validate` PASSES: 63 scored cell-prices all within [1/2,2], median
|log2(pred/meas)| = 0.067 (bound 0.5), rho within [0.75,1.33] at log2 p>=32. All [pcc:unverified].
Cost unit = group-addition equivalents; native ops priced at pi in {0, 0.1, 1} GAE.
Entry below = log2(IC_min / rho); negative => IC cheaper. m=2..8, k free, best route chosen.

## Verdict by degree assumption (price 0.1, the realistic band)
| log2 N (=log2 p) | LB  D=2 (counterfactual) | LAW (measured growth) | CEIL (mk+1) |
|---|---|---|---|
| 64  | -12.8  IC wins | +4.0  IC loses | +4.0  IC loses |
| 128 | -30.2  IC wins | +6.9  IC loses | +6.9  IC loses |
| 256 | -65.4  IC wins | +10.0 IC loses | +10.0 IC loses |

"IC beats rho (all three prices)":  LB = **yes at every size**;  LAW, CEIL, LAW-dense, enum = **no at every size**.

## Reading
- The ONLY regime where prime-field IC beats rho is **LB with D=2** — a bounded *constant*
  solving degree. That is exactly the "p-independent / polylog-degree oracle" counterfactual.
- Under the **measured** law (LFD = mk+1 for the m>=5 arities a sub-sqrt exponent needs;
  D = 57..273 across 40..256-bit sizes), IC is +3..+10 bits WORSE than rho at every
  cryptographic size, at every realistic op price. Only the unphysical price pi=0
  (all non-group ops free) shows the groebner route negative, and even then only via the
  LB degree.
- Therefore there is **no crossover p\*** below (or at) cryptographic sizes under the real
  degree law. The sub-sqrt(p) hope lives entirely in the D=2 counterfactual that the measured
  solving-degree data refutes.

## Chain of evidence (complete)
1. Reframe (both Mythos reads): the whole sub-sqrt program reduces to the per-decomposition
   solving-degree growth, not fp20-32 cold parity, not the F4 constant.
2. Measured (rows-merged.jsonl, 5818 systems): prime LFD saturates mk+1 (linear, slope~m) for
   m>=5; bounded only at m=3 (which cannot beat sqrt(p)). Binary bounded through m=4 (Frobenius).
3. Cost model (this file): under that measured law, IC never beats rho at 40..256 bits.
=> **B1 (PKM two-power-subgroup sub-sqrt(p) tower) is dead as posed.** Clean publishable negative.

## Residual falsifiers (honest)
- Short high-m lever (measured k<=4): extend m=5 to k=5,6 and confirm it stays on mk+1.
- Alternative prime-field presentations (split / System-(4)) not yet measured.
- A non-Groebner decomposition oracle (e.g. a true Graeffe/iterated-norm engine, which does
  NOT exist in-repo) with provably bounded cost would reopen it — but it must beat the budget
  table C_dec(m,p); the measured Groebner route does not.
